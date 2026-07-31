"""
===============================================================================

Mesh Control Plane

Topic Registry

Loads deployment topics from config/topics.yaml

===============================================================================
"""

import yaml


class TopicRegistry:

    def __init__(self, filename="config/topics.yaml"):

        self._topics = {}

        with open(filename, "r") as f:

            cfg = yaml.safe_load(f)

        for topic in cfg["topics"]:

            self._topics[topic["name"]] = topic

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

            print(
                f'{topic["id"]:2d}  '
                f'{topic["name"]:12}  '
                f'P{topic["priority"]}  '
                f'{topic["bandwidth"]:3d} Mbps'
            )

        print()
