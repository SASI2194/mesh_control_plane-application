"""
===============================================================================

Mesh Control Plane

Topic Registry

Loads deployment topics from config/topics.yaml and tracks real-time
measured topic bandwidths, publication frequency (Hz), and payload data sizes.

===============================================================================
"""

import yaml


def is_2d_occupancy_grid_topic(topic: str) -> bool:
    """
    Checks if a topic or Zenoh key is strictly a 2D OccupancyGrid map topic (/map, /rtabmap/map,
    or their device-namespaced variants like /ugv_02/map, /ugv_02/rtabmap/map, filtered/55/ugv_02/map).
    Excludes non-occupancy topics such as /compressed/map, /rtabmap/info,
    /rtabmap/cloud_map, /rtabmap/mapData, /rtabmap/mapGraph, map_metadata, etc.
    """
    if not topic:
        return False
    clean = topic.strip().rstrip("/")
    if clean.startswith("filtered/"):
        parts = clean.split("/")
        if len(parts) >= 3:
            clean = "/" + "/".join(parts[2:])
        else:
            clean = "/" + parts[-1]
    if not clean.startswith("/"):
        clean = "/" + clean
    if any(ex in clean for ex in ["compressed", "metadata", "cloud", "octomap", "mapData", "mapGraph", "mapPath", "map_updates", "prob_map", "grid_prob"]):
        return False
    parts = clean.split("/")
    if parts[-1] != "map":
        return False
    return clean in ["/map", "/rtabmap/map"] or clean.endswith("/rtabmap/map") or clean.endswith("/map")


def is_rtabmap_3d_cloud_topic(topic: str) -> bool:
    """
    Checks if a topic or Zenoh key is an RTAB-Map 3D point cloud or octomap topic
    (e.g., /rtabmap/cloud_obstacles, /rtabmap/cloud_map, /rtabmap/cloud_ground,
    /rtabmap/octomap_grid, or namespaced variants like /ugv_02/rtabmap/cloud_obstacles,
    filtered/55/ugv_02/rtabmap/cloud_obstacles).
    Excludes compressed representations (/compressed/cloud_obstacles).
    These topics publish with TRANSIENT_LOCAL durability and RELIABLE reliability.
    """
    if not topic:
        return False
    clean = topic.strip().lower()
    if "compressed" in clean:
        return False
    return any(k in clean for k in ["cloud_obstacles", "cloud_map", "cloud_ground", "octomap"])


