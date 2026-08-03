#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Zenoh Transport Key Mapper

Maps ROS topics to Zenoh transport keys using robust wildcard matching.

===============================================================================
"""

import os


class KeyMapper:

    #####################################################################

    def __init__(self):

        self.domain = os.getenv("ROS_DOMAIN_ID", "40")

    #####################################################################

    def ros_to_zenoh(self, ros_topic: str) -> str:
        """
        Convert

            /topic_01

        into wildcard Zenoh key matcher:

            **/topic_01/**
        """

        if ros_topic.startswith("/"):
            clean_topic = ros_topic[1:]
        else:
            clean_topic = ros_topic

        return f"**/{clean_topic}/**"

    #####################################################################

    def zenoh_to_ros(self, zenoh_key: str) -> str:
        """
        Convert

            55/topic_01/sensor_msgs::...  OR  filtered/topic_01

        into

            /topic_01
        """

        parts = zenoh_key.split("/")
        for part in parts:
            if part.startswith("topic_"):
                return "/" + part
            elif part in ["topic_01", "topic_02", "topic_03", "topic_04", "topic_05",
                          "topic_06", "topic_07", "topic_08", "topic_09", "topic_10",
                          "topic_11", "topic_12", "topic_13", "topic_14", "topic_15",
                          "topic_16", "topic_17", "topic_18", "topic_19", "topic_20"]:
                return "/" + part

        return ""

    #####################################################################

    def print_example(self):

        print()

        print("============== Key Mapper ==============")

        example = "/topic_01"

        print(example)

        print("↓")

        print(self.ros_to_zenoh(example))

        print()
