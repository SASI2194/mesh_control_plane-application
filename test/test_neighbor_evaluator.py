#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Test Suite: Neighbor Evaluator & Best 2 Selection Test

Verifies that NeighborEvaluator accurately normalizes link metrics, calculates
composite link scores according to YAML formula weights, enforces hard boundary
disqualifications, and ranks peers into Top 2 roles (PRIMARY_ACTIVE and STANDBY_BACKUP).

===============================================================================
"""

import os
import sys
import tempfile
import unittest
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from routing.neighbor_evaluator import NeighborEvaluator


class TestNeighborEvaluator(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, "neighbor_selection.yaml")

        self.yaml_content = {
            "neighbor_selection": {
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
        }

        with open(self.config_file, "w") as f:
            yaml.dump(self.yaml_content, f)

        self.evaluator = NeighborEvaluator(config_path=self.config_file)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_normalization_bounds(self):
        # RSSI (-95 to -45): -95 -> 0.0, -45 -> 1.0, -70 -> 0.5
        self.assertEqual(self.evaluator.normalize_rssi(-95.0), 0.0)
        self.assertEqual(self.evaluator.normalize_rssi(-45.0), 1.0)
        self.assertEqual(self.evaluator.normalize_rssi(-70.0), 0.5)

        # Latency (1 to 50 ms): 1 ms -> 1.0 (best), 50 ms -> 0.0 (worst)
        self.assertEqual(self.evaluator.normalize_latency(1.0), 1.0)
        self.assertEqual(self.evaluator.normalize_latency(50.0), 0.0)

        # Packet Loss (0 to 100%): 0% -> 1.0, 10% -> 0.9, 100% -> 0.0
        self.assertEqual(self.evaluator.normalize_packet_loss(0.0), 1.0)
        self.assertEqual(self.evaluator.normalize_packet_loss(10.0), 0.9)

        # SNR (10 to 40 dB): 10 -> 0.0, 40 -> 1.0
        self.assertEqual(self.evaluator.normalize_snr(10.0), 0.0)
        self.assertEqual(self.evaluator.normalize_snr(40.0), 1.0)

    def test_link_score_calculation(self):
        # Ideal metrics: RSSI=-45, Latency=1ms, Loss=0%, SNR=40dB -> Score 1.0
        ideal_metrics = {
            "rssi": -45.0,
            "latency": 1.0,
            "loss": 0.0,
            "snr": 40.0,
            "status": "ONLINE",
        }
        score = self.evaluator.calculate_link_score(ideal_metrics)
        self.assertEqual(score, 1.0)

    def test_hard_boundary_disqualification(self):
        # RSSI below min_rssi (-85 dBm)
        bad_rssi = {"rssi": -86.0, "latency": 10.0, "loss": 1.0, "snr": 25.0, "status": "ONLINE"}
        self.assertEqual(self.evaluator.calculate_link_score(bad_rssi), -1.0)

        # Latency above max_latency (100 ms)
        high_latency = {"rssi": -60.0, "latency": 105.0, "loss": 1.0, "snr": 25.0, "status": "ONLINE"}
        self.assertEqual(self.evaluator.calculate_link_score(high_latency), -1.0)

        # Loss above max_packet_loss (10%)
        high_loss = {"rssi": -60.0, "latency": 10.0, "loss": 12.0, "snr": 25.0, "status": "ONLINE"}
        self.assertEqual(self.evaluator.calculate_link_score(high_loss), -1.0)

        # Offline node
        offline_node = {"rssi": -50.0, "latency": 5.0, "loss": 0.0, "snr": 30.0, "status": "OFFLINE"}
        self.assertEqual(self.evaluator.calculate_link_score(offline_node), -1.0)

    def test_evaluate_neighbors_top2_ranking(self):
        peer_table = {
            "192.168.1.10": {"rssi": -50.0, "latency": 5.0, "loss": 0.0, "snr": 35.0, "status": "ONLINE"},  # Best
            "192.168.1.11": {"rssi": -65.0, "latency": 15.0, "loss": 2.0, "snr": 28.0, "status": "ONLINE"}, # 2nd best
            "192.168.1.12": {"rssi": -75.0, "latency": 25.0, "loss": 5.0, "snr": 20.0, "status": "ONLINE"}, # 3rd best
            "192.168.1.13": {"rssi": -90.0, "latency": 10.0, "loss": 0.0, "snr": 30.0, "status": "ONLINE"}, # RSSI disqualified
        }

        evaluated = self.evaluator.evaluate_neighbors(peer_table)

        self.assertIn(evaluated["192.168.1.10"]["role_assignment"], ["ACTIVE_PRIMARY", "PRIMARY_ACTIVE"])
        self.assertIn(evaluated["192.168.1.11"]["role_assignment"], ["ACTIVE_SECONDARY", "STANDBY_BACKUP"])
        self.assertEqual(evaluated["192.168.1.12"]["role_assignment"], "DISCOVERED_IDLE")
        self.assertEqual(evaluated["192.168.1.13"]["role_assignment"], "DISQUALIFIED")
        self.assertEqual(evaluated["192.168.1.10"]["allocated_bw_pct"], 50.0)
        self.assertEqual(evaluated["192.168.1.11"]["allocated_bw_pct"], 50.0)
        self.assertEqual(evaluated["192.168.1.12"]["allocated_bw_pct"], 0.0)

    def test_network_inclusivity_single_peer_edge(self):
        # Scenario: UGV-05 is a single-peer edge node (peer_count = 1)
        peer_table = {
            "UGV-03": {"rssi": -56.0, "latency": 8.5, "loss": 0.0, "snr": 30.0, "status": "ONLINE", "peer_count": 2}, # Best link
            "UGV-04": {"rssi": -64.0, "latency": 12.0, "loss": 0.0, "snr": 28.0, "status": "ONLINE", "peer_count": 2}, # 2nd best
            "UGV-05": {"rssi": -78.0, "latency": 24.5, "loss": 1.0, "snr": 18.0, "status": "ONLINE", "peer_count": 1}, # Single-peer edge node!
        }

        evaluated = self.evaluator.evaluate_neighbors(peer_table)

        # UGV-05 must receive Network Inclusivity active slot (ACTIVE_SECONDARY) so it is not isolated
        self.assertEqual(evaluated["UGV-05"]["is_single_peer_edge"], True)
        self.assertIn(evaluated["UGV-05"]["role_assignment"], ["ACTIVE_SECONDARY", "STANDBY_BACKUP"])
        self.assertEqual(evaluated["UGV-05"]["allocated_bw_pct"], 50.0)


if __name__ == "__main__":
    unittest.main()
