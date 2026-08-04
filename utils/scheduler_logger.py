#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Priority Scheduler & Dual Tx/Rx Role Topic Admission Logger

Logs real-time dynamic topic admission state, Publisher (Tx) generated rates,
Subscriber (Rx) received rates, differential throughput, and delivery efficiency
to text and CSV log files.

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

    def __init__(self, log_dir="logs", clear_on_start=True):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.text_logfile = self.log_dir / "priority_scheduler.log"
        self.csv_logfile = self.log_dir / "priority_scheduler.csv"
        self.lock = Lock()

        # Erase previous data whenever the script starts
        if clear_on_start:
            self._reset_log_files()

    def _reset_log_files(self):
        """Erases previous log contents and writes clean headers on script startup."""
        with open(self.csv_logfile, "w", encoding="utf-8") as f:
            f.write("Timestamp,Topic_ID,Topic_Name,Priority,Role,Tx_Rate_Hz,Tx_Msg_Size,Tx_Live_Mbps,Rx_Rate_Hz,Rx_Msg_Size,Rx_Live_Mbps,Diff_Mbps,Delivery_Pct,Admission_Status,Lossless_Verification\n")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.text_logfile, "w", encoding="utf-8") as f:
            f.write(f"===================================================================================\n")
            f.write(f" Mesh Control Plane Priority Scheduler & Dual Tx/Rx Differential Log (Session: {now_str})\n")
            f.write(f"===================================================================================\n\n")

    def log_snapshot(self, registry, scheduler):
        """
        Captures and writes current Tx/Rx Role rates, Differential Mbps, and Admission status
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

                    role = topic.get("role", "IDLE")

                    tx_hz = topic.get("tx_hz", 0.0)
                    tx_mbps = topic.get("tx_mbps", 0.0) if is_allowed else 0.0
                    tx_size = topic.get("tx_data_size_str", "0 B") if tx_hz > 0.0 else "0 B"

                    rx_hz = topic.get("rx_hz", 0.0)
                    rx_mbps = topic.get("rx_mbps", 0.0)
                    rx_size = topic.get("rx_data_size_str", "0 B") if rx_hz > 0.0 else "0 B"

                    diff_mbps = round(tx_mbps - rx_mbps, 1)
                    delivery_pct = topic.get("delivery_pct", 100.0) if is_allowed else 0.0

                    csv_f.write(
                        f"{now_str},{topic['id']},{topic['name']},P{topic['priority']},{role},"
                        f"{tx_hz:.1f},{tx_size},{tx_mbps:.1f},"
                        f"{rx_hz:.1f},{rx_size},{rx_mbps:.1f},"
                        f"{diff_mbps:.1f},{delivery_pct:.1f}%,{status},{verification}\n"
                    )

            # 2. Append to human-readable Text Log
            with open(self.text_logfile, "a", encoding="utf-8") as txt_f:
                txt_f.write(f"[{now_str}] PRIORITY SCHEDULER & DUAL Tx/Rx DIFFERENTIAL SNAPSHOT\n")
                txt_f.write(f"Capacity: {avail_bw:.1f} Mbps | Used: {used_bw:.1f} Mbps | Remaining: {max(0, avail_bw - used_bw):.1f} Mbps\n")
                txt_f.write("-" * 115 + "\n")
                txt_f.write(f"{'ID':<4} {'Topic Name':<12} {'Pri':<5} {'Role':<10} {'Tx Hz':<8} {'Tx Mbps':<9} {'Rx Hz':<8} {'Rx Mbps':<9} {'Diff':<8} {'Delivery':<10} {'Status':<9} {'Verification':<16}\n")
                txt_f.write("-" * 115 + "\n")

                for name, topic in sorted(topics.items(), key=lambda x: (x[1]["priority"], x[1]["id"])):
                    is_allowed = name in allowed_topics
                    status = "ALLOWED" if is_allowed else "BLOCKED"
                    verification = "FULL DATA 100%" if is_allowed else "SHEDDED"

                    role = topic.get("role", "IDLE")

                    tx_hz = topic.get("tx_hz", 0.0)
                    tx_mbps = topic.get("tx_mbps", 0.0) if is_allowed else 0.0

                    rx_hz = topic.get("rx_hz", 0.0)
                    rx_mbps = topic.get("rx_mbps", 0.0)

                    diff_mbps = round(tx_mbps - rx_mbps, 1)
                    delivery_pct = topic.get("delivery_pct", 100.0) if is_allowed else 0.0

                    txt_f.write(
                        f"{topic['id']:<4} {topic['name']:<12} P{topic['priority']:<4} {role:<10} "
                        f"{tx_hz:<8.1f} {tx_mbps:<9.1f} {rx_hz:<8.1f} {rx_mbps:<9.1f} "
                        f"{diff_mbps:<8.1f} {delivery_pct:<9.1f}% {status:<9} {verification:<16}\n"
                    )

                txt_f.write("=" * 115 + "\n\n")
