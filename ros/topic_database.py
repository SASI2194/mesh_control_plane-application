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

    def __init__(self, filename="config/topics.yaml"):

        self._topics = {}

        with open(filename, "r") as f:
            cfg = yaml.safe_load(f)

        for topic in cfg["topics"]:
            # Store both static baseline requirement and live measured dynamic metrics
            t_copy = dict(topic)
            t_copy["static_bandwidth"] = float(topic.get("bandwidth", 0))
            t_copy["measured_bandwidth"] = 0.0  # 0.0 Mbps until samples enter mesh
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
                else:
                    topic["measured_bandwidth"] = float(val)
            else:
                topic["measured_bandwidth"] = 0.0
                topic["hz"] = 0.0
                topic["data_size_str"] = "0 B"

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
            static_bw = topic.get("static_bandwidth", 0.0)
            print(f"{topic['id']:<3} {topic['name']:<15} P{topic['priority']}   {static_bw:.1f} Mbps (Nominal Capacity)")
        print()
