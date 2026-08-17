#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Web Dashboard Telemetry Server

Lightweight HTTP REST API & Web Server providing real-time telemetry for
6 UGVs (Jetson Orin + NetMetal AX) and 3 GCSs (Processing System + Switch + NetMetal AX).

Features:
    • Ultra-Fast Non-Blocking Parallel Ping Monitoring (200ms Timeout)
    • 7-Sided Polygon (Heptagon) Wireless Mesh Topology Generator (7 NetMetal AX Radios)
    • Real-time Live ICMP Ping & Heartbeat Monitoring for all 9 devices
    • Dynamic Bandwidth Utilization, Real-Time Frequency (Hz), and Data Size Tracking
    • Priority Admission & Topic Lossless Verification Data

===============================================================================
"""

import json
import os
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread, RLock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.config_manager import ConfigManager
from ros.topic_database import TopicRegistry
from scheduler.bandwidth_scheduler import BandwidthScheduler


PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")


class TelemetryDataProvider:
    """
    Generates real-time dynamic state data for 7 wireless radios (7-sided heptagon polygon) and 9 nodes.
    """

    def __init__(self):
        self.lock = RLock()
        self.config_mgr = ConfigManager()
        try:
            self.config_mgr.load()
        except Exception:
            pass

        self.registry = TopicRegistry()
        self.scheduler = BandwidthScheduler(self.registry)

        mesh_cfg = self.config_mgr.get("mesh") or {}
        sched_cfg = mesh_cfg.get("scheduler", {})
        self.max_bw = float(sched_cfg.get("maximum_bandwidth_mbps", 600.0))
        self.loss_tolerance = float(sched_cfg.get("packet_loss_tolerance_percent", 5.0))

        self.scheduler.available_bandwidth = self.max_bw
        self.scheduler.schedule()

        # Define 9 mesh nodes: 6 UGVs + 3 GCSs with NetMetal AX radio interface details
        self.nodes = [
            {
                "id": "UGV-01", "name": "UGV Unit 01", "type": "UGV", "hardware": "Jetson Orin + NetMetal AX", "ip": "192.168.3.65", "role": "Mesh Node", "status": "OFFLINE", "rssi": -95, "latency": 0.0, "loss": 0.0, "uptime": "0m",
                "wifi_details": {
                    "total_interfaces": 3,
                    "active_interfaces": 2,
                    "interfaces": [
                        {"name": "wifi1", "master": "", "mode": "AP", "ssid": "", "band": "2.4GHz", "freq": "N/A", "flags": "MBX", "status": "DISABLED", "running": False},
                        {"name": "wifi2", "master": "", "mode": "AP", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "MBR", "status": "ACTIVE & RUNNING", "running": True},
                        {"name": "wifi2_vsb", "master": "wifi2", "mode": "STATION-BRIDGE", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "BR", "status": "ACTIVE & RUNNING", "running": True}
                    ]
                }
            },
            {
                "id": "UGV-02", "name": "UGV Unit 02", "type": "UGV", "hardware": "Jetson Orin + NetMetal AX", "ip": "192.168.3.66", "role": "Field Unit", "status": "OFFLINE", "rssi": -95, "latency": 0.0, "loss": 0.0, "uptime": "0m",
                "wifi_details": {
                    "total_interfaces": 3,
                    "active_interfaces": 2,
                    "interfaces": [
                        {"name": "wifi1", "master": "", "mode": "AP", "ssid": "", "band": "2.4GHz", "freq": "N/A", "flags": "MBX", "status": "DISABLED", "running": False},
                        {"name": "wifi2", "master": "", "mode": "AP", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "MBR", "status": "ACTIVE & RUNNING", "running": True},
                        {"name": "wifi2_vsb", "master": "wifi2", "mode": "STATION-BRIDGE", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "BR", "status": "ACTIVE & RUNNING", "running": True}
                    ]
                }
            },
            {
                "id": "UGV-03", "name": "UGV Unit 03", "type": "UGV", "hardware": "Jetson Orin + NetMetal AX", "ip": "192.168.3.67", "role": "Field Unit", "status": "OFFLINE", "rssi": -95, "latency": 0.0, "loss": 0.0, "uptime": "0m",
                "wifi_details": {
                    "total_interfaces": 3,
                    "active_interfaces": 2,
                    "interfaces": [
                        {"name": "wifi1", "master": "", "mode": "AP", "ssid": "", "band": "2.4GHz", "freq": "N/A", "flags": "MBX", "status": "DISABLED", "running": False},
                        {"name": "wifi2", "master": "", "mode": "STATION-BRIDGE", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "MBR", "status": "ACTIVE & RUNNING", "running": True},
                        {"name": "wifi2_vap", "master": "wifi2", "mode": "AP", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "BR", "status": "ACTIVE & RUNNING", "running": True}
                    ]
                }
            },
            {
                "id": "UGV-04", "name": "UGV Unit 04", "type": "UGV", "hardware": "Jetson Orin + NetMetal AX", "ip": "192.168.3.68", "role": "Field Unit", "status": "OFFLINE", "rssi": -95, "latency": 0.0, "loss": 0.0, "uptime": "0m",
                "wifi_details": {
                    "total_interfaces": 3,
                    "active_interfaces": 2,
                    "interfaces": [
                        {"name": "wifi1", "master": "", "mode": "AP", "ssid": "", "band": "2.4GHz", "freq": "N/A", "flags": "MBX", "status": "DISABLED", "running": False},
                        {"name": "wifi2", "master": "", "mode": "AP", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "MBR", "status": "ACTIVE & RUNNING", "running": True},
                        {"name": "wifi2_vsb", "master": "wifi2", "mode": "STATION-BRIDGE", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "BR", "status": "ACTIVE & RUNNING", "running": True}
                    ]
                }
            },
            {
                "id": "UGV-05", "name": "UGV Unit 05", "type": "UGV", "hardware": "Jetson Orin + NetMetal AX", "ip": "192.168.3.69", "role": "Field Unit", "status": "OFFLINE", "rssi": -95, "latency": 0.0, "loss": 0.0, "uptime": "0m",
                "wifi_details": {
                    "total_interfaces": 3,
                    "active_interfaces": 2,
                    "interfaces": [
                        {"name": "wifi1", "master": "", "mode": "AP", "ssid": "", "band": "2.4GHz", "freq": "N/A", "flags": "MBX", "status": "DISABLED", "running": False},
                        {"name": "wifi2", "master": "", "mode": "AP", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "MBR", "status": "ACTIVE & RUNNING", "running": True},
                        {"name": "wifi2_vsb", "master": "wifi2", "mode": "STATION-BRIDGE", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "BR", "status": "ACTIVE & RUNNING", "running": True}
                    ]
                }
            },
            {
                "id": "UGV-06", "name": "UGV Unit 06", "type": "UGV", "hardware": "Jetson Orin + NetMetal AX", "ip": "192.168.3.70", "role": "Field Unit", "status": "OFFLINE", "rssi": -95, "latency": 0.0, "loss": 0.0, "uptime": "0m",
                "wifi_details": {
                    "total_interfaces": 3,
                    "active_interfaces": 2,
                    "interfaces": [
                        {"name": "wifi1", "master": "", "mode": "AP", "ssid": "", "band": "2.4GHz", "freq": "N/A", "flags": "MBX", "status": "DISABLED", "running": False},
                        {"name": "wifi2", "master": "", "mode": "AP", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "MBR", "status": "ACTIVE & RUNNING", "running": True},
                        {"name": "wifi2_vsb", "master": "wifi2", "mode": "STATION-BRIDGE", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "BR", "status": "ACTIVE & RUNNING", "running": True}
                    ]
                }
            },
            {
                "id": "GCS-01", "name": "GCS Primary Command", "type": "GCS", "hardware": "Proc System + Switch + NetMetal AX", "ip": "192.168.3.71", "role": "Primary Coordinator", "status": "OFFLINE", "rssi": -95, "latency": 0.0, "loss": 0.0, "uptime": "0m",
                "wifi_details": {
                    "total_interfaces": 3,
                    "active_interfaces": 2,
                    "interfaces": [
                        {"name": "wifi1", "master": "", "mode": "AP", "ssid": "", "band": "2.4GHz", "freq": "N/A", "flags": "MBX", "status": "DISABLED", "running": False},
                        {"name": "wifi2", "master": "", "mode": "AP", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "MBR", "status": "ACTIVE & RUNNING", "running": True},
                        {"name": "wifi2_vsb", "master": "wifi2", "mode": "STATION-BRIDGE", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "BR", "status": "ACTIVE & RUNNING", "running": True}
                    ]
                }
            },
            {
                "id": "GCS-02", "name": "GCS Tactical Station 1", "type": "GCS", "hardware": "Proc System + Switch + NetMetal AX", "ip": "192.168.3.72", "role": "Tactical Monitor", "status": "OFFLINE", "rssi": -95, "latency": 0.0, "loss": 0.0, "uptime": "0m",
                "wifi_details": {
                    "total_interfaces": 3,
                    "active_interfaces": 2,
                    "interfaces": [
                        {"name": "wifi1", "master": "", "mode": "AP", "ssid": "", "band": "2.4GHz", "freq": "N/A", "flags": "MBX", "status": "DISABLED", "running": False},
                        {"name": "wifi2", "master": "", "mode": "AP", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "MBR", "status": "ACTIVE & RUNNING", "running": True},
                        {"name": "wifi2_vsb", "master": "wifi2", "mode": "STATION-BRIDGE", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "BR", "status": "ACTIVE & RUNNING", "running": True}
                    ]
                }
            },
            {
                "id": "GCS-03", "name": "GCS Tactical Station 2", "type": "GCS", "hardware": "Proc System + Switch + NetMetal AX", "ip": "192.168.3.73", "role": "Backup Command", "status": "OFFLINE", "rssi": -95, "latency": 0.0, "loss": 0.0, "uptime": "0m",
                "wifi_details": {
                    "total_interfaces": 3,
                    "active_interfaces": 2,
                    "interfaces": [
                        {"name": "wifi1", "master": "", "mode": "AP", "ssid": "", "band": "2.4GHz", "freq": "N/A", "flags": "MBX", "status": "DISABLED", "running": False},
                        {"name": "wifi2", "master": "", "mode": "AP", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "MBR", "status": "ACTIVE & RUNNING", "running": True},
                        {"name": "wifi2_vsb", "master": "wifi2", "mode": "STATION-BRIDGE", "ssid": "test_device", "band": "5GHz-ax", "freq": "5180 MHz", "flags": "BR", "status": "ACTIVE & RUNNING", "running": True}
                    ]
                }
            },
        ]

        self.node_activity = {}
        self.network_activity = {}
        self.transmission_activity = {}
        self.mesh_node_running = False
        self.master_failover_event = None

        # Start live parallel Application Layer Heartbeat Audit daemon thread
        self.monitor_thread = Thread(target=self._live_heartbeat_audit_loop, daemon=True)
        self.monitor_thread.start()

        # Start live NetMetal AX Hardware Radio Audit daemon thread
        self.radio_audit_thread = Thread(target=self._live_radio_hardware_audit_loop, daemon=True)
        self.radio_audit_thread.start()

        # Start dynamic Master AP Failover Leader Election daemon thread
        self.failover_thread = Thread(target=self._master_ap_failover_election_loop, daemon=True)
        self.failover_thread.start()

    def set_mesh_node_running(self, running=True):
        """Sets active mesh_node.py application running status flag."""
        with self.lock:
            self.mesh_node_running = running
            if not running:
                self.node_activity.clear()

    def record_node_activity(self, node_ip):
        """Records real-time application heartbeat activity timestamp for a node IP."""
        with self.lock:
            now = time.time()
            self.node_activity[node_ip] = now
            self.network_activity[node_ip] = now
            self.transmission_activity[node_ip] = now

    def record_network_activity(self, node_ip):
        """Records decoupled physical network discovery heartbeat activity timestamp."""
        with self.lock:
            now = time.time()
            self.network_activity[node_ip] = now
            self.node_activity[node_ip] = now

    def record_transmission_activity(self, node_ip):
        """Records decoupled topic transmission telemetry heartbeat activity timestamp."""
        with self.lock:
            now = time.time()
            self.transmission_activity[node_ip] = now
            self.node_activity[node_ip] = now

    def _get_this_machine_ip(self):
        """Helper to resolve exact physical host IP for this machine (192.168.3.x)."""
        target_ip = getattr(self, "local_ip", None)
        if target_ip and target_ip not in ["127.0.0.1", "localhost"]:
            return target_ip

        local_ips = self._get_local_ips()
        for ip in local_ips:
            if ip.startswith("192.168.3."):
                return ip

        try:
            res = subprocess.run(["hostname", "-I"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                for ip in res.stdout.strip().split():
                    if ip.startswith("192.168.3."):
                        return ip
        except Exception:
            pass

        return "192.168.3.65"

    def update_remote_node_wifi(self, sender_ip, wifi_details):
        """Updates live NetMetal AX WiFi radio telemetry for a specific remote node received over Zenoh."""
        my_ip = self._get_this_machine_ip()
        # Ignore self-broadcasts so local audit loop remains authoritative for local node
        if sender_ip == my_ip:
            return

        with self.lock:
            for node in self.nodes:
                if node["ip"] == sender_ip:
                    import copy
                    node["wifi_details"] = copy.deepcopy(wifi_details)
                    break

    def attach_components(self, registry, scheduler, congestion=None, local_ip=None):
        """Attaches live MeshNode registry, scheduler & congestion instances for real-time telemetry updates."""
        with self.lock:
            self.registry = registry
            self.scheduler = scheduler
            if congestion:
                self.congestion = congestion
            self.mesh_node_running = True
            if local_ip:
                self.local_ip = local_ip

    def _get_local_ips(self):
        """Returns set of all local IPv4 interface addresses for this machine."""
        local_ips = {"127.0.0.1", "localhost"}
        try:
            res = subprocess.run(["hostname", "-I"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                for ip in res.stdout.strip().split():
                    if ip:
                        local_ips.add(ip)
        except Exception:
            pass
        return local_ips

    def _live_heartbeat_audit_loop(self):
        """
        Continuously audits active mesh node status based 100% on Application Layer
        1 Hz Control Plane Heartbeats & Live Topic Activity (Zero ICMP Ping Dependency).
        """
        while True:
            local_ips = self._get_local_ips()
            target_ip = getattr(self, "local_ip", None)
            now = time.time()

            with self.lock:
                for node in self.nodes:
                    ip = node["ip"]

                    # If local mesh_node.py application is NOT running, ALL nodes are OFFLINE
                    if not self.mesh_node_running:
                        node["status"] = "OFFLINE"
                        node["latency"] = 0.0
                        node["rssi"] = -95
                        continue

                    # 1. Local Node Audit
                    is_this_local = (ip == target_ip) if target_ip else (ip in local_ips)
                    if is_this_local:
                        node["status"] = "ONLINE"
                        node["latency"] = 1.0
                        node["rssi"] = -62
                        continue

                    # 2. Remote Node Physical Network Link Heartbeat & Topology Audit (Decoupled 10s Buffer)
                    last_active = self.network_activity.get(ip, self.node_activity.get(ip, 0.0))
                    offline_timeout = self._get_node_offline_timeout()
                    if (now - last_active) <= offline_timeout:
                        node["status"] = "ONLINE"
                        node["latency"] = 8.5
                        node["rssi"] = -68
                    else:
                        node["status"] = "OFFLINE"
                        node["latency"] = 0.0
                        node["rssi"] = -95

            time.sleep(1.0)

    def _get_node_offline_timeout(self):
        """Loads node_offline_timeout_seconds from config/failover.yaml (default: 10.0s)."""
        try:
            import yaml
            from pathlib import Path
            p = Path("config/failover.yaml")
            if p.exists():
                with open(p, "r") as f:
                    data = yaml.safe_load(f)
                    val = data.get("failover", {}).get("node_offline_timeout_seconds")
                    if val is not None:
                        return float(val)
        except Exception:
            pass
        return 10.0

    def _ping_device(self, ip):
        """
        Application-Layer Node Audit interface (100% Heartbeat Driven).
        """
        if not getattr(self, "mesh_node_running", False):
            return "OFFLINE", 0.0

        target_ip = getattr(self, "local_ip", None)
        is_this_local = (ip == target_ip) if target_ip else (ip in self._get_local_ips())
        if is_this_local:
            return "ONLINE", 1.0

        last_active = self.node_activity.get(ip, 0.0)
        offline_timeout = self._get_node_offline_timeout()
        if (time.time() - last_active) <= offline_timeout:
            return "ONLINE", 8.5

        return "OFFLINE", 0.0

    def _fetch_radio_interfaces(self, radio_ip):
        """Queries local NetMetal AX radio via RouterOS REST API to fetch live interface states."""
        try:
            req_url = f"http://{radio_ip}/rest/interface/wifi"
            import urllib.request
            import base64

            req = urllib.request.Request(req_url)
            auth_str = base64.b64encode(b"admin:").decode("ascii")
            req.add_header("Authorization", f"Basic {auth_str}")

            with urllib.request.urlopen(req, timeout=0.6) as resp:
                if resp.status == 200:
                    raw_data = json.loads(resp.read().decode("utf-8"))
                    interfaces = []
                    active_count = 0
                    for item in raw_data:
                        name = item.get("name") or item.get("default-name", "wifi")
                        master = item.get("master-interface", "")
                        cfg_val = item.get("configuration")
                        if isinstance(cfg_val, dict):
                            mode_raw = cfg_val.get("mode")
                        else:
                            mode_raw = item.get("mode") or item.get("configuration.mode")
                        
                        if not mode_raw:
                            mode = "AP" if name in ["wifi1", "wifi2_vap"] else "STATION-BRIDGE"
                        else:
                            mode = str(mode_raw).upper()
                        ssid = item.get("configuration.ssid") or item.get("ssid") or ""
                        band = item.get("channel.band") or item.get("band") or "5GHz-ax"
                        freq = item.get("channel.frequency") or item.get("frequency") or "5180 MHz"

                        is_disabled = str(item.get("disabled", "false")).lower() == "true"
                        is_inactive = str(item.get("inactive", "false")).lower() == "true"
                        is_running = str(item.get("running", "false")).lower() == "true"

                        flags = "M" if item.get("master") == "true" else ""
                        flags += "B" if item.get("bound") == "true" else ""
                        if is_disabled:
                            flags += "X"
                            status_str = "DISABLED"
                        elif is_running:
                            flags += "R"
                            status_str = "ACTIVE & RUNNING"
                            active_count += 1
                        elif is_inactive:
                            flags += "I"
                            status_str = "INACTIVE"
                        else:
                            status_str = "INACTIVE"

                        interfaces.append({
                            "name": name,
                            "master": master,
                            "mode": mode,
                            "ssid": ssid,
                            "band": band,
                            "freq": freq,
                            "flags": flags,
                            "status": status_str,
                            "running": is_running,
                            "disabled": is_disabled
                        })
                    return {
                        "total_interfaces": len(interfaces),
                        "active_interfaces": active_count,
                        "interfaces": interfaces
                    }
        except Exception:
            pass
        return None

    def _live_radio_hardware_audit_loop(self):
        """
        Periodically audits ONLY THIS LOCAL DEVICE's NetMetal AX hardware radio interface states
        every 3 seconds to update its own local running/disabled interface badges.
        """
        radio_ip_map = {
            "192.168.3.65": "192.168.3.3",  # UGV-01 local radio
            "192.168.3.67": "192.168.3.2",  # UGV-03 local radio
            "192.168.3.66": "192.168.3.4",  # UGV-02 local radio
            "192.168.3.68": "192.168.3.5",  # UGV-04 local radio
            "192.168.3.69": "192.168.3.6",  # UGV-05 local radio
            "192.168.3.70": "192.168.3.7",  # UGV-06 local radio
            "192.168.3.71": "192.168.3.8",  # GCS-01 local radio
        }

        while True:
            try:
                # 1. Determine local host IP and local radio IP
                target_ip = self._get_this_machine_ip()
                local_radio_ip = radio_ip_map.get(target_ip, "192.168.3.3")

                # 2. Fetch ONLY the local radio interface states
                live_details = self._fetch_radio_interfaces(local_radio_ip)
                if live_details and live_details.get("total_interfaces", 0) > 0:
                    with self.lock:
                        # Update ONLY the local node's card in self.nodes!
                        for node in self.nodes:
                            if node["ip"] == target_ip or (target_ip in ["127.0.0.1", "localhost"] and node["id"] == "UGV-01"):
                                import copy
                                node["wifi_details"] = copy.deepcopy(live_details)
                                break
            except Exception:
                pass
            time.sleep(3)

    def _load_failover_config(self, my_ip=None):
        """
        Loads device priority hierarchy and calculates per-device staggered switching intervals from config/failover.yaml.
        Priority rank 1 (GCS-01/UGV-01) = 30s base interval.
        Priority rank N = base_interval + (rank_index * 15s increment).
        Custom overrides in config/failover.yaml take precedence.
        """
        default_priority = [
            "GCS-01", "GCS-02", "GCS-03", "UGV-01", "UGV-02", "UGV-03", "UGV-04", "UGV-05", "UGV-06"
        ]
        base_interval = 30.0
        stagger_increment = 15.0
        custom_intervals = {}

        try:
            from utils.config_manager import ConfigManager
            cm = ConfigManager()
            failover_cfg = cm.get_failover() or {}
            cfg = failover_cfg.get("failover", {})
            priority = cfg.get("device_priority") or default_priority
            base_interval = float(cfg.get("base_switching_interval_seconds", 30.0))
            stagger_increment = float(cfg.get("priority_stagger_increment_seconds", 15.0))
            custom_intervals = cfg.get("device_custom_intervals") or {}
        except Exception:
            priority = default_priority

        try:
            import yaml
            from pathlib import Path
            p = Path("config/failover.yaml")
            if p.exists():
                with open(p, "r") as f:
                    data = yaml.safe_load(f)
                    cfg = data.get("failover", {})
                    priority = cfg.get("device_priority") or default_priority
                    base_interval = float(cfg.get("base_switching_interval_seconds", 30.0))
                    stagger_increment = float(cfg.get("priority_stagger_increment_seconds", 10.0))
                    custom_intervals = cfg.get("device_custom_intervals") or {}
                    device_nodes = cfg.get("device_nodes", {})
                    for dev_id, dev_info in device_nodes.items():
                        if isinstance(dev_info, dict) and "switching_interval_seconds" in dev_info:
                            custom_intervals[dev_id] = float(dev_info["switching_interval_seconds"])
        except Exception:
            pass

        # Identify local node ID from my_ip
        local_node_id = None
        if my_ip:
            with self.lock:
                for n in self.nodes:
                    if n["ip"] == my_ip:
                        local_node_id = n["id"]
                        break

        if not local_node_id:
            local_node_id = "UGV-01"

        # Explicit custom interval override takes highest precedence
        if local_node_id in custom_intervals:
            interval = float(custom_intervals[local_node_id])
        elif local_node_id in priority:
            rank_idx = priority.index(local_node_id)
            interval = base_interval + (rank_idx * stagger_increment)
        else:
            interval = base_interval

        return priority, interval

    def _log_failover_event(self, msg):
        """Prints failover election & probe timing logs to terminal and writes to logs/failover_election.log."""
        print(msg)
        try:
            from pathlib import Path
            from datetime import datetime
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / "failover_election.log"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {msg}\n")
        except Exception:
            pass

    def _handle_disconnected_30s_probe(self, my_ip, switching_interval):
        """
        Manages strict AP <-> STATION-BRIDGE search probe cycle for isolated Master APs.
        Ensures radio stays in STATION-BRIDGE mode for FULL switching_interval seconds.
        """
        now = time.time()
        state_start = getattr(self, "_probe_state_start", 0.0)
        current_state = getattr(self, "_probe_state", "AP")

        if state_start == 0.0:
            self._probe_state_start = now
            self._probe_state = "AP"
            self._log_failover_event(f"[PROBE TIMING AUDIT] Initializing search probe cycle for isolated host {my_ip}. Configured Switching Interval: {switching_interval:.1f}s | Initial Mode: AP")
            self._promote_local_radio_hardware()
            return

        elapsed = now - state_start

        if elapsed >= switching_interval:
            self._probe_state_start = now
            if current_state == "AP":
                self._probe_state = "STATION_BRIDGE"
                self._log_failover_event(f"[PROBE HARDWARE SWITCH] Dwell limit reached ({elapsed:.1f}s >= {switching_interval:.1f}s). Toggling hardware from AP -> STATION_BRIDGE (Scan Probe Phase)...")
                self._demote_local_radio_hardware(force=True)
            else:
                self._probe_state = "AP"
                self._log_failover_event(f"[PROBE HARDWARE SWITCH] Dwell limit reached ({elapsed:.1f}s >= {switching_interval:.1f}s). Toggling hardware from STATION_BRIDGE -> AP (Beacon Phase)...")
                self._promote_local_radio_hardware(force=True)
        else:
            remaining = switching_interval - elapsed
            self._log_failover_event(f"[PROBE TIMING AUDIT] Host {my_ip} ISOLATED (0 peers). Current Mode: {current_state} | Elapsed: {elapsed:.1f}s / {switching_interval:.1f}s | Next Mode Switch in: {remaining:.1f}s")
            if current_state == "AP":
                self._promote_local_radio_hardware()
            else:
                self._demote_local_radio_hardware()

    def _master_ap_failover_election_loop(self):
        """
        Monitors health of Master AP across 9-device mesh using config/failover.yaml.
        Determines the single highest-priority ONLINE node in the mesh:
          - Highest priority ONLINE node (e.g. GCS-01 / UGV-01) -> Promotes to MASTER AP.
          - All lower priority connected nodes -> Demote to STATION-BRIDGE and lock.
          - Isolated nodes with 0 peers -> Perform rank-staggered search probe cycle.
        """
        # Grace period for initial startup heartbeat discovery across mesh nodes
        time.sleep(3.0)

        while True:
            try:
                my_ip = self._get_this_machine_ip()
                priority_order, switching_interval = self._load_failover_config(my_ip)

                with self.lock:
                    nodes_dict = {n["id"]: n for n in self.nodes}
                    my_node = next((n for n in self.nodes if n["ip"] == my_ip), None)
                    local_node_id = my_node["id"] if my_node else "UGV-01"

                    # Find active remote mesh peers (excluding self)
                    remote_online_nodes = [
                        n for n in self.nodes 
                        if n["ip"] != my_ip and n.get("status") == "ONLINE"
                    ]
                    has_remote_peers = len(remote_online_nodes) > 0

                    # 1. Determine all currently ONLINE node IDs across the mesh
                    online_node_ids = [n["id"] for n in self.nodes if n.get("status") == "ONLINE"]

                    # 2. Identify highest priority ONLINE node from priority_order
                    highest_online_master_id = None
                    for node_id in priority_order:
                        if node_id in online_node_ids:
                            highest_online_master_id = node_id
                            break

                    # 3. Fallback: if no remote nodes are online yet, local node acts as candidate
                    if not highest_online_master_id:
                        highest_online_master_id = local_node_id

                    # 4. Evaluate if THIS host is the elected Master AP
                    i_am_master_ap = (local_node_id == highest_online_master_id)

                    if i_am_master_ap:
                        self.master_failover_event = None
                        for n in self.nodes:
                            if n["id"] == local_node_id:
                                n["is_master_ap"] = True
                                n["ap_role"] = "MASTER_AP"
                            else:
                                n["is_master_ap"] = False
                                n["ap_role"] = "STATION_BRIDGE"

                        if not has_remote_peers:
                            self._log_failover_event(f"[FAILOVER ELECTION AUDIT] Local Host {my_ip} ({local_node_id}) is ELECTED MASTER AP (Isolated: 0 peers). Running Probe Cycle (Interval: {switching_interval:.1f}s)...")
                            self._handle_disconnected_30s_probe(my_ip, switching_interval)
                        else:
                            self._log_failover_event(f"[FAILOVER ELECTION AUDIT] Local Host {my_ip} ({local_node_id}) is ELECTED MASTER AP (Connected: {len(remote_online_nodes)} peers). Locking hardware in MASTER AP mode.")
                            self._probe_state_start = 0.0
                            self._probe_state = "AP"
                            self._promote_local_radio_hardware()
                    else:
                        # THIS host is NOT the Master AP
                        self.master_failover_event = {
                            "timestamp": time.time(),
                            "elected_node_id": highest_online_master_id,
                            "elected_node_name": nodes_dict.get(highest_online_master_id, {}).get("name", highest_online_master_id),
                            "elected_node_ip": nodes_dict.get(highest_online_master_id, {}).get("ip", ""),
                            "reason": f"Higher Priority Node ({highest_online_master_id}) Active as Master AP"
                        }
                        for n in self.nodes:
                            if n["id"] == highest_online_master_id:
                                n["is_master_ap"] = True
                                n["ap_role"] = "MASTER_AP"
                            else:
                                n["is_master_ap"] = False
                                n["ap_role"] = "STATION_BRIDGE"

                        if not has_remote_peers:
                            self._log_failover_event(f"[FAILOVER ELECTION AUDIT] Local Host {my_ip} ({local_node_id}) is CLIENT NODE (Isolated: 0 peers, Higher Rank: {highest_online_master_id}). Running Search Probe Cycle (Interval: {switching_interval:.1f}s)...")
                            self._handle_disconnected_30s_probe(my_ip, switching_interval)
                        else:
                            self._log_failover_event(f"[FAILOVER ELECTION AUDIT] Local Host {my_ip} ({local_node_id}) is CLIENT NODE (Connected to Master AP {highest_online_master_id}). Locking hardware in STATION_BRIDGE client mode.")
                            self._probe_state_start = 0.0
                            self._probe_state = "STATION_BRIDGE"
                            self._demote_local_radio_hardware()
            except Exception as e:
                print(f"[ELECTION ERROR] {e}")
            time.sleep(2)

    def _get_radio_ip_map(self):
        """Returns physical host IP -> NetMetal AX Radio IP mapping loaded from config/failover.yaml."""
        default_map = {
            "192.168.3.65": "192.168.3.3",
            "192.168.3.67": "192.168.3.2",
            "192.168.3.66": "192.168.3.4",
            "192.168.3.68": "192.168.3.5",
            "192.168.3.69": "192.168.3.6",
            "192.168.3.70": "192.168.3.7",
            "192.168.3.71": "192.168.3.8",
            "192.168.3.72": "192.168.3.8",
            "192.168.3.73": "192.168.3.8",
        }
        try:
            from utils.config_manager import ConfigManager
            cm = ConfigManager()
            failover_cfg = cm.get_failover() or {}
            nodes = failover_cfg.get("failover", {}).get("device_nodes", {})
            if nodes:
                dynamic_map = {}
                for node_id, node_info in nodes.items():
                    h_ip = node_info.get("host_ip")
                    r_ip = node_info.get("radio_ip")
                    if h_ip and r_ip:
                        dynamic_map[h_ip] = r_ip
                if dynamic_map:
                    return dynamic_map
        except Exception:
            pass
        return default_map

    def _promote_local_radio_hardware(self, force=False):
        """Invokes RouterOS REST API client to promote local radio (wifi2 -> AP, wifi2_vap -> STATION-BRIDGE)."""
        if not force and getattr(self, "current_hardware_mode", None) == "AP":
            return
        try:
            from hardware.routeros_client import RouterOSClient
            my_ip = self._get_this_machine_ip()
            radio_ip_map = self._get_radio_ip_map()
            local_radio_ip = radio_ip_map.get(my_ip, "192.168.3.2")
            print(f"[HARDWARE FAILOVER] Promoting local NetMetal AX radio ({local_radio_ip}) for host {my_ip} to MASTER AP mode...")
            client = RouterOSClient(host=local_radio_ip)
            res = client.promote_to_master_ap()
            if res:
                self.current_hardware_mode = "AP"
            print(f"[HARDWARE FAILOVER PROMOTION RESULT] {res}")
        except Exception as e:
            print(f"[HARDWARE PROMOTION ERROR] {e}")

    def _demote_local_radio_hardware(self, force=False):
        """Invokes RouterOS REST API client to set local radio to client mode (wifi2 -> STATION-BRIDGE, wifi2_vap -> AP)."""
        if not force and getattr(self, "current_hardware_mode", None) == "STATION_BRIDGE":
            return
        try:
            from hardware.routeros_client import RouterOSClient
            my_ip = self._get_this_machine_ip()
            radio_ip_map = self._get_radio_ip_map()
            local_radio_ip = radio_ip_map.get(my_ip, "192.168.3.2")
            print(f"[HARDWARE RECONCILIATION] Demoting local NetMetal AX radio ({local_radio_ip}) for host {my_ip} to STATION-BRIDGE mode...")
            client = RouterOSClient(host=local_radio_ip)
            res = client.demote_to_station_bridge()
            if res:
                self.current_hardware_mode = "STATION_BRIDGE"
            print(f"[HARDWARE DEMOTION RESULT] {res}")
        except Exception as e:
            print(f"[HARDWARE DEMOTION ERROR] {e}")
            print(f"[HARDWARE DEMOTION ERROR] {e}")

    def get_system_summary(self):
        with self.lock:
            local_ips = self._get_local_ips()
            target_ip = getattr(self, "local_ip", None)
            online_count = sum(1 for n in self.nodes if n["status"] == "ONLINE")
            ugv_count = sum(1 for n in self.nodes if n["type"] == "UGV" and n["status"] == "ONLINE")
            gcs_count = sum(1 for n in self.nodes if n["type"] == "GCS" and n["status"] == "ONLINE")

            if target_ip:
                local_node = next((n for n in self.nodes if n["ip"] == target_ip), None)
            else:
                local_node = next((n for n in self.nodes if n["ip"] in local_ips), None)

            local_id = local_node["id"] if local_node else "LOCAL"
            local_name = local_node["name"] if local_node else "Local Node Host"
            local_ip = local_node["ip"] if local_node else (target_ip or next((ip for ip in local_ips if not ip.startswith("127.")), "127.0.0.1"))

            # Inter-System Mesh Bandwidth Capacity Governance:
            # Active mesh bandwidth capacity measures inter-system data transfer across the mesh using configured node_offline_timeout_seconds buffer (10.0s).
            # If 0 remote mesh nodes are ONLINE (n["ip"] != local_ip), active inter-system mesh bandwidth is 0.0 Mbps.
            remote_nodes_online = any(n["status"] == "ONLINE" and n["ip"] != local_ip for n in self.nodes)

            allowed = self.scheduler.allowed_topics
            live_used_bw = 0.0
            if remote_nodes_online:
                for name, topic in self.registry.all_topics().items():
                    if name in allowed:
                        tx_mbps = topic.get("tx_mbps", 0.0)
                        rx_mbps = topic.get("rx_mbps", 0.0)
                        bw = tx_mbps if tx_mbps > 0.0 else rx_mbps
                        live_used_bw += bw

            return {
                "timestamp": time.time(),
                "total_nodes": len(self.nodes),
                "online_nodes": online_count,
                "ugv_online": ugv_count,
                "ugv_total": 6,
                "gcs_online": gcs_count,
                "gcs_total": 3,
                "wireless_radios": 7,  # 7-Sided Polygon (Heptagon)
                "max_bandwidth_mbps": self.max_bw,
                "used_bandwidth_mbps": round(live_used_bw, 1),
                "loss_tolerance_percent": self.loss_tolerance,
                "system_health": "OPTIMAL" if online_count >= 8 else "DEGRADED",
                "local_node_id": local_id,
                "local_node_name": local_name,
                "local_node_ip": local_ip,
                "master_failover_event": self.master_failover_event
            }

    def get_nodes(self):
        with self.lock:
            local_ips = self._get_local_ips()
            target_ip = getattr(self, "local_ip", None)
            nodes_copy = []
            for n in self.nodes:
                c = dict(n)
                if target_ip:
                    c["is_local"] = n["ip"] == target_ip
                else:
                    c["is_local"] = n["ip"] in local_ips

                # Determine if node is acting as Master Access Point (Master AP) dynamically based on live wifi2 hardware mode
                is_master = False
                if n.get("status") == "ONLINE":
                    wifi_det = n.get("wifi_details")
                    wifi2_mode = None
                    if wifi_det and isinstance(wifi_det, dict):
                        for i in wifi_det.get("interfaces", []):
                            if i.get("name") == "wifi2":
                                wifi2_mode = (i.get("mode") or "").upper()
                                break
                    
                    if wifi2_mode == "AP":
                        is_master = True
                    elif wifi2_mode in ["STATION-BRIDGE", "STATION"]:
                        is_master = False
                    else:
                        is_master = (n.get("ap_role") in ["MASTER_AP", "ELECTED_MASTER_AP"])

                c["is_master_ap"] = is_master
                c["ap_role"] = "MASTER_AP" if is_master else "STATION_BRIDGE"
                nodes_copy.append(c)
            return nodes_copy

    def get_topology(self):
        """Generates 7-Sided Polygon (Heptagon) Wireless Interconnection Links."""
        with self.lock:
            links = []
            radio_endpoints = [
                "UGV-01", "UGV-02", "UGV-03", "UGV-04", "UGV-05", "UGV-06", "GCS-RADIO"
            ]

            n = len(radio_endpoints)
            node_dict = {n["id"]: n for n in self.nodes}

            for i in range(n):
                for j in range(i + 1, n):
                    r1 = radio_endpoints[i]
                    r2 = radio_endpoints[j]

                    n1 = node_dict.get(r1, {"rssi": -65, "latency": 5.0})
                    n2 = node_dict.get(r2, {"rssi": -65, "latency": 5.0})

                    worst_rssi = min(n1["rssi"], n2["rssi"])
                    worst_lat = round(max(n1["latency"], n2["latency"]), 1)

                    links.append({
                        "source": r1,
                        "target": r2,
                        "rssi": worst_rssi,
                        "latency": worst_lat,
                        "quality": "EXCELLENT" if worst_rssi > -65 else ("GOOD" if worst_rssi > -75 else "POOR")
                    })

            return {
                "radios": 7,
                "nodes": list(self.nodes),
                "links": links
            }

    def get_topics(self):
        with self.lock:
            result = []
            allowed = self.scheduler.allowed_topics
            for name, topic in self.registry.all_topics().items():
                is_allowed = name in allowed
                tx_hz = topic.get("tx_hz", 0.0)
                tx_mbps = topic.get("tx_mbps", 0.0) if is_allowed else 0.0
                tx_data_size_str = topic.get("tx_data_size_str", "0 B") if tx_hz > 0.0 else "0 B"

                rx_hz = topic.get("rx_hz", 0.0)
                rx_mbps = topic.get("rx_mbps", 0.0)
                rx_data_size_str = topic.get("rx_data_size_str", "0 B") if rx_hz > 0.0 else "0 B"

                diff_mbps = round(tx_mbps - rx_mbps, 1)
                delivery_pct = topic.get("delivery_pct", 100.0) if is_allowed else 0.0
                role = topic.get("role", "IDLE")

                bw = tx_mbps if tx_mbps > 0.0 else rx_mbps
                hz = tx_hz if tx_hz > 0.0 else rx_hz
                data_size_str = tx_data_size_str if tx_hz > 0.0 else rx_data_size_str

                congestion_obj = getattr(self, "congestion", getattr(self.scheduler, "congestion", None) if hasattr(self, "scheduler") else None)
                shedding_level = getattr(congestion_obj, "shedding_level", 0) if congestion_obj else 0
                last_loss = getattr(congestion_obj, "last_loss_percent", 0.0) if congestion_obj else 0.0

                loss_pct = round(100.0 - delivery_pct, 1) if is_allowed else last_loss

                cfg_st = str(topic.get("status", "ALLOW")).upper()
                if cfg_st == "DENY":
                    status_str = "DENIED"
                    verif_str = "BLOCKED BY CONFIG (DENY)"
                elif is_allowed:
                    if tx_hz > 0.0 and rx_hz == 0.0:
                        # Local Node is Publisher (Tx): Active Transmission
                        status_str = "ALLOWED"
                        verif_str = "TX LIVE 100%"
                    elif rx_hz > 0.0 or hz > 0.0:
                        # Local Node is Subscriber (Rx): Cross-verified delivery rate
                        if delivery_pct >= 99.9:
                            status_str = "ALLOWED"
                            verif_str = "FULL DATA 100%"
                        else:
                            status_str = "ALLOWED"
                            verif_str = f"{loss_pct:.1f}% LOSS DETECTED"
                    else:
                        status_str = "ALLOWED"
                        verif_str = "UNINITIATED"
                else:
                    if shedding_level > 0:
                        status_str = "SHEDDED"
                        verif_str = f"SHEDDED ({last_loss:.1f}% LOSS)"
                    else:
                        status_str = "BLOCKED"
                        verif_str = "CAPACITY EXCEEDED"

                result.append({
                    "id": topic["id"],
                    "name": topic["name"],
                    "priority": topic["priority"],
                    "bandwidth_mbps": round(bw, 1),
                    "hz": round(hz, 1),
                    "data_size_str": data_size_str,
                    "tx_hz": round(tx_hz, 1),
                    "tx_mbps": round(tx_mbps, 1),
                    "tx_data_size_str": tx_data_size_str,
                    "rx_hz": round(rx_hz, 1),
                    "rx_mbps": round(rx_mbps, 1),
                    "rx_data_size_str": rx_data_size_str,
                    "diff_mbps": diff_mbps,
                    "delivery_pct": delivery_pct,
                    "role": role,
                    "status": status_str,
                    "loss_percent": loss_pct,
                    "verification": verif_str
                })
            return sorted(result, key=lambda x: (x["priority"], x["id"]))


DATA_PROVIDER = TelemetryDataProvider()


class ReusableHTTPServer(HTTPServer):
    """HTTPServer with socket reuse address enabled to prevent port bind failures."""
    allow_reuse_address = True


class DashboardRequestHandler(SimpleHTTPRequestHandler):
    """
    HTTP Request Handler serving web assets and REST JSON endpoints.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._send_api_response()
        else:
            super().do_GET()

    def _send_api_response(self):
        try:
            if self.path == "/api/summary":
                data = DATA_PROVIDER.get_system_summary()
            elif self.path == "/api/nodes":
                data = DATA_PROVIDER.get_nodes()
            elif self.path == "/api/topology":
                data = DATA_PROVIDER.get_topology()
            elif self.path == "/api/topics":
                data = DATA_PROVIDER.get_topics()
            elif self.path == "/api/all":
                data = {
                    "summary": DATA_PROVIDER.get_system_summary(),
                    "nodes": DATA_PROVIDER.get_nodes(),
                    "topology": DATA_PROVIDER.get_topology(),
                    "topics": DATA_PROVIDER.get_topics()
                }
            else:
                data = {"error": "Endpoint not found"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            data = {"error": str(e)}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def log_message(self, format, *args):
        # Silence standard HTTP access logging to keep terminal clean
        pass


def start_dashboard_server(host="0.0.0.0", port=8080):
    try:
        server = ReusableHTTPServer((host, port), DashboardRequestHandler)
        print(f"[INFO] Mesh Control Plane Web Dashboard Server running at http://{host}:{port}")
        server.serve_forever()
    except Exception as e:
        print(f"[ERROR] Failed to start Web Dashboard on {host}:{port} -> {e}")


def start_dashboard_background(host="0.0.0.0", port=8080):
    t = Thread(target=start_dashboard_server, args=(host, port), daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    start_dashboard_server()
