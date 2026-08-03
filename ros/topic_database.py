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

            # Store both static fallback and measured dynamic metrics
            t_copy = dict(topic)
            t_copy["static_bandwidth"] = float(topic.get("bandwidth", 0))
            t_copy["measured_bandwidth"] = float(topic.get("bandwidth", 0))
            t_copy["hz"] = 0.0
            t_copy["data_size_bytes"] = 0.0
            t_copy["data_size_str"] = "0 B"
            self._topics[topic["name"]] = t_copy

    #####################################################################

    def update_measured_bandwidths(self, measured_map: dict):
        """
        Update registry with real-time measured Mbps map.
        """
        for name, val in measured_map.items():
            if name in self._topics:
                if isinstance(val, dict):
                    mbps = val.get("mbps", 0.0)
                    hz = val.get("hz", 0.0)
                    data_size_str = val.get("data_size_str", "0 B")

                    if mbps > 0.0 or hz > 0.0:
                        self._topics[name]["measured_bandwidth"] = mbps
                        self._topics[name]["bandwidth"] = mbps
                        self._topics[name]["hz"] = hz
                        self._topics[name]["data_size_str"] = data_size_str
                else:
                    mbps = float(val)
                    if mbps > 0.0:
                        self._topics[name]["measured_bandwidth"] = mbps
                        self._topics[name]["bandwidth"] = mbps

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

            bw = topic.get("measured_bandwidth", topic.get("bandwidth", 0))
            hz = topic.get("hz", 0.0)
            sz = topic.get("data_size_str", "0 B")

            print(
                f'{topic["id"]:2d}  '
                f'{topic["name"]:12}  '
                f'P{topic["priority"]}  '
                f'{bw:5.1f} Mbps  '
                f'({hz:4.1f} Hz, {sz})'
            )

        print()
