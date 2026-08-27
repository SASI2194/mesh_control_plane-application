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
        Convert Zenoh transport key (e.g. 'filtered/camera/camera/color/image_raw'
        or '55/camera/camera/color/image_raw/**') into clean ROS 2 topic name (e.g. '/camera/camera/color/image_raw').
        """
        if not zenoh_key:
            return ""

        clean_key = zenoh_key
        if clean_key.startswith("filtered/"):
            clean_key = clean_key[len("filtered/"):]
        elif "/" in clean_key:
            parts = clean_key.split("/", 1)
            if parts[0].isdigit():
                clean_key = parts[1]

        if clean_key.endswith("/**"):
            clean_key = clean_key[:-3]
        elif clean_key.endswith("/*"):
            clean_key = clean_key[:-2]

        if not clean_key.startswith("/"):
            clean_key = "/" + clean_key

        return clean_key

    #####################################################################

    def print_example(self):

        print()
        print("============== Key Mapper ==============")
        example = "/topic_01"
        print(example)
        print("↓")
        print(self.ros_to_zenoh(example))
        print()
