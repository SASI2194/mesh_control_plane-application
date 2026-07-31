#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Zenoh Transport Key Mapper

Maps ROS topics to Zenoh transport keys and vice versa.

===============================================================================
"""

import os


class KeyMapper:

    #####################################################################

    def __init__(self):

        #
        # ROS Domain ID
        #

        self.domain = os.getenv("ROS_DOMAIN_ID", "40")

        #
        # Current deployment uses CompressedImage
        #

        self.type_name = (
            "sensor_msgs::msg::dds_::CompressedImage_/TypeHashNotSupported"
        )

    #####################################################################

    def ros_to_zenoh(self, ros_topic: str) -> str:
        """
        Convert

            /topic_01

        into

            40/topic_01/sensor_msgs::msg::dds_::CompressedImage_/TypeHashNotSupported
        """

        if ros_topic.startswith("/"):
            ros_topic = ros_topic[1:]

        return f"{self.domain}/{ros_topic}/{self.type_name}"

    #####################################################################

    def zenoh_to_ros(self, zenoh_key: str) -> str:
        """
        Convert

            40/topic_01/sensor_msgs::...

        into

            /topic_01
        """

        parts = zenoh_key.split("/")

        if len(parts) < 2:
            return ""

        return "/" + parts[1]

    #####################################################################

    def print_example(self):

        print()

        print("============== Key Mapper ==============")

        example = "/topic_01"

        print(example)

        print("↓")

        print(self.ros_to_zenoh(example))

        print()