class TopicRegistry:

    def __init__(self, filename="config/topics.yaml", extra_files=None):

        self._topics = {}
        import os

        filenames = [filename]
        if extra_files:
            if isinstance(extra_files, list):
                filenames.extend(extra_files)
            else:
                filenames.append(extra_files)

        sys_topics_path = os.path.join(os.path.dirname(os.path.abspath(filename)), "system_topics.yaml")
        if sys_topics_path not in filenames and os.path.exists(sys_topics_path):
            filenames.append(sys_topics_path)

        prio_topics_path = os.path.join(os.path.dirname(os.path.abspath(filename)), "priority_topics.yaml")
        if prio_topics_path not in filenames and os.path.exists(prio_topics_path):
            filenames.append(prio_topics_path)

        for fn in filenames:
            if not os.path.exists(fn):
                continue
            with open(fn, "r") as f:
                cfg = yaml.safe_load(f)
            if not cfg:
                continue

            is_sys_file = "system_topics" in cfg or "system_topics.yaml" in fn
            is_prio_file = "priority_topics" in cfg or "priority_topics.yaml" in fn
            raw_list = cfg.get("topics") or cfg.get("system_topics") or cfg.get("priority_topics") or []
            for topic in raw_list:
                t_copy = dict(topic)
                t_copy["is_system"] = is_sys_file
                t_copy["is_priority_protected"] = is_prio_file or t_copy.get("priority") == 1
                t_copy["status"] = str(topic.get("status", "ALLOW")).upper()
                t_copy["type"] = str(topic.get("type", "std_msgs/msg/String"))
                t_copy["static_bandwidth"] = float(topic.get("bandwidth", 0.0))
                t_copy["measured_bandwidth"] = 0.0
                t_copy["hz"] = 0.0
                t_copy["data_size_bytes"] = 0.0
                t_copy["data_size_str"] = "0 B"
                self._topics[topic["name"]] = t_copy

    #####################################################################

    def is_system_topic(self, topic_name: str) -> bool:
        """
        Check if a given topic name is a ROS 2 system infrastructure topic
        (e.g., /tf, /tf_static, /clock, /rosout, /parameter_events).
        """
        if not topic_name:
            return False
        clean_t = topic_name.strip()
        if not clean_t.startswith("/"):
            clean_t = "/" + clean_t

        info = self._topics.get(clean_t)
        if info and info.get("is_system", False):
            return True

        SYSTEM_NAMES = {"/tf", "/tf_static", "/clock", "/rosout", "/parameter_events"}
        if clean_t in SYSTEM_NAMES:
            return True

        base_name = "/" + clean_t.split("/")[-1] if "/" in clean_t else clean_t
        return base_name in SYSTEM_NAMES

    #####################################################################

    def update_measured_bandwidths(self, measured_map: dict):
        """
        Update registry with real-time measured metrics map (Mbps, Hz, Data Size),
        mapping namespaced multi-device streams to canonical base topics and tracking
        per-device stream statistics.
        """
        NAMESPACE_TO_DEVICE = {
            "ugv_01": "UGV-01",
            "ugv_02": "UGV-02",
            "ugv_03": "UGV-03",
            "ugv_04": "UGV-04",
            "ugv_05": "UGV-05",
            "ugv_06": "UGV-06",
            "gcs_01": "GCS-01",
            "gcs_02": "GCS-02",
            "gcs_03": "GCS-03",
        }

        canonical_streams = {c_name: [] for c_name in self._topics.keys()}
        sorted_canonicals = sorted(self._topics.keys(), key=len, reverse=True)

        for m_key, m_val in measured_map.items():
            if not isinstance(m_val, dict):
                continue

            # Determine matched canonical topic
            matched_canonical = None
            for c_name in sorted_canonicals:
                c_clean = c_name if c_name.startswith("/") else "/" + c_name
                if m_key == c_name or m_key == c_clean:
                    matched_canonical = c_name
                    break
                if m_key.endswith(c_clean):
                    prefix = m_key[:-len(c_clean)]
                    if prefix.endswith("/") or prefix.startswith("/"):
                        matched_canonical = c_name
                        break

            if not matched_canonical:
                continue

            # Determine device identity from m_key
            dev_name = "Local / Fleet"
            dev_ns = ""
            clean_m = m_key.strip("/")
            parts = clean_m.split("/")
            if len(parts) > 1 and parts[0].lower() in NAMESPACE_TO_DEVICE:
                dev_ns = parts[0].lower()
                dev_name = NAMESPACE_TO_DEVICE[dev_ns]
            elif m_val.get("origin_device"):
                dev_name = m_val["origin_device"]
            elif m_val.get("tx_hz", 0.0) > 0.0 and m_val.get("rx_hz", 0.0) == 0.0:
                dev_name = "Local Tx"
            elif m_val.get("rx_hz", 0.0) > 0.0 and m_val.get("tx_hz", 0.0) == 0.0:
                dev_name = "Swarm Rx"

            role = m_val.get("role", "IDLE")
            tx_hz = m_val.get("tx_hz", 0.0)
            rx_hz = m_val.get("rx_hz", 0.0)
            tx_mbps = m_val.get("tx_mbps", 0.0)
            rx_mbps = m_val.get("rx_mbps", 0.0)
            del_pct = m_val.get("delivery_pct", 100.0)

            # Stream-level verification per Rule 3
            if role == "PUBLISHER" or (tx_hz > 0.0 and rx_hz == 0.0):
                verif = "TX LIVE 100%"
            elif role in ["SUBSCRIBER", "BOTH"] or rx_hz > 0.0:
                if del_pct >= 99.0:
                    verif = "FULL DATA 100%"
                elif del_pct <= 0.0:
                    verif = "0% LOSS (DISCONNECTED)"
                else:
                    verif = f"{round(100.0 - del_pct, 1)}% LOSS DETECTED"
            else:
                verif = "UNINITIATED"

            stream_item = {
                "stream_key": m_key,
                "device_ns": dev_ns,
                "device_name": dev_name,
                "role": role,
                "tx_hz": round(tx_hz, 1),
                "tx_mbps": round(tx_mbps, 1),
                "tx_data_size_str": m_val.get("tx_data_size_str", "0 B"),
                "rx_hz": round(rx_hz, 1),
                "rx_mbps": round(rx_mbps, 1),
                "rx_data_size_str": m_val.get("rx_data_size_str", "0 B"),
                "diff_mbps": round(m_val.get("diff_mbps", 0.0), 1),
                "delivery_pct": round(del_pct, 1),
                "verification": verif
            }
            canonical_streams[matched_canonical].append(stream_item)

        for name, topic in self._topics.items():
            streams = canonical_streams.get(name, [])
            active_streams = [s for s in streams if s["tx_hz"] > 0.0 or s["rx_hz"] > 0.0]
            topic["active_streams"] = streams
            topic["active_streams_count"] = len(active_streams)

            if active_streams:
                agg_tx_hz = sum(s["tx_hz"] for s in active_streams)
                agg_tx_mbps = sum(s["tx_mbps"] for s in active_streams)
                agg_rx_hz = sum(s["rx_hz"] for s in active_streams)
                agg_rx_mbps = sum(s["rx_mbps"] for s in active_streams)

                topic["tx_hz"] = round(agg_tx_hz, 1)
                topic["tx_mbps"] = round(agg_tx_mbps, 1)
                topic["rx_hz"] = round(agg_rx_hz, 1)
                topic["rx_mbps"] = round(agg_rx_mbps, 1)

                tx_sizes = [s["tx_data_size_str"] for s in active_streams if s["tx_data_size_str"] != "0 B"]
                rx_sizes = [s["rx_data_size_str"] for s in active_streams if s["rx_data_size_str"] != "0 B"]
                topic["tx_data_size_str"] = tx_sizes[0] if tx_sizes else "0 B"
                topic["rx_data_size_str"] = rx_sizes[0] if rx_sizes else "0 B"

                topic["measured_bandwidth"] = round(agg_tx_mbps if agg_tx_mbps > 0.0 else agg_rx_mbps, 1)
                topic["hz"] = round(max(agg_tx_hz, agg_rx_hz), 1)
                topic["data_size_str"] = topic["tx_data_size_str"] if agg_tx_hz > 0.0 else topic["rx_data_size_str"]

                topic["diff_mbps"] = round(agg_tx_mbps - agg_rx_mbps, 1)
                min_del_pct = min(s["delivery_pct"] for s in active_streams)
                topic["delivery_pct"] = round(min_del_pct, 1)

                roles = {s["role"] for s in active_streams}
                if "BOTH" in roles or ("PUBLISHER" in roles and "SUBSCRIBER" in roles):
                    topic["role"] = "BOTH"
                elif "PUBLISHER" in roles:
                    topic["role"] = "PUBLISHER"
                elif "SUBSCRIBER" in roles:
                    topic["role"] = "SUBSCRIBER"
                else:
                    topic["role"] = "IDLE"

                if topic["role"] == "PUBLISHER":
                    topic["verification"] = "TX LIVE 100%"
                elif topic["role"] in ["SUBSCRIBER", "BOTH"]:
                    if topic["delivery_pct"] >= 99.0:
                        topic["verification"] = "FULL DATA 100%"
                    else:
                        topic["verification"] = f"{round(100.0 - topic['delivery_pct'], 1)}% LOSS"
                else:
                    topic["verification"] = "UNINITIATED"
            elif name in measured_map and isinstance(measured_map[name], (int, float)):
                topic["measured_bandwidth"] = float(measured_map[name])
                topic["verification"] = "UNINITIATED"
            else:
                topic["measured_bandwidth"] = 0.0
                topic["hz"] = 0.0
                topic["data_size_str"] = "0 B"
                topic["tx_hz"] = 0.0
                topic["tx_mbps"] = 0.0
                topic["tx_data_size_str"] = "0 B"
                topic["rx_hz"] = 0.0
                topic["rx_mbps"] = 0.0
                topic["rx_data_size_str"] = "0 B"
                topic["diff_mbps"] = 0.0
                topic["delivery_pct"] = 100.0
                topic["role"] = "IDLE"
                topic["verification"] = "UNINITIATED"

    def update_measured_metrics(self, metrics_map: dict):
        """
        Update registry with full live real-time metrics dictionary.
        """
        self.update_measured_bandwidths(metrics_map)

    #####################################################################

    def exists(self, topic):

        return topic in self._topics

    #####################################################################

    def get(self, topic):

        return self._topics.get(topic)

    #####################################################################

    def all_topics(self):

        return self._topics

    #####################################################################

    def print_topics(self):

        print()
        print("============== Topic Registry ==============")
        for topic in self._topics.values():
            st = topic.get("status", "ALLOW").upper()
            st_str = "ALLOW" if st == "ALLOW" else "DENY (BLOCKED)"
            print(f"{topic['id']:<3} {topic['name']:<15} P{topic['priority']}   Status: {st_str}")
        print()
