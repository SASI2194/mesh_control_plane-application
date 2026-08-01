"""
===============================================================================

Mesh Control Plane

Topic Registry

Loads deployment topics from config/topics.yaml and tracks real-time
measured topic bandwidths.

===============================================================================
"""

import yaml


class TopicRegistry:

    def __init__(self, filename="config/topics.yaml"):

        self._topics = {}

        with open(filename, "r") as f:

            cfg = yaml.safe_load(f)

        for topic in cfg["topics"]:

            # Store both static fallback and measured dynamic bandwidth
            t_copy = dict(topic)
            t_copy["static_bandwidth"] = float(topic.get("bandwidth", 0))
            t_copy["measured_bandwidth"] = float(topic.get("bandwidth", 0))
            self._topics[topic["name"]] = t_copy

    #####################################################################

    def update_measured_bandwidths(self, measured_map: dict):
        """
        Update registry with real-time measured Mbps from BandwidthMonitor.
        """
        for name, mbps in measured_map.items():
            if name in self._topics:
                # If measured Mbps > 0, update measured_bandwidth
                if mbps > 0.0:
                    self._topics[name]["measured_bandwidth"] = mbps
                    self._topics[name]["bandwidth"] = mbps

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

            print(
                f'{topic["id"]:2d}  '
                f'{topic["name"]:12}  '
                f'P{topic["priority"]}  '
                f'{bw:5.1f} Mbps'
            )

        print()
