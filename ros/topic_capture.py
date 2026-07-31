"""
===============================================================================

Mesh Control Plane V2

File : topic_capture.py

Purpose:
    Discover application ROS topics.

===============================================================================
"""

import rclpy

from rclpy.node import Node


class TopicCapture(Node):

    """
    Discovers ROS topics that belong to the application.

    Mesh topics and ROS internal topics are ignored.
    """

    def __init__(self):

        super().__init__("mesh_topic_capture")

        self.ignore_prefix = [

            "/mesh",

            "/parameter_events",

            "/rosout"

        ]

    ###########################################################################

    def discover_topics(self):

        """
        Returns all application topics.
        """

        topics = self.get_topic_names_and_types()

        application_topics = []

        for topic_name, topic_type in topics:

            ignore = False

            for prefix in self.ignore_prefix:

                if topic_name.startswith(prefix):

                    ignore = True

                    break

            if ignore:

                continue

            application_topics.append(

                {

                    "name": topic_name,

                    "type": topic_type[0]

                }

            )

        application_topics.sort(

            key=lambda x: x["name"]

        )

        return application_topics
