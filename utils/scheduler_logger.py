#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Priority Scheduler & Topic Admission Logger

Logs real-time dynamic topic admission state, publication frequency (Hz),
message payload sizes, and bandwidth allocation to text and CSV log files.

Output Log Files:
    • logs/priority_scheduler.log (Human-Readable Formatted Text Log)
    • logs/priority_scheduler.csv (Structured CSV Data Log)

===============================================================================
"""

import os
import time
from datetime import datetime
from pathlib import Path
from threading import Lock


class SchedulerLogger:

    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.text_logfile = self.log_dir / "priority_scheduler.log"
        self.csv_logfile = self.log_dir / "priority_scheduler.csv"
        self.lock = Lock()

        # Initialize CSV header if file doesn't exist or is empty
        if not self.csv_logfile.exists() or self.csv_logfile.stat().st_size == 0:
            with open(self.csv_logfile, "w", encoding="utf-8") as f:
                f.write("Timestamp,Topic_ID,Topic_Name,Priority,Rate_Hz,Msg_Size,Live_Mbps,Admission_Status,Lossless_Verification\n")

    def log_snapshot(self, registry, scheduler):
        """
        Captures and writes the current Priority Scheduler & Topic Admission snapshot
        to both logs/priority_scheduler.log and logs/priority_scheduler.csv.
        """
        with self.lock:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            topics = registry.all_topics()
            allowed_topics = scheduler.allowed_topics

            used_bw = scheduler.used_bandwidth
            avail_bw = scheduler.available_bandwidth

            # 1. Append to structured CSV Log
            with open(self.csv_logfile, "a", encoding="utf-8") as csv_f:
                for name, topic in sorted(topics.items(), key=lambda x: (x[1]["priority"], x[1]["id"])):
                    is_allowed = name in allowed_topics
                    status = "ALLOWED" if is_allowed else "BLOCKED"
                    verification = "FULL DATA 100%" if is_allowed else "SHEDDED"

                    bw = topic.get("measured_bandwidth", topic.get("bandwidth", 0.0))
                    hz = topic.get("hz", 0.0)
                    msg_size = topic.get("data_size_str", "0 B")

                    csv_f.write(
                        f"{now_str},{topic['id']},{topic['name']},P{topic['priority']},"
                        f"{hz:.1f},{msg_size},{bw:.1f},{status},{verification}\n"
                    )

            # 2. Append to human-readable Text Log
            with open(self.text_logfile, "a", encoding="utf-8") as txt_f:
                txt_f.write(f"[{now_str}] PRIORITY SCHEDULER & REAL-TIME TOPIC ADMISSION SNAPSHOT\n")
                txt_f.write(f"Capacity: {avail_bw:.1f} Mbps | Used: {used_bw:.1f} Mbps | Remaining: {max(0, avail_bw - used_bw):.1f} Mbps\n")
                txt_f.write("-" * 95 + "\n")
                txt_f.write(f"{'ID':<4} {'Topic Name':<14} {'Priority':<10} {'Rate (Hz)':<12} {'Msg Size':<12} {'Live Mbps':<12} {'Status':<10} {'Verification':<18}\n")
                txt_f.write("-" * 95 + "\n")

                for name, topic in sorted(topics.items(), key=lambda x: (x[1]["priority"], x[1]["id"])):
                    is_allowed = name in allowed_topics
                    status = "ALLOWED" if is_allowed else "BLOCKED"
                    verification = "FULL DATA 100%" if is_allowed else "SHEDDED"

                    bw = topic.get("measured_bandwidth", topic.get("bandwidth", 0.0))
                    hz = topic.get("hz", 0.0)
                    msg_size = topic.get("data_size_str", "0 B")

                    txt_f.write(
                        f"{topic['id']:<4} {topic['name']:<14} P{topic['priority']:<9} "
                        f"{hz:<12.1f} {msg_size:<12} {bw:<12.1f} {status:<10} {verification:<18}\n"
                    )

                txt_f.write("=" * 95 + "\n\n")
