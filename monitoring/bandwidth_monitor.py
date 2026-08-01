#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Real-Time Dynamic Bandwidth Monitor

Measures incoming ROS topic bandwidth and packet rates in real-time
using a sliding time window.

===============================================================================
"""

import time
from collections import deque
from threading import Lock


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

    def get_bandwidth_mbps(self):
        with self.lock:
            now = time.time()
            self._clean_old_samples(now)
            if not self.samples:
                return 0.0
            total_bytes = sum(s[1] for s in self.samples)
            # Mbps = (bytes * 8) / 1,000,000 over window_size_sec
            return (total_bytes * 8.0) / (self.window_size_sec * 1e6)

    def get_packet_rate(self):
        with self.lock:
            now = time.time()
            self._clean_old_samples(now)
            if not self.samples:
                return 0.0
            return len(self.samples) / self.window_size_sec


class RealtimeBandwidthMonitor:
    """
    Monitors real-time bandwidth across all active ROS topics.
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

    def get_topic_bandwidth(self, topic_name):
        """
        Get the current measured Mbps for a topic.
        """
        with self.lock:
            stats = self.topic_stats.get(topic_name)
            if stats:
                return stats.get_bandwidth_mbps()
            return 0.0

    def get_all_bandwidths(self):
        """
        Get a dict mapping topic_name -> measured Mbps.
        """
        with self.lock:
            topics = list(self.topic_stats.keys())

        result = {}
        for topic in topics:
            result[topic] = self.get_topic_bandwidth(topic)
        return result
