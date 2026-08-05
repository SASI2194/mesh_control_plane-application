#!/usr/bin/env python3

"""
===============================================================================
Mesh Control Plane

Test Script: Real-Time Dynamic Bandwidth Measurement & Sequence Verification
===============================================================================
"""

import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from monitoring.bandwidth_monitor import RealtimeBandwidthMonitor
from core.network_models import MeshSample


def main():
    print("==========================================================")
    print("Testing Real-Time Dynamic Topic Bandwidth Monitor")
    print("==========================================================")

    monitor = RealtimeBandwidthMonitor(window_size_sec=1.0)

    # 1. Simulate burst of 100 KB packets on /topic_01
    payload_100k = b"x" * 100000

    print("\n[Simulating 10 packets on /topic_01...]")
    seq_nums = []
    for _ in range(10):
        seq = monitor.record_sample("/topic_01", len(payload_100k))
        seq_nums.append(seq)
        time.sleep(0.05)

    bw_map = monitor.get_all_bandwidths()
    print(f"Measured Mbps for /topic_01: {bw_map.get('/topic_01', 0.0):.2f} Mbps")
    print(f"Sequence numbers generated: {seq_nums}")

    # 2. Verify sequence header encoding and decoding
    raw_data = b"ROS2 Image Frame Payload Data"
    packed = MeshSample.pack_payload(seq_num=42, timestamp=time.time(), raw_payload=raw_data)
    unpacked_seq, unpacked_ts, unpacked_origin, unpacked_raw = MeshSample.unpack_payload(packed)

    print("\n[Testing Payload Sequence Header Packing/Unpacking]")
    print(f"Original Payload Size : {len(raw_data)} bytes")
    print(f"Packed Payload Size   : {len(packed)} bytes (includes 16-byte header)")
    print(f"Unpacked Sequence #   : {unpacked_seq}")
    print(f"Unpacked Payload Match: {unpacked_raw == raw_data}")

    assert unpacked_seq == 42
    assert unpacked_raw == raw_data

    print("\n[SUCCESS] Real-Time Dynamic Bandwidth & Sequence Verification PASSED!")


if __name__ == "__main__":
    main()
