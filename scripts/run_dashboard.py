#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Dashboard Portal Launcher Script

Launches the Web Telemetry Server at http://localhost:8080 (or your network IP).

===============================================================================
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dashboard.server import start_dashboard_server


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8080
    print("===============================================================================")
    print(f"Starting Mesh Control Plane Web Dashboard at http://{host}:{port}")
    print("Supports: 6 UGVs (Jetson Orin + NetMetal AX) & 3 GCSs (Proc System + Switch + NetMetal AX)")
    print("===============================================================================")
    start_dashboard_server(host=host, port=port)
