#!/usr/bin/env python3

"""
===============================================================================
Mesh Control Plane

Test Script: Web Dashboard Portal & REST API Server
===============================================================================
"""

import os
import sys
import time
import urllib.request
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dashboard.server import start_dashboard_background


def main():
    print("==========================================================")
    print("Testing Web Dashboard Telemetry Server (Port 8089)")
    print("==========================================================")

    # Start test server on port 8089 to avoid port conflicts
    t = start_dashboard_background(host="127.0.0.1", port=8089)
    time.sleep(1)

    # 1. Test /api/summary
    req = urllib.request.urlopen("http://127.0.0.1:8089/api/summary")
    assert req.status == 200
    summary = json.loads(req.read().decode("utf-8"))
    print(f"\n[Summary Endpoint Test] Status: {req.status}")
    print(f"Total Nodes: {summary['total_nodes']} (6 UGVs + 3 GCSs)")
    assert summary["total_nodes"] == 9
    assert summary["ugv_total"] == 6
    assert summary["gcs_total"] == 3

    # 2. Test /api/nodes
    req_nodes = urllib.request.urlopen("http://127.0.0.1:8089/api/nodes")
    assert req_nodes.status == 200
    nodes = json.loads(req_nodes.read().decode("utf-8"))
    print(f"\n[Nodes Endpoint Test] Devices Count: {len(nodes)}")
    assert len(nodes) == 9
    ugvs = [n for n in nodes if n["type"] == "UGV"]
    gcss = [n for n in nodes if n["type"] == "GCS"]
    assert len(ugvs) == 6
    assert len(gcss) == 3

    # 3. Test /api/topology
    req_topo = urllib.request.urlopen("http://127.0.0.1:8089/api/topology")
    assert req_topo.status == 200
    topo = json.loads(req_topo.read().decode("utf-8"))
    print(f"\n[Topology Endpoint Test] Nodes: {len(topo['nodes'])}, Links: {len(topo['links'])}")
    assert len(topo["nodes"]) == 9
    assert len(topo["links"]) >= 8

    # 4. Test HTML Index Page
    req_html = urllib.request.urlopen("http://127.0.0.1:8089/")
    assert req_html.status == 200
    html_content = req_html.read().decode("utf-8")
    print(f"\n[HTML Portal Page Test] Length: {len(html_content)} bytes")
    assert "<title>Mesh Control Plane" in html_content

    print("\n[SUCCESS] Web Dashboard Telemetry Server Tests PASSED!")


if __name__ == "__main__":
    main()
