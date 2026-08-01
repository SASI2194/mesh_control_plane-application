#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Main Application with Real-Time Dynamic Topic Bandwidth Measurement, Sequence Tracking,
and Packet Loss Tolerance Congestion Control.

===============================================================================
"""

import time

from mesh_transport.zenoh_session import ZenohSession
from mesh_transport.topic_receiver import TopicReceiver
from mesh_transport.key_mapper import KeyMapper

from routing.forwarding_engine import ForwardingEngine

from scheduler.bandwidth_scheduler import BandwidthScheduler
from scheduler.admission_controller import AdmissionController
from scheduler.congestion_controller import CongestionController

from ros.topic_database import TopicRegistry
from utils.config_manager import ConfigManager
from monitoring.bandwidth_monitor import RealtimeBandwidthMonitor

from core.network_models import MeshSample


PEER_CONFIG = "/home/nvidia/ws_rmw_zenoh/src/rmw_zenoh-humble/rmw_zenoh_cpp/config/tcp/zenoh_peer_tcp.json5"


class MeshNode:

    #####################################################################

    def __init__(self):

        print()
        print("============================================================")
        print("Mesh Control Plane (Real-Time Dynamic Rate & Congestion Control)")
        print("============================================================")
        print()

        #
        # Real-time Bandwidth Monitor
        #

        self.bw_monitor = RealtimeBandwidthMonitor(window_size_sec=1.0)

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
        sched_cfg = mesh_cfg.get("scheduler", {})

        self.max_bandwidth = float(sched_cfg.get("maximum_bandwidth_mbps", 600.0))
        self.loss_tolerance = float(sched_cfg.get("packet_loss_tolerance_percent", 5.0))
        self.hysteresis = float(sched_cfg.get("hysteresis_percent", 2.0))

        #
        # Scheduler & Congestion Controller
        #

        self.scheduler = BandwidthScheduler(self.registry)
        self.scheduler.available_bandwidth = self.max_bandwidth

        self.congestion = CongestionController(
            tolerance_percent=self.loss_tolerance,
            hysteresis_percent=self.hysteresis
        )

        self.scheduler.schedule()
        self.scheduler.print_schedule()

        print(f"Packet Loss Tolerance Limit: {self.loss_tolerance:.1f} %")
        print()

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
        # Convert Zenoh transport key (e.g. 55/topic_01/...) into ROS topic (/topic_01)
        #

        ros_topic = self.mapper.zenoh_to_ros(

            str(sample.key_expr)

        )

        payload_bytes = sample.payload.to_bytes()

        #
        # Record real-time bandwidth & get sequence number
        #

        seq_num = self.bw_monitor.record_sample(ros_topic, len(payload_bytes))

        mesh_sample = MeshSample(

            key=ros_topic,

            payload=payload_bytes,

            sequence_number=seq_num

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

            print(f"[ALLOW] {mesh_sample.key} (Seq #{seq_num})")

        else:

            print(f"[BLOCK ] {mesh_sample.key}")

        #
        # Forward
        #

        self.forwarding.forward(

            mesh_sample

        )

    #####################################################################

    def update_scheduler(self, current_loss_percent=0.0):

        #
        # Update registry with live measured bandwidths
        #

        self.registry.update_measured_bandwidths(
            self.bw_monitor.get_all_bandwidths()
        )

        self.scheduler.available_bandwidth = self.max_bandwidth

        self.scheduler.schedule()

        #
        # Apply congestion controller feedback and shedding rules
        #

        self.congestion.update_feedback(
            current_loss_percent,
            self.scheduler,
            self.registry
        )

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
