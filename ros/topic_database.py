"""
===============================================================================

Mesh Control Plane

Topic Registry

Loads deployment topics from config/topics.yaml and tracks real-time
measured topic bandwidths, publication frequency (Hz), and payload data sizes.

===============================================================================
"""

import yaml


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

        for fn in filenames:
            if not os.path.exists(fn):
                continue
            with open(fn, "r") as f:
                cfg = yaml.safe_load(f)
            if not cfg:
                continue

            raw_list = cfg.get("topics") or cfg.get("system_topics") or []
            for topic in raw_list:
                t_copy = dict(topic)
                t_copy["status"] = str(topic.get("status", "ALLOW")).upper()
                t_copy["type"] = str(topic.get("type", "std_msgs/msg/String"))
                t_copy["static_bandwidth"] = float(topic.get("bandwidth", 0.0))
                t_copy["measured_bandwidth"] = 0.0
                t_copy["hz"] = 0.0
                t_copy["data_size_bytes"] = 0.0
                t_copy["data_size_str"] = "0 B"
                self._topics[topic["name"]] = t_copy

    #####################################################################

    def update_measured_bandwidths(self, measured_map: dict):
        """
        Update registry with real-time measured metrics map (Mbps, Hz, Data Size).
        """
        for name, topic in self._topics.items():
            if name in measured_map:
                val = measured_map[name]
                if isinstance(val, dict):
                    mbps = val.get("mbps", 0.0)
                    hz = val.get("hz", 0.0)
                    data_size_str = val.get("data_size_str", "0 B")

                    topic["measured_bandwidth"] = mbps
                    topic["hz"] = hz
                    topic["data_size_str"] = data_size_str

                    # Dual Tx/Rx Role metrics
                    topic["tx_hz"] = val.get("tx_hz", 0.0)
                    topic["tx_mbps"] = val.get("tx_mbps", 0.0)
                    topic["tx_data_size_str"] = val.get("tx_data_size_str", "0 B")

                    topic["rx_hz"] = val.get("rx_hz", 0.0)
                    topic["rx_mbps"] = val.get("rx_mbps", 0.0)
                    topic["rx_data_size_str"] = val.get("rx_data_size_str", "0 B")

                    topic["diff_mbps"] = val.get("diff_mbps", 0.0)
                    topic["delivery_pct"] = val.get("delivery_pct", 100.0)
                    topic["role"] = val.get("role", "IDLE")
                else:
                    topic["measured_bandwidth"] = float(val)
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
