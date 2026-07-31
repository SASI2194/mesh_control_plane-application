"""
===============================================================================

Mesh Control Plane V2

ROS Transport Layer

Every Mesh module communicates through this class.

===============================================================================
"""

import json

import rclpy
from rclpy.node import Node

from std_msgs.msg import String

from utils.logger import MeshLogger


class RosTransport(Node):

    def __init__(self):

        super().__init__("mesh_transport")

        self.logger = MeshLogger.get_logger("RosTransport")

        self.mesh_publishers = {}

        self.mesh_subscribers = {}

    ###########################################################################

    def create_mesh_publisher(self, topic):

        if topic in self.mesh_publishers:

            return

        self.mesh_publishers[topic] = self.create_publisher(
            String,
            topic,
            10
        )

        self.logger.info(f"Publisher Created : {topic}")

    ###########################################################################

    def publish(self, topic, data):

        if topic not in self.mesh_publishers:

            self.create_mesh_publisher(topic)

        msg = String()

        msg.data = json.dumps(data)

        self.mesh_publishers[topic].publish(msg)

    ###########################################################################

    def subscribe(self, topic, callback):

        if topic in self.mesh_subscribers:

            return

        subscriber = self.create_subscription(

            String,

            topic,

            callback,

            10,

        )

        self.mesh_subscribers[topic] = subscriber

        self.logger.info(f"Subscribed : {topic}")
