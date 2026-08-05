#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Zenoh Transport Key Mapper

Maps ROS topics to Zenoh transport keys using specific domain matching
to prevent loopback matching on control plane topics (filtered/**).

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

        into explicit domain matcher excluding filtered/** keys:

            */topic_01/**
        """

        if ros_topic.startswith("/"):
            clean_topic = ros_topic[1:]
        else:
            clean_topic = ros_topic

        # Use explicit ROS domain ID prefix (e.g. 40/topic_01/** or 0/topic_01/**)
        # to subscribe strictly to local ROS topics without double-matching filtered/**
        return f"{self.domain}/{clean_topic}/**"

    #####################################################################

    def zenoh_to_ros(self, zenoh_key: str) -> str:
        """
        Convert

            40/topic_01/sensor_msgs::...  OR  filtered/topic_01

        into

            /topic_01
        """

        parts = zenoh_key.split("/")
        for part in parts:
            if part.startswith("topic_"):
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
