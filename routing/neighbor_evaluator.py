"""
===============================================================================
Mesh Control Plane V2

File    : neighbor_evaluator.py
Purpose : Evaluates peer link metrics using dynamic YAML scoring formulas
          and selects the Top 2 Best Active Neighbors.

Author  : Mesh Control Plane Project
===============================================================================
"""

from pathlib import Path
import yaml
import time


class NeighborEvaluator:
    """
    Evaluates dynamic link quality metrics across reachable mesh peers
    and assigns Top 2 neighbor routing roles (PRIMARY_ACTIVE & STANDBY_BACKUP).
    """

    def __init__(self, config_path="config/neighbor_selection.yaml"):
        self.config_path = Path(config_path)
        self.config = {}
        self.load_config()

    def load_config(self):
        """Loads or reloads neighbor selection configuration from YAML."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    raw = yaml.safe_load(f) or {}
                    self.config = raw.get("neighbor_selection", {})
            except Exception:
                self.config = {}

        if not self.config:
            # Fallback default configuration
            self.config = {
                "enabled": True,
                "max_active_neighbors": 2,
                "evaluation_interval_seconds": 1.0,
                "stale_timeout_seconds": 3.5,
                "scoring_weights": {
                    "rssi_weight": 0.40,
                    "latency_weight": 0.35,
                    "packet_loss_weight": 0.15,
                    "snr_weight": 0.10,
                },
                "hard_boundaries": {
                    "min_rssi_dbm": -85.0,
                    "max_latency_ms": 100.0,
                    "max_packet_loss_percent": 10.0,
                },
                "normalization_bounds": {
                    "rssi_min_dbm": -95.0,
                    "rssi_max_dbm": -45.0,
                    "latency_min_ms": 1.0,
                    "latency_max_ms": 50.0,
                    "snr_min_db": 10.0,
                    "snr_max_db": 40.0,
                },
            }

    def normalize_rssi(self, rssi_dbm):
        bounds = self.config.get("normalization_bounds", {})
        r_min = float(bounds.get("rssi_min_dbm", -95.0))
        r_max = float(bounds.get("rssi_max_dbm", -45.0))
        val = max(r_min, min(r_max, float(rssi_dbm)))
        return (val - r_min) / (r_max - r_min) if (r_max > r_min) else 0.5

    def normalize_latency(self, latency_ms):
        bounds = self.config.get("normalization_bounds", {})
        l_min = float(bounds.get("latency_min_ms", 1.0))
        l_max = float(bounds.get("latency_max_ms", 50.0))
        val = max(l_min, min(l_max, float(latency_ms)))
        norm = (val - l_min) / (l_max - l_min) if (l_max > l_min) else 0.5
        return max(0.0, 1.0 - norm)

    def normalize_packet_loss(self, loss_pct):
        val = max(0.0, min(100.0, float(loss_pct)))
        return max(0.0, 1.0 - (val / 100.0))

    def normalize_snr(self, snr_db):
        bounds = self.config.get("normalization_bounds", {})
        s_min = float(bounds.get("snr_min_db", 10.0))
        s_max = float(bounds.get("snr_max_db", 40.0))
        val = max(s_min, min(s_max, float(snr_db)))
        return (val - s_min) / (s_max - s_min) if (s_max > s_min) else 0.5

    def calculate_link_score(self, metrics):
        """
        Calculates composite link quality score (0.0 - 1.0).
        Returns -1.0 if hard boundaries are violated.
        """
        if not metrics or metrics.get("status") in ["OFFLINE", "DISABLED"]:
            return -1.0

        rssi = float(metrics.get("rssi", -95.0))
        latency = float(metrics.get("latency", 0.0))
        loss = float(metrics.get("loss", 0.0))
        snr = float(metrics.get("snr", 25.0))

        # Check Hard Boundaries
        boundaries = self.config.get("hard_boundaries", {})
        min_rssi = float(boundaries.get("min_rssi_dbm", -85.0))
        max_lat = float(boundaries.get("max_latency_ms", 100.0))
        max_loss = float(boundaries.get("max_packet_loss_percent", 10.0))

        if rssi < min_rssi or (latency > max_lat and latency > 0.0) or loss > max_loss:
            return -1.0

        weights = self.config.get("scoring_weights", {})
        w_rssi = float(weights.get("rssi_weight", 0.40))
        w_lat = float(weights.get("latency_weight", 0.35))
        w_loss = float(weights.get("packet_loss_weight", 0.15))
        w_snr = float(weights.get("snr_weight", 0.10))

        n_rssi = self.normalize_rssi(rssi)
        n_lat = self.normalize_latency(latency)
        n_loss = self.normalize_packet_loss(loss)
        n_snr = self.normalize_snr(snr)

        score = (w_rssi * n_rssi) + (w_lat * n_lat) + (w_loss * n_loss) + (w_snr * n_snr)
        return round(max(0.0, min(1.0, score)), 4)

    def evaluate_neighbors(self, peer_table, network_peer_graph=None):
        """
        Scores all reachable peers in peer_table dictionary and assigns neighbor routing roles according to Rule 5:
        1. Both Top 2 valid candidates are ACTIVE (ACTIVE_PRIMARY for Rank 1, ACTIVE_SECONDARY for Rank 2).
        2. Dynamic 50/50 bandwidth allocation across active neighbours (50% each).
        3. Network Inclusivity Override ("No Node Left Behind"): If a peer is an edge node with only 1 reachable peer connection,
           it is prioritized into an ACTIVE_SECONDARY neighbour slot so it is never isolated.
        4. Lower-ranked peers (Rank 3+) become DISCOVERED_IDLE (Hot Standby Backup).
        """
        self.load_config()
        max_active = int(self.config.get("max_active_neighbors", 2))

        scored_peers = []
        for peer_id, metrics in peer_table.items():
            score = self.calculate_link_score(metrics)
            metrics_copy = dict(metrics)
            metrics_copy["link_score"] = score
            
            # Check if this peer is a single-peer edge node (e.g. UGV-05 connected only to UGV-01)
            is_single_peer_edge = False
            if network_peer_graph and isinstance(network_peer_graph, dict):
                p_links = network_peer_graph.get(peer_id, [])
                if len(p_links) == 1:
                    is_single_peer_edge = True
            elif metrics.get("is_single_peer_edge") or metrics.get("peer_count") == 1:
                is_single_peer_edge = True

            metrics_copy["is_single_peer_edge"] = is_single_peer_edge
            scored_peers.append((peer_id, score, is_single_peer_edge, metrics_copy))

        # Separate valid candidates and sort descending by link score
        valid_peers = [p for p in scored_peers if p[3].get("status") not in ["OFFLINE", "DISABLED"] and p[1] >= 0]
        invalid_peers = [p for p in scored_peers if p[3].get("status") in ["OFFLINE", "DISABLED"] or p[1] < 0]

        valid_peers.sort(key=lambda x: x[1], reverse=True)

        # Apply Network Inclusivity Override for Rank 2:
        # If there is a single-peer edge node (e.g. UGV-05) in valid_peers beyond Rank 1, promote it to Rank 2 slot
        if len(valid_peers) >= 2:
            edge_idx = next((i for i in range(1, len(valid_peers)) if valid_peers[i][2]), None)
            if edge_idx is not None and edge_idx > 1:
                edge_item = valid_peers.pop(edge_idx)
                valid_peers.insert(1, edge_item)

        ordered_peers = valid_peers + invalid_peers
        active_count = len(valid_peers)

        evaluated = {}
        active_rank = 0
        for peer_id, score, is_edge, item in ordered_peers:
            if item.get("status") in ["OFFLINE", "DISABLED"] or score < 0:
                item["role_assignment"] = "DISQUALIFIED" if item.get("status") not in ["OFFLINE", "DISABLED"] else item.get("status")
                item["allocated_bw_pct"] = 0.0
                item["is_active_neighbor"] = False
            else:
                active_rank += 1
                if active_rank == 1:
                    item["role_assignment"] = "ACTIVE_PRIMARY"
                    item["allocated_bw_pct"] = 50.0 if active_count >= 2 else 100.0
                    item["is_active_neighbor"] = True
                elif active_rank == 2:
                    item["role_assignment"] = "ACTIVE_SECONDARY"
                    item["allocated_bw_pct"] = 50.0
                    item["is_active_neighbor"] = True
                else:
                    item["role_assignment"] = "DISCOVERED_IDLE"
                    item["allocated_bw_pct"] = 0.0
                    item["is_active_neighbor"] = False

            evaluated[peer_id] = item

        return evaluated
