#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Priority Scheduler & Dual Tx/Rx Role Topic Admission Logger

Logs real-time dynamic topic admission state, Publisher (Tx) generated rates,
Subscriber (Rx) received rates, differential throughput, delivery efficiency,
and hierarchical multi-device stream telemetry to text and CSV log files.

Output Log Files:
    • logs/priority_scheduler.log (Human-Readable Formatted Text Log with Stream Hierarchy)
    • logs/priority_scheduler.csv (Structured CSV Data Log including Parent Topics and Child Streams)
    • logs/active_streams.log     (Dedicated Real-Time Multi-Device Streams Text Log)
    • logs/active_streams.csv     (Dedicated Multi-Device Streams CSV Log)

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
        self.streams_text_logfile = self.log_dir / "active_streams.log"
        self.streams_csv_logfile = self.log_dir / "active_streams.csv"
        self.lock = Lock()

        # Erase previous data whenever the script starts
        if clear_on_start:
            self._reset_log_files()

    def _reset_log_files(self):
        """Erases previous log contents and writes clean headers on script startup."""
        with open(self.csv_logfile, "w", encoding="utf-8") as f:
            f.write("Timestamp,Topic_ID,Topic_Name,Priority,Role,Tx_Rate_Hz,Tx_Msg_Size,Publisher_Tx_Mbps,Rx_Rate_Hz,Rx_Msg_Size,Subscriber_Rx_Mbps,Diff_Mbps,Delivery_Pct,Admission_Status,Lossless_Verification\n")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.text_logfile, "w", encoding="utf-8") as f:
            f.write(f"===================================================================================================\n")
            f.write(f" Mesh Control Plane Priority Scheduler Log — Publisher Transmitted (Tx) & Subscriber Received (Rx)\n")
            f.write(f" Session Started: {now_str}\n")
            f.write(f"===================================================================================================\n\n")

        with open(self.streams_csv_logfile, "w", encoding="utf-8") as f:
            f.write("Timestamp,Topic_ID,Device,Stream_Key,Canonical_Topic,Priority,Role,Tx_Rate_Hz,Tx_Msg_Size,Publisher_Tx_Mbps,Rx_Rate_Hz,Rx_Msg_Size,Subscriber_Rx_Mbps,Diff_Mbps,Delivery_Pct,Admission_Status,Lossless_Verification\n")

        with open(self.streams_text_logfile, "w", encoding="utf-8") as f:
            f.write(f"===================================================================================================\n")
            f.write(f" Mesh Control Plane Active Streams Telemetry Log — Multi-Device Tx / Rx Streams Breakdown\n")
            f.write(f" Session Started: {now_str}\n")
            f.write(f"===================================================================================================\n\n")

    def log_snapshot(self, registry, scheduler, congestion_controller=None):
        """
        Captures and writes current Publisher (Tx) transmitted rates, Subscriber (Rx) received rates,
        Differential Mbps, Delivery efficiency, and Rule 3 cross-verified Lossless Verification status
        for both canonical topics and active child streams to logs/priority_scheduler.csv,
        logs/priority_scheduler.log, logs/active_streams.csv, and logs/active_streams.log.
        """
        with self.lock:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            topics = registry.all_topics()
            allowed_topics = scheduler.allowed_topics

            used_bw = scheduler.used_bandwidth
            avail_bw = scheduler.available_bandwidth

            congestion_obj = congestion_controller or getattr(scheduler, "congestion", None)
            shedding_level = getattr(congestion_obj, "shedding_level", 0) if congestion_obj else 0
            last_loss = getattr(congestion_obj, "last_loss_percent", 0.0) if congestion_obj else 0.0

            total_tx_mbps = 0.0
            total_rx_mbps = 0.0

            # Pre-calculate totals across all topics
            for name, topic in topics.items():
                tx_m = topic.get("tx_mbps", 0.0)
                rx_m = topic.get("rx_mbps", 0.0)
                total_tx_mbps += tx_m
                total_rx_mbps += rx_m

            total_diff_mbps = round(total_tx_mbps - total_rx_mbps, 1)

            # 1. Append to structured CSV Log (Parent topics + child stream hierarchy)
            with open(self.csv_logfile, "a", encoding="utf-8") as csv_f:
                for name, topic in sorted(topics.items(), key=lambda x: (x[1]["priority"], x[1]["id"])):
                    is_allowed = name in allowed_topics or str(topic.get("status", "")).upper() in ["ALLOW", "ALLOWED"]
                    role = topic.get("role", "IDLE")

                    tx_hz = topic.get("tx_hz", 0.0)
                    tx_mbps = topic.get("tx_mbps", 0.0)
                    tx_size = topic.get("tx_data_size_str", "0 B") if tx_hz > 0.0 else "0 B"

                    rx_hz = topic.get("rx_hz", 0.0)
                    rx_mbps = topic.get("rx_mbps", 0.0)
                    rx_size = topic.get("rx_data_size_str", "0 B") if rx_hz > 0.0 else "0 B"

                    diff_mbps = round(tx_mbps - rx_mbps, 1)
                    delivery_pct = topic.get("delivery_pct", 100.0)
                    loss_pct = round(100.0 - delivery_pct, 1) if is_allowed else last_loss

                    cfg_st = str(topic.get("status", "ALLOW")).upper()
                    if cfg_st == "DENY":
                        status_str = "DENIED"
                        verif_str = "BLOCKED BY CONFIG (DENY)"
                    elif is_allowed:
                        if tx_hz > 0.0 and rx_hz == 0.0:
                            status_str = "ALLOWED"
                            verif_str = "TX LIVE 100%"
                        elif rx_hz > 0.0 or tx_hz > 0.0:
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

                    csv_f.write(
                        f"{now_str},{topic['id']},{topic['name']},P{topic['priority']},{role},"
                        f"{tx_hz:.1f},{tx_size},{tx_mbps:.1f},"
                        f"{rx_hz:.1f},{rx_size},{rx_mbps:.1f},"
                        f"{diff_mbps:.1f},{delivery_pct:.1f}%,{status_str},{verif_str}\n"
                    )

                    # Log active streams under this parent topic
                    for s in topic.get("active_streams", []):
                        dev_id = s.get("device_ns") or s.get("device_name", "stream").lower().replace(" ", "_")
                        s_id = f"{topic['id']}:{dev_id}"
                        s_name = f"↳ [{s['device_name']}] {s['stream_key']}"
                        s_role = s.get("role", "IDLE")
                        s_tx_hz = s.get("tx_hz", 0.0)
                        s_tx_mbps = s.get("tx_mbps", 0.0)
                        s_tx_size = s.get("tx_data_size_str", "0 B") if s_tx_hz > 0.0 else "0 B"
                        s_rx_hz = s.get("rx_hz", 0.0)
                        s_rx_mbps = s.get("rx_mbps", 0.0)
                        s_rx_size = s.get("rx_data_size_str", "0 B") if s_rx_hz > 0.0 else "0 B"
                        s_diff = round(s_tx_mbps - s_rx_mbps, 1)
                        s_del = s.get("delivery_pct", 100.0)
                        s_status = "ACTIVE" if (s_tx_hz > 0.0 or s_rx_hz > 0.0) else status_str
                        s_verif = s.get("verification", "UNINITIATED")

                        csv_f.write(
                            f"{now_str},{s_id},{s_name},P{topic['priority']},{s_role},"
                            f"{s_tx_hz:.1f},{s_tx_size},{s_tx_mbps:.1f},"
                            f"{s_rx_hz:.1f},{s_rx_size},{s_rx_mbps:.1f},"
                            f"{s_diff:.1f},{s_del:.1f}%,{s_status},{s_verif}\n"
                        )

            # 2. Append to human-readable Text Log
            with open(self.text_logfile, "a", encoding="utf-8") as txt_f:
                txt_f.write(f"[{now_str}] PRIORITY SCHEDULER & DUAL Tx/Rx DIFFERENTIAL SNAPSHOT — MULTI-DEVICE STREAM TELEMETRY\n")
                txt_f.write(f"Network Capacity: {avail_bw:.1f} Mbps | Admitted Used: {used_bw:.1f} Mbps | Remaining: {max(0, avail_bw - used_bw):.1f} Mbps\n")
                txt_f.write(f"Publisher Transmitted (Tx): {total_tx_mbps:.1f} Mbps | Subscriber Received (Rx): {total_rx_mbps:.1f} Mbps | Total Diff: {total_diff_mbps:.1f} Mbps\n")
                txt_f.write("-" * 155 + "\n")
                txt_f.write(f"{'ID':<6} {'Topic / Stream Name':<42} {'Pri':<5} {'Role':<12} {'Tx Hz':<8} {'Publisher Tx':<17} {'Rx Hz':<8} {'Subscriber Rx':<17} {'Diff':<11} {'Delivery':<10} {'Status':<9} {'Verification':<18}\n")
                txt_f.write("-" * 155 + "\n")

                for name, topic in sorted(topics.items(), key=lambda x: (x[1]["priority"], x[1]["id"])):
                    is_allowed = name in allowed_topics or str(topic.get("status", "")).upper() in ["ALLOW", "ALLOWED"]
                    role = topic.get("role", "IDLE")

                    tx_hz = topic.get("tx_hz", 0.0)
                    tx_mbps = topic.get("tx_mbps", 0.0)

                    rx_hz = topic.get("rx_hz", 0.0)
                    rx_mbps = topic.get("rx_mbps", 0.0)

                    diff_mbps = round(tx_mbps - rx_mbps, 1)
                    delivery_pct = topic.get("delivery_pct", 100.0)
                    loss_pct = round(100.0 - delivery_pct, 1) if is_allowed else last_loss

                    cfg_st = str(topic.get("status", "ALLOW")).upper()
                    if cfg_st == "DENY":
                        status_str = "DENIED"
                        verif_str = "BLOCKED BY CONFIG (DENY)"
                    elif is_allowed:
                        if tx_hz > 0.0 and rx_hz == 0.0:
                            status_str = "ALLOWED"
                            verif_str = "TX LIVE 100%"
                        elif rx_hz > 0.0 or tx_hz > 0.0:
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

                    stream_badge = f" [🌐 {len(topic.get('active_streams', []))} stream{'s' if len(topic.get('active_streams', [])) > 1 else ''}]" if topic.get("active_streams") else ""
                    disp_name = f"{topic['name']}{stream_badge}"
                    tx_str = f"{tx_mbps:.1f} Mbps"
                    rx_str = f"{rx_mbps:.1f} Mbps"
                    diff_str = f"{diff_mbps:+.1f} Mbps"

                    txt_f.write(
                        f"T{topic['id']:<5} {disp_name:<42} P{topic['priority']:<4} {role:<12} "
                        f"{tx_hz:<8.1f} {tx_str:<17} {rx_hz:<8.1f} {rx_str:<17} "
                        f"{diff_str:<11} {delivery_pct:<9.1f}% {status_str:<9} {verif_str:<18}\n"
                    )

                    # Indented child stream lines
                    for s in topic.get("active_streams", []):
                        s_name = f"  ↳ [{s['device_name']}] {s['stream_key']}"
                        s_role = s.get("role", "IDLE")
                        s_tx_hz = s.get("tx_hz", 0.0)
                        s_tx_mbps = s.get("tx_mbps", 0.0)
                        s_rx_hz = s.get("rx_hz", 0.0)
                        s_rx_mbps = s.get("rx_mbps", 0.0)
                        s_diff = round(s_tx_mbps - s_rx_mbps, 1)
                        s_del = s.get("delivery_pct", 100.0)
                        s_status = "ACTIVE" if (s_tx_hz > 0.0 or s_rx_hz > 0.0) else status_str
                        s_verif = s.get("verification", "UNINITIATED")

                        s_tx_str = f"{s_tx_mbps:.1f} Mbps"
                        s_rx_str = f"{s_rx_mbps:.1f} Mbps"
                        s_diff_str = f"{s_diff:+.1f} Mbps"

                        txt_f.write(
                            f"{'':<6} {s_name:<42} P{topic['priority']:<4} {s_role:<12} "
                            f"{s_tx_hz:<8.1f} {s_tx_str:<17} {s_rx_hz:<8.1f} {s_rx_str:<17} "
                            f"{s_diff_str:<11} {s_del:<9.1f}% {s_status:<9} {s_verif:<18}\n"
                        )

                txt_f.write("=" * 155 + "\n\n")

            # 3. Dedicated active_streams.csv and active_streams.log
            active_streams_list = []
            for name, topic in sorted(topics.items(), key=lambda x: (x[1]["priority"], x[1]["id"])):
                for s in topic.get("active_streams", []):
                    active_streams_list.append((topic, s))

            if active_streams_list:
                with open(self.streams_csv_logfile, "a", encoding="utf-8") as scsv_f:
                    for topic, s in active_streams_list:
                        dev_id = s.get("device_ns") or s.get("device_name", "stream").lower().replace(" ", "_")
                        s_id = f"{topic['id']}:{dev_id}"
                        s_role = s.get("role", "IDLE")
                        s_tx_hz = s.get("tx_hz", 0.0)
                        s_tx_mbps = s.get("tx_mbps", 0.0)
                        s_tx_size = s.get("tx_data_size_str", "0 B") if s_tx_hz > 0.0 else "0 B"
                        s_rx_hz = s.get("rx_hz", 0.0)
                        s_rx_mbps = s.get("rx_mbps", 0.0)
                        s_rx_size = s.get("rx_data_size_str", "0 B") if s_rx_hz > 0.0 else "0 B"
                        s_diff = round(s_tx_mbps - s_rx_mbps, 1)
                        s_del = s.get("delivery_pct", 100.0)
                        is_allowed = topic['name'] in allowed_topics or str(topic.get("status", "")).upper() in ["ALLOW", "ALLOWED"]
                        s_status = "ACTIVE" if (s_tx_hz > 0.0 or s_rx_hz > 0.0) else ("ALLOWED" if is_allowed else "DENIED")
                        s_verif = s.get("verification", "UNINITIATED")

                        scsv_f.write(
                            f"{now_str},{s_id},{s['device_name']},{s['stream_key']},{topic['name']},P{topic['priority']},{s_role},"
                            f"{s_tx_hz:.1f},{s_tx_size},{s_tx_mbps:.1f},"
                            f"{s_rx_hz:.1f},{s_rx_size},{s_rx_mbps:.1f},"
                            f"{s_diff:.1f},{s_del:.1f}%,{s_status},{s_verif}\n"
                        )

                with open(self.streams_text_logfile, "a", encoding="utf-8") as stxt_f:
                    stxt_f.write(f"[{now_str}] ACTIVE MULTI-DEVICE STREAMS SNAPSHOT ({len(active_streams_list)} Streams Discovered)\n")
                    stxt_f.write("-" * 155 + "\n")
                    stxt_f.write(f"{'Device':<12} {'Stream Key':<36} {'Canonical Topic':<28} {'Pri':<5} {'Role':<12} {'Tx Hz':<8} {'Tx Mbps':<11} {'Rx Hz':<8} {'Rx Mbps':<11} {'Diff':<10} {'Delivery':<10} {'Verification':<18}\n")
                    stxt_f.write("-" * 155 + "\n")
                    for topic, s in active_streams_list:
                        s_role = s.get("role", "IDLE")
                        s_tx_hz = s.get("tx_hz", 0.0)
                        s_tx_mbps = s.get("tx_mbps", 0.0)
                        s_rx_hz = s.get("rx_hz", 0.0)
                        s_rx_mbps = s.get("rx_mbps", 0.0)
                        s_diff = round(s_tx_mbps - s_rx_mbps, 1)
                        s_del = s.get("delivery_pct", 100.0)
                        s_verif = s.get("verification", "UNINITIATED")
                        stxt_f.write(
                            f"{s['device_name']:<12} {s['stream_key']:<36} {topic['name']:<28} P{topic['priority']:<4} {s_role:<12} "
                            f"{s_tx_hz:<8.1f} {s_tx_mbps:<11.1f} {s_rx_hz:<8.1f} {s_rx_mbps:<11.1f} "
                            f"{s_diff:<10.1f} {s_del:<9.1f}% {s_verif:<18}\n"
                        )
                    stxt_f.write("=" * 155 + "\n\n")
