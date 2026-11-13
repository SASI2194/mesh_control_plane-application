#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Test Suite: Priority Scheduler & Topic Admission Logger Test

Verifies that SchedulerLogger accurately records formatted text snapshots and
CSV logs containing Rate (Hz), Msg Size, Live Bandwidth (Mbps), Admission Status,
and multi-device child stream telemetry.

===============================================================================
"""

import os
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ros.topic_database import TopicRegistry
from scheduler.bandwidth_scheduler import BandwidthScheduler
from utils.scheduler_logger import SchedulerLogger


class TestSchedulerLogger(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.logger = SchedulerLogger(log_dir=self.test_dir)
        self.registry = TopicRegistry()
        self.scheduler = BandwidthScheduler(self.registry)
        self.scheduler.available_bandwidth = 600.0
        self.scheduler.schedule()

    def test_log_snapshot_creation(self):
        # Update metrics with test data
        metrics = {
            "/camera/camera/color/camera_info": {"mbps": 40.0, "hz": 50.0, "data_size_str": "100.0 KB"},
            "/camera/camera/color/image_raw": {"mbps": 60.0, "hz": 30.0, "data_size_str": "250.0 KB"},
        }
        self.registry.update_measured_metrics(metrics)

        # Log snapshot
        self.logger.log_snapshot(self.registry, self.scheduler)

        # Verify text log creation
        txt_path = os.path.join(self.test_dir, "priority_scheduler.log")
        self.assertTrue(os.path.exists(txt_path))
        with open(txt_path, "r", encoding="utf-8") as f:
            txt_content = f.read()
            self.assertIn("PRIORITY SCHEDULER & DUAL Tx/Rx DIFFERENTIAL SNAPSHOT", txt_content)
            self.assertIn("/camera/color/image_raw", txt_content)

        # Verify CSV log creation
        csv_path = os.path.join(self.test_dir, "priority_scheduler.csv")
        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_lines = f.readlines()
            self.assertGreaterEqual(len(csv_lines), 2)
            self.assertIn("Timestamp,Topic_ID,Topic_Name", csv_lines[0])
            matched_allowed = any("ALLOWED" in line for line in csv_lines)
            self.assertTrue(matched_allowed, "No ALLOWED topic found in CSV log!")

    def test_multi_device_stream_logging(self):
        # Test stream logging with multi-robot telemetry
        stream_metrics = {
            "/ugv_02/lidar_point_cloud": {
                "role": "SUBSCRIBER",
                "tx_hz": 0.0,
                "tx_mbps": 0.0,
                "tx_data_size_str": "0 B",
                "rx_hz": 20.0,
                "rx_mbps": 150.0,
                "rx_data_size_str": "936.0 KB",
                "diff_mbps": -150.0,
                "delivery_pct": 98.5
            },
            "/ugv_01/compressed/lidar_point_cloud": {
                "role": "PUBLISHER",
                "tx_hz": 15.0,
                "tx_mbps": 25.0,
                "tx_data_size_str": "200.0 KB",
                "rx_hz": 0.0,
                "rx_mbps": 0.0,
                "rx_data_size_str": "0 B",
                "diff_mbps": 25.0,
                "delivery_pct": 100.0
            }
        }
        self.registry.update_measured_metrics(stream_metrics)
        self.logger.log_snapshot(self.registry, self.scheduler)

        # 1. Verify priority_scheduler.log records stream lines
        txt_path = os.path.join(self.test_dir, "priority_scheduler.log")
        with open(txt_path, "r", encoding="utf-8") as f:
            txt_content = f.read()
            self.assertIn("[UGV-02] /ugv_02/lidar_point_cloud", txt_content)
            self.assertIn("SUBSCRIBER", txt_content)
            self.assertIn("150.0 Mbps", txt_content)

        # 2. Verify priority_scheduler.csv records stream child rows
        csv_path = os.path.join(self.test_dir, "priority_scheduler.csv")
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_lines = f.readlines()
            ugv02_stream = any("↳ [UGV-02] /ugv_02/lidar_point_cloud" in line for line in csv_lines)
            self.assertTrue(ugv02_stream, "Child stream /ugv_02/lidar_point_cloud not found in priority_scheduler.csv!")

        # 3. Verify dedicated active_streams.csv
        streams_csv_path = os.path.join(self.test_dir, "active_streams.csv")
        self.assertTrue(os.path.exists(streams_csv_path))
        with open(streams_csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertGreaterEqual(len(lines), 2)
            self.assertTrue(any("UGV-02" in l and "/ugv_02/lidar_point_cloud" in l for l in lines))

        # 4. Verify dedicated active_streams.log
        streams_txt_path = os.path.join(self.test_dir, "active_streams.log")
        self.assertTrue(os.path.exists(streams_txt_path))
        with open(streams_txt_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("UGV-02", content)
            self.assertIn("/ugv_02/lidar_point_cloud", content)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
