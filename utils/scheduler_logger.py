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
            f.write("Timestamp,Topic_ID,Topic_Name,Priority,Role,Tx_Rate_Hz,Tx_Msg_Size,Tx_Live_Mbps,Rx_Rate_Hz,Rx_Msg_Size,Rx_Live_Mbps,Diff_Mbps,Delivery_Pct,Return_Peer_Loss_Pct,Admission_Status,Lossless_Verification\n")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.text_logfile, "w", encoding="utf-8") as f:
            f.write(f"===================================================================================\n")
            f.write(f" Mesh Control Plane Priority Scheduler & Dual Tx/Rx Differential Log (Session: {now_str})\n")
            f.write(f" Heartbeat Governance: Phase 1 Network HB @ 1.0 Hz (15.0s Timeout) | Phase 2 Tx HB @ 0.5 Hz (5.0s Timeout)\n")
            f.write(f" Peer Loss Feedback Return Status: Transmitted over Phase 2 Heartbeat (!f float loss)\n")
            f.write(f"===================================================================================\n\n")

    def log_snapshot(self, registry, scheduler, congestion_controller=None, bw_monitor=None):
        """
        Captures and writes current Tx/Rx Role rates, Differential Mbps, Delivery efficiency,
        and Rule 3 cross-verified Lossless Verification status to logs/priority_scheduler.csv
        and logs/priority_scheduler.log.
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

            monitor_obj = bw_monitor or getattr(scheduler, "bw_monitor", None)
            peer_loss = 0.0
            if monitor_obj and hasattr(monitor_obj, "peer_losses"):
                import time
                now = time.time()
                with monitor_obj.lock:
                    for ip, (ts, ploss) in list(monitor_obj.peer_losses.items()):
                        if (now - ts) <= 2.5 and ploss > peer_loss:
                            peer_loss = ploss

            has_tx = any(t.get("tx_hz", 0.0) > 0.0 for t in topics.values())
            has_rx = any(t.get("rx_hz", 0.0) > 0.0 for t in topics.values())

            if has_tx and not has_rx:
                feedback_str = f"Peer Return Loss Received: {peer_loss:.1f}% (via Phase 2 Tx HB)"
                display_loss = peer_loss
            else:
                feedback_str = f"Return Loss Transmitted: {last_loss:.1f}% (via Phase 2 Tx HB)"
                display_loss = last_loss

            # 1. Append to structured CSV Log
            with open(self.csv_logfile, "a", encoding="utf-8") as csv_f:
                for name, topic in sorted(topics.items(), key=lambda x: (x[1]["priority"], x[1]["id"])):
                    is_allowed = name in allowed_topics
                    role = topic.get("role", "IDLE")

                    tx_hz = topic.get("tx_hz", 0.0)
                    tx_mbps = topic.get("tx_mbps", 0.0) if is_allowed else 0.0
                    tx_size = topic.get("tx_data_size_str", "0 B") if tx_hz > 0.0 else "0 B"

                    rx_hz = topic.get("rx_hz", 0.0)
                    rx_mbps = topic.get("rx_mbps", 0.0)
                    rx_size = topic.get("rx_data_size_str", "0 B") if rx_hz > 0.0 else "0 B"

                    diff_mbps = round(tx_mbps - rx_mbps, 1)
                    delivery_pct = topic.get("delivery_pct", 100.0)
                    loss_pct = round(100.0 - delivery_pct, 1) if is_allowed else display_loss

                    cfg_st = str(topic.get("status", "ALLOW")).upper()
                    if cfg_st == "DENY":
                        status_str = "DENIED"
                        verif_str = "BLOCKED BY CONFIG (DENY)"
                    elif is_allowed:
                        if tx_hz > 0.0 and rx_hz == 0.0:
                            status_str = "ALLOWED"
                            verif_str = f"TX LIVE (PEER LOSS: {peer_loss:.1f}%)" if peer_loss > 0.0 else "TX LIVE 100%"
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
                            verif_str = f"SHEDDED ({display_loss:.1f}% LOSS)"
                        else:
                            status_str = "BLOCKED"
                            verif_str = "CAPACITY EXCEEDED"

                    csv_f.write(
                        f"{now_str},{topic['id']},{topic['name']},P{topic['priority']},{role},"
                        f"{tx_hz:.1f},{tx_size},{tx_mbps:.1f},"
                        f"{rx_hz:.1f},{rx_size},{rx_mbps:.1f},"
                        f"{diff_mbps:.1f},{delivery_pct:.1f}%,{display_loss:.1f}%,{status_str},{verif_str}\n"
                    )

            # 2. Append to human-readable Text Log
            with open(self.text_logfile, "a", encoding="utf-8") as txt_f:
                txt_f.write(f"[{now_str}] PRIORITY SCHEDULER & DUAL Tx/Rx DIFFERENTIAL SNAPSHOT\n")
                txt_f.write(f"Capacity: {avail_bw:.1f} Mbps | Used: {used_bw:.1f} Mbps | Remaining: {max(0, avail_bw - used_bw):.1f} Mbps | {feedback_str} | Heartbeats: Phase 1 Net (1.0 Hz) / Phase 2 Tx (0.5 Hz)\n")
                txt_f.write("-" * 125 + "\n")
                txt_f.write(f"{'ID':<4} {'Topic Name':<12} {'Pri':<5} {'Role':<10} {'Tx Hz':<8} {'Tx Mbps':<9} {'Rx Hz':<8} {'Rx Mbps':<9} {'Diff':<8} {'Delivery':<10} {'Status':<9} {'Verification':<24}\n")
                txt_f.write("-" * 125 + "\n")

                for name, topic in sorted(topics.items(), key=lambda x: (x[1]["priority"], x[1]["id"])):
                    is_allowed = name in allowed_topics
                    role = topic.get("role", "IDLE")

                    tx_hz = topic.get("tx_hz", 0.0)
                    tx_mbps = topic.get("tx_mbps", 0.0) if is_allowed else 0.0

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

                    txt_f.write(
                        f"{topic['id']:<4} {topic['name']:<12} P{topic['priority']:<4} {role:<10} "
                        f"{tx_hz:<8.1f} {tx_mbps:<9.1f} {rx_hz:<8.1f} {rx_mbps:<9.1f} "
                        f"{diff_mbps:<8.1f} {delivery_pct:<9.1f}% {status_str:<9} {verif_str:<16}\n"
                    )

                txt_f.write("=" * 115 + "\n\n")
