#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Main Application

===============================================================================
"""

import time

from mesh_transport.zenoh_session import ZenohSession
from mesh_transport.topic_receiver import TopicReceiver
from mesh_transport.key_mapper import KeyMapper

from routing.forwarding_engine import ForwardingEngine

from scheduler.bandwidth_scheduler import BandwidthScheduler
from scheduler.admission_controller import AdmissionController

from ros.topic_database import TopicRegistry
from utils.config_manager import ConfigManager

from core.network_models import MeshSample


PEER_CONFIG = "/home/nvidia/ws_rmw_zenoh/src/rmw_zenoh-humble/rmw_zenoh_cpp/config/tcp/zenoh_peer_tcp.json5"


class MeshNode:

    #####################################################################

    def __init__(self):

        print()
        print("============================================================")
        print("Mesh Control Plane")
        print("============================================================")
        print()

        #
        # Transport Sessions
        #

        self.peer = ZenohSession(PEER_CONFIG)
        self.forward_session = ZenohSession(PEER_CONFIG)

        self.peer.connect()
        self.forward_session.connect()

        #
        # Key Mapper
        #

        self.mapper = KeyMapper()

        #
        # Topic Registry
        #

        self.registry = TopicRegistry()

        self.registry.print_topics()

        #
        # Configuration
        #

        self.config_mgr = ConfigManager()
        self.config_mgr.load()
        mesh_cfg = self.config_mgr.get("mesh")
        self.max_bandwidth = float(mesh_cfg.get("scheduler", {}).get("maximum_bandwidth_mbps", 600.0))

        #
        # Scheduler
        #

        self.scheduler = BandwidthScheduler(self.registry)

        self.scheduler.available_bandwidth = self.max_bandwidth

        self.scheduler.schedule()

        self.scheduler.print_schedule()

        #
        # Admission Controller
        #

        self.admission = AdmissionController(

            self.scheduler

        )

        #
        # Forwarding Engine
        #

        self.forwarding = ForwardingEngine(

            self.forward_session

        )

        #
        # Topic Receiver
        #

        self.receiver = TopicReceiver(

            self.peer,

            self.registry,

            self.callback

        )

        self.receiver.start()

    #####################################################################

    def callback(self, sample):

        #
        # Convert Zenoh transport key
        #
        # 40/topic_01/...
        #
        # into
        #
        # /topic_01
        #

        ros_topic = self.mapper.zenoh_to_ros(

            str(sample.key_expr)

        )

        mesh_sample = MeshSample(

            key=ros_topic,

            payload=sample.payload.to_bytes()

        )

        #
        # Admission
        #

        mesh_sample.allowed = self.admission.evaluate(

            mesh_sample.key

        )

        #
        # Debug
        #

        if mesh_sample.allowed:

            print(f"[ALLOW] {mesh_sample.key}")

        else:

            print(f"[BLOCK ] {mesh_sample.key}")

        #
        # Forward
        #

        self.forwarding.forward(

            mesh_sample

        )

    #####################################################################

    def update_scheduler(self):

        self.scheduler.available_bandwidth = self.max_bandwidth

        self.scheduler.schedule()

    #####################################################################

    def run(self):

        try:

            while True:

                self.update_scheduler()

                time.sleep(1)

        except KeyboardInterrupt:

            self.shutdown()

    #####################################################################

    def shutdown(self):

        print()

        print("Stopping Mesh Control Plane")

        print()

        self.forwarding.statistics()

        self.receiver.stop()

        self.peer.close()

        self.forward_session.close()


########################################################################

if __name__ == "__main__":

    node = MeshNode()

    node.run()
