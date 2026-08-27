#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Test Suite: Priority Scheduler & Topic Admission Logger Test

Verifies that SchedulerLogger accurately records formatted text snapshots and
CSV logs containing Rate (Hz), Msg Size, Live Bandwidth (Mbps), and Admission Status.

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
            self.assertIn("/camera/camera/depth/image_rect_raw", txt_content)

        # Verify CSV log creation
        csv_path = os.path.join(self.test_dir, "priority_scheduler.csv")
        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_lines = f.readlines()
            self.assertGreaterEqual(len(csv_lines), 2)
            self.assertIn("Timestamp,Topic_ID,Topic_Name", csv_lines[0])
            matched_allowed = any("ALLOWED" in line for line in csv_lines)
            self.assertTrue(matched_allowed, "No ALLOWED topic found in CSV log!")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
