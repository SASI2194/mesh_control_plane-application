#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Real-Time Dynamic Bandwidth & Dual Publisher/Subscriber Role Metrics Monitor

Measures incoming (Rx - Subscriber) and outgoing (Tx - Publisher) ROS topic bandwidth,
packet rates (Hz), message payload sizes, and calculates end-to-end differential throughput
in real-time using a 2.0-second sliding time window.

===============================================================================
"""

import time
from collections import deque
from threading import Lock


def format_bytes(num_bytes):
    """Formats bytes into human readable B, KB, MB strings."""
    if num_bytes < 1024:
        return f"{num_bytes:.0f} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024.0:.1f} KB"
    else:
        return f"{num_bytes / (1024.0 * 1024.0):.2f} MB"


class TopicWindowStats:
    """
    Tracks sliding window statistics for a single topic (Publisher Tx or Subscriber Rx).
    """

    def __init__(self, window_size_sec=2.0):
        self.window_size_sec = window_size_sec
        self.samples = deque()  # (timestamp, byte_size, seq_num)
        self.sequence_number = 0
        self.last_update_time = time.time()
        self.lock = Lock()

    def add_sample(self, byte_size, seq_num=None):
        with self.lock:
            now = time.time()
            if seq_num is not None:
                if getattr(self, "last_seq", None) is not None:
                    if seq_num > self.last_seq + 1:
                        gap = seq_num - (self.last_seq + 1)
                        self.total_gaps = getattr(self, "total_gaps", 0) + gap
                    self.total_expected = getattr(self, "total_expected", 0) + max(1, seq_num - self.last_seq)
                else:
                    self.total_gaps = 0
                    self.total_expected = 1
                self.last_seq = seq_num
            else:
                self.sequence_number += 1

            self.samples.append((now, byte_size, seq_num if seq_num is not None else self.sequence_number))
            self.last_update_time = now
            self._clean_old_samples(now)
            return seq_num if seq_num is not None else self.sequence_number

    def _clean_old_samples(self, current_time):
        cutoff = current_time - self.window_size_sec
        while self.samples and self.samples[0][0] < cutoff:
            self.samples.popleft()

    def get_metrics(self):
        """
        Returns a dict containing live Mbps, Hz (pps), avg message size in bytes, and formatted string.
        """
        with self.lock:
            now = time.time()
            self._clean_old_samples(now)

            if not self.samples:
                return {
                    "mbps": 0.0,
                    "hz": 0.0,
                    "avg_bytes": 0.0,
                    "data_size_str": "0 B"
                }

            total_bytes = sum(s[1] for s in self.samples)
            count = len(self.samples)

            mbps = (total_bytes * 8.0) / (self.window_size_sec * 1e6)
            hz = count / self.window_size_sec
            avg_bytes = total_bytes / count if count > 0 else 0.0

            return {
                "mbps": round(mbps, 1),
                "hz": round(hz, 1),
                "avg_bytes": round(avg_bytes, 1),
                "data_size_str": format_bytes(avg_bytes)
            }


class RealtimeBandwidthMonitor:
    """
    Monitors real-time Tx (Publisher) and Rx (Subscriber) bandwidth, frequency (Hz),
    payload data sizes, and differential throughput across all active ROS topics.
    """

    def __init__(self, window_size_sec=2.0):
        self.window_size_sec = window_size_sec
        self.tx_stats = {}  # topic_name -> TopicWindowStats (Publisher Tx)
        self.rx_stats = {}  # topic_name -> TopicWindowStats (Subscriber Rx)
        self.lock = Lock()

    def record_sample(self, topic_name, byte_size):
        """Backward compatible helper - records Tx sample."""
        return self.record_tx_sample(topic_name, byte_size)

    def record_tx_sample(self, topic_name, byte_size):
        """Record Publisher (Tx) generated ROS sample before entering transport."""
        if not topic_name:
            return 0
        with self.lock:
            if topic_name not in self.tx_stats:
                self.tx_stats[topic_name] = TopicWindowStats(self.window_size_sec)
            stats = self.tx_stats[topic_name]
        return stats.add_sample(byte_size)

    def record_rx_sample(self, topic_name, byte_size, seq_num=None):
        """Record Subscriber (Rx) received mesh sample that entered through transport."""
        if not topic_name:
            return 0
        with self.lock:
            if topic_name not in self.rx_stats:
                self.rx_stats[topic_name] = TopicWindowStats(self.window_size_sec)
            stats = self.rx_stats[topic_name]
        return stats.add_sample(byte_size, seq_num)

    def get_topic_metrics(self, topic_name):
        """
        Get the current Publisher (Tx), Subscriber (Rx), and Differential metrics for a topic.
        """
        with self.lock:
            tx_obj = self.tx_stats.get(topic_name)
            rx_obj = self.rx_stats.get(topic_name)

        tx_m = tx_obj.get_metrics() if tx_obj else {"mbps": 0.0, "hz": 0.0, "avg_bytes": 0.0, "data_size_str": "0 B"}
        rx_m = rx_obj.get_metrics() if rx_obj else {"mbps": 0.0, "hz": 0.0, "avg_bytes": 0.0, "data_size_str": "0 B"}

        tx_mbps = tx_m["mbps"]
        rx_mbps = rx_m["mbps"]
        diff_mbps = round(tx_mbps - rx_mbps, 1)

        # Role determination
        if tx_m["hz"] > 0.0 and rx_m["hz"] > 0.0:
            role = "BOTH"
        elif tx_m["hz"] > 0.0:
            role = "PUBLISHER"
        elif rx_m["hz"] > 0.0:
            role = "SUBSCRIBER"
        else:
            role = "IDLE"

        # Delivery percentage
        if tx_mbps > 0.0:
            delivery_pct = round(min(100.0, (rx_mbps / tx_mbps) * 100.0), 1)
        elif rx_obj and getattr(rx_obj, "total_expected", 0) > 0:
            gaps = getattr(rx_obj, "total_gaps", 0)
            exp = rx_obj.total_expected
            delivery_pct = round(max(0.0, min(100.0, ((exp - gaps) / float(exp)) * 100.0)), 1)
        else:
            delivery_pct = 100.0

        # General fallbacks
        primary_mbps = tx_mbps if tx_mbps > 0.0 else rx_mbps
        primary_hz = tx_m["hz"] if tx_m["hz"] > 0.0 else rx_m["hz"]
        primary_data_str = tx_m["data_size_str"] if tx_m["hz"] > 0.0 else rx_m["data_size_str"]

        return {
            "mbps": primary_mbps,
            "hz": primary_hz,
            "avg_bytes": tx_m["avg_bytes"] if tx_m["hz"] > 0.0 else rx_m["avg_bytes"],
            "data_size_str": primary_data_str,
            # Publisher Tx metrics
            "tx_mbps": tx_mbps,
            "tx_hz": tx_m["hz"],
            "tx_data_size_str": tx_m["data_size_str"],
            # Subscriber Rx metrics
            "rx_mbps": rx_mbps,
            "rx_hz": rx_m["hz"],
            "rx_data_size_str": rx_m["data_size_str"],
            # Differential & Role metrics
            "diff_mbps": diff_mbps,
            "delivery_pct": delivery_pct,
            "role": role
        }

    def get_all_bandwidths(self):
        with self.lock:
            all_keys = set(self.tx_stats.keys()).union(set(self.rx_stats.keys()))

        result = {}
        for topic in all_keys:
            metrics = self.get_topic_metrics(topic)
            result[topic] = metrics["mbps"]
        return result

    def get_all_metrics(self):
        with self.lock:
            all_keys = set(self.tx_stats.keys()).union(set(self.rx_stats.keys()))

        result = {}
        for topic in all_keys:
            result[topic] = self.get_topic_metrics(topic)
        return result

    def record_peer_loss(self, peer_ip, loss_pct):
        """Records peer loss feedback received over control plane heartbeat."""
        with self.lock:
            if not hasattr(self, "peer_losses"):
                self.peer_losses = {}
            self.peer_losses[peer_ip] = (time.time(), float(loss_pct))

    def get_max_loss_percent(self):
        """Calculates maximum loss percentage across active local topics and fresh peer feedback."""
        with self.lock:
            all_keys = set(self.tx_stats.keys()).union(set(self.rx_stats.keys()))

        max_local_loss = 0.0
        for topic in all_keys:
            m = self.get_topic_metrics(topic)
            # Only evaluate packet loss for topics with active traffic
            if m.get("tx_hz", 0.0) > 0.0 or m.get("rx_hz", 0.0) > 0.0:
                del_pct = m.get("delivery_pct", 100.0)
                if del_pct < 100.0:
                    loss = 100.0 - del_pct
                    if loss > max_local_loss:
                        max_local_loss = loss

        max_peer_loss = 0.0
        now = time.time()
        with self.lock:
            if hasattr(self, "peer_losses"):
                for ip, (ts, loss) in list(self.peer_losses.items()):
                    # Ignore stale peer loss older than 2.5 seconds
                    if (now - ts) <= 2.5:
                        if loss > max_peer_loss:
                            max_peer_loss = loss

        return round(max(max_local_loss, max_peer_loss), 1)
