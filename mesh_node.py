#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Main Application with Real-Time Dynamic Topic Bandwidth Measurement, Sequence Tracking,
Packet Loss Tolerance Congestion Control, Automatic Web Dashboard Telemetry, and Loggers.

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
from utils.scheduler_logger import SchedulerLogger
from monitoring.bandwidth_monitor import RealtimeBandwidthMonitor
from dashboard.server import start_dashboard_background, DATA_PROVIDER

from core.network_models import MeshSample


PEER_CONFIG = "/home/nvidia/ws_rmw_zenoh/src/rmw_zenoh-humble/rmw_zenoh_cpp/config/tcp/zenoh_peer_tcp.json5"


class MeshNode:

    #####################################################################

    def __init__(self):

        print()
        print("============================================================")
        print("Mesh Control Plane (Real-Time Dynamic Rate & Automatic Dashboard)")
        print("============================================================")
        print()

        #
        # Real-time Bandwidth & Hz / Payload Monitor
        #

        self.bw_monitor = RealtimeBandwidthMonitor(window_size_sec=2.0)
        self.scheduler_logger = SchedulerLogger(log_dir="logs")

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
        # Web Dashboard Telemetry Server (Automatic Mode & Live Instance Linking)
        #

        try:
            start_dashboard_background(host="0.0.0.0", port=8080)
            DATA_PROVIDER.attach_components(self.registry, self.scheduler)
            print("[INFO] Web Dashboard Portal active at http://0.0.0.0:8080")
        except Exception as e:
            print(f"[WARNING] Web Dashboard failed to start: {e}")

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
        # Topic Receiver (Automatic Subscription to filtered/** and local ROS topics)
        #

        self.receiver = TopicReceiver(
            self.peer,
            self.registry,
            self.callback
        )

        self.receiver.start()

    #####################################################################

    def callback(self, sample):

        key_str = str(sample.key_expr)
        payload_bytes = sample.payload.to_bytes()

        #
        # Handle Inter-Device Control Plane Samples (filtered/**)
        #

        if key_str.startswith("filtered/"):
            # Incoming sample from another mesh node over physical interface
            seq_num, timestamp, raw_payload = MeshSample.unpack_payload(payload_bytes)
            print(f"[RECV MESH] {key_str} (Seq #{seq_num}, Bytes: {len(raw_payload)})")
            return

        #
        # Handle Local ROS Deployment Topics
        #

        ros_topic = self.mapper.zenoh_to_ros(key_str)
        if not ros_topic:
            return

        #
        # Record real-time bandwidth, Hz, and msg size ONCE per local sample
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
        # Debug & Forwarding
        #

        if mesh_sample.allowed:
            print(f"[ALLOW] {mesh_sample.key} (Seq #{seq_num}, Size: {len(payload_bytes)} B)")
            self.forwarding.forward(
                mesh_sample
            )
        else:
            print(f"[BLOCK ] {mesh_sample.key}")

    #####################################################################

    def update_scheduler(self, current_loss_percent=0.0):

        #
        # Update registry with live measured bandwidths, Hz, and data sizes
        #

        self.registry.update_measured_metrics(
            self.bw_monitor.get_all_metrics()
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

        #
        # Log Priority Scheduler & Real-Time Topic Admission snapshot to log files
        #

        self.scheduler_logger.log_snapshot(self.registry, self.scheduler)

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
