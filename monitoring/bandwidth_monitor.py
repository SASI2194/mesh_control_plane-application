#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Real-Time Dynamic Bandwidth & Topic Metrics Monitor

Measures incoming ROS topic bandwidth, packet rates (Hz), and message data sizes
in real-time using a sliding time window.

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
    Tracks sliding window statistics for a single topic.
    """

    def __init__(self, window_size_sec=1.0):
        self.window_size_sec = window_size_sec
        self.samples = deque()  # (timestamp, byte_size, seq_num)
        self.sequence_number = 0
        self.last_update_time = time.time()
        self.lock = Lock()

    def add_sample(self, byte_size):
        with self.lock:
            now = time.time()
            self.sequence_number += 1
            self.samples.append((now, byte_size, self.sequence_number))
            self.last_update_time = now
            self._clean_old_samples(now)
            return self.sequence_number

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
                "mbps": round(mbps, 2),
                "hz": round(hz, 1),
                "avg_bytes": round(avg_bytes, 1),
                "data_size_str": format_bytes(avg_bytes)
            }


class RealtimeBandwidthMonitor:
    """
    Monitors real-time bandwidth, frequency (Hz), and payload data sizes across all active ROS topics.
    """

    def __init__(self, window_size_sec=1.0):
        self.window_size_sec = window_size_sec
        self.topic_stats = {}
        self.lock = Lock()

    def record_sample(self, topic_name, byte_size):
        """
        Record a received message for a topic and return its sequence number.
        """
        with self.lock:
            if topic_name not in self.topic_stats:
                self.topic_stats[topic_name] = TopicWindowStats(self.window_size_sec)
            stats = self.topic_stats[topic_name]

        return stats.add_sample(byte_size)

    def get_topic_metrics(self, topic_name):
        """
        Get the current measured metrics for a topic.
        """
        with self.lock:
            stats = self.topic_stats.get(topic_name)
            if stats:
                return stats.get_metrics()
            return {
                "mbps": 0.0,
                "hz": 0.0,
                "avg_bytes": 0.0,
                "data_size_str": "0 B"
            }

    def get_all_bandwidths(self):
        """
        Get a dict mapping topic_name -> measured Mbps.
        """
        with self.lock:
            topics = list(self.topic_stats.keys())

        result = {}
        for topic in topics:
            metrics = self.get_topic_metrics(topic)
            result[topic] = metrics["mbps"]
        return result

    def get_all_metrics(self):
        """
        Get a dict mapping topic_name -> full metrics dict (mbps, hz, avg_bytes, data_size_str).
        """
        with self.lock:
            topics = list(self.topic_stats.keys())

        result = {}
        for topic in topics:
            result[topic] = self.get_topic_metrics(topic)
        return result
