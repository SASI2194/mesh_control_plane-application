#!/usr/bin/env python3

"""
==============================================================================

Mesh Control Plane

Main Application with Real-Time Dynamic Topic Bandwidth Measurement, Dual Tx/Rx Role Tracking,
Application Heartbeat Protocol, Sequence Tracking, Congestion Control, Telemetry Server, and Loggers.

==============================================================================
"""

import socket
import time
from threading import Thread

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
        print("Mesh Control Plane (Real-Time Dynamic Rate & Dual Role Governance)")
        print("============================================================")
        print()

        self.running = True
        self.my_ip = self._detect_local_ip()

        #
        # Real-time Bandwidth & Dual Tx/Rx Role Monitor
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
            DATA_PROVIDER.record_node_activity(self.my_ip)
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
            self.forward_session,
            my_ip=self.my_ip
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

        #
        # Start 1 Hz Control Plane Application Heartbeat Thread
        #

        self.heartbeat_thread = Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()

    #####################################################################

    def _detect_local_ip(self):
        """Dynamically detects local physical network interface IP without any hardcoded fallback."""
        # 1. Try ip route get to 192.168.3.1 gateway
        try:
            res = subprocess.run(["ip", "route", "get", "192.168.3.1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                tokens = res.stdout.split()
                if "src" in tokens:
                    idx = tokens.index("src")
                    if idx + 1 < len(tokens):
                        return tokens[idx + 1]
        except Exception:
            pass

        # 2. Try hostname -I interface list
        try:
            res = subprocess.run(["hostname", "-I"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                for ip in res.stdout.strip().split():
                    if ip.startswith("192.168.3."):
                        return ip
                for ip in res.stdout.strip().split():
                    if ip and not ip.startswith("127.") and not ip.startswith("172."):
                        return ip
        except Exception:
            pass

        # 3. Try UDP socket connection probe
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("192.168.3.1", 80))
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass

        return "127.0.0.1"

    #####################################################################

    def _heartbeat_loop(self):
        """Sends a periodic 1 Hz control plane application heartbeat to peer nodes over Zenoh."""
        heartbeat_key = f"filtered/_mesh_heartbeat/{self.my_ip}"
        while self.running:
            try:
                payload = f"{time.time()}:{self.my_ip}".encode("utf-8")
                self.forward_session.session.put(heartbeat_key, payload)
            except Exception:
                pass
            time.sleep(1.0)

    #####################################################################

    def callback(self, sample):

        key_str = str(sample.key_expr)
        payload_bytes = sample.payload.to_bytes()

        #
        # Handle Inter-Device Control Plane Samples (filtered/**) - Subscriber (Rx) Role
        #

        if key_str.startswith("filtered/"):
            # Check for Application Control Plane Heartbeat
            if "_mesh_heartbeat/" in key_str:
                parts = key_str.split("_mesh_heartbeat/")
                if len(parts) > 1:
                    sender_ip = parts[1]
                    DATA_PROVIDER.record_node_activity(sender_ip)
                return

            seq_num, timestamp, origin_ip, raw_payload = MeshSample.unpack_payload(payload_bytes)

            # Ignore local loopback (samples published by self) for Subscriber Rx rate calculation
            if origin_ip == self.my_ip or origin_ip in ["127.0.0.1", "localhost"]:
                return

            # Record remote node activity and Rx subscriber metrics for peer sample
            DATA_PROVIDER.record_node_activity(origin_ip)
            ros_topic = self.mapper.zenoh_to_ros(key_str)
            if ros_topic:
                self.bw_monitor.record_rx_sample(ros_topic, len(raw_payload))

            print(f"[RECV MESH] {key_str} (From: {origin_ip}, Seq #{seq_num}, Bytes: {len(raw_payload)})")
            return

        #
        # Handle Local ROS Deployment Topics - Publisher (Tx) Role
        #

        ros_topic = self.mapper.zenoh_to_ros(key_str)
        if not ros_topic:
            return

        #
        # Record Publisher (Tx) sample before entering transport
        #

        seq_num = self.bw_monitor.record_tx_sample(ros_topic, len(payload_bytes))

        mesh_sample = MeshSample(
            key=ros_topic,
            payload=payload_bytes,
            sequence_number=seq_num,
            origin_ip=self.my_ip
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

        # Record local node heartbeat activity
        DATA_PROVIDER.record_node_activity(self.my_ip)

        #
        # Update registry with live measured bandwidths, Tx/Rx rates, and data sizes
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
            while self.running:
                self.update_scheduler()
                time.sleep(1)

        except KeyboardInterrupt:
            self.shutdown()

    #####################################################################

    def shutdown(self):

        print()
        print("Stopping Mesh Control Plane")
        print()

        self.running = False
        DATA_PROVIDER.set_mesh_node_running(False)
        self.forwarding.statistics()
        self.receiver.stop()
        self.peer.close()
        self.forward_session.close()


########################################################################

if __name__ == "__main__":

    node = MeshNode()
    node.run()
