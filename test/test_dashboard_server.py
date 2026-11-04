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
    os.environ["no_proxy"] = "127.0.0.1,localhost"
    os.environ["HTTP_PROXY"] = ""
    os.environ["http_proxy"] = ""

    print("==========================================================")
    print("Testing Web Dashboard Telemetry Server (Port 8089)")
    print("==========================================================")

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    urllib.request.install_opener(opener)

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
    assert len(topo["nodes"]) >= 2
    assert len(topo["links"]) >= 1

    # 4. Test /api/config/neighbor_selection
    req_ns = urllib.request.urlopen("http://127.0.0.1:8089/api/config/neighbor_selection")
    assert req_ns.status == 200
    ns_cfg = json.loads(req_ns.read().decode("utf-8"))
    print(f"\n[Neighbor Selection API Test] Enabled: {ns_cfg.get('enabled')}")
    assert "scoring_weights" in ns_cfg
    assert "hard_boundaries" in ns_cfg

    # 5. Test /api/time_sync (GET)
    req_ts = urllib.request.urlopen("http://127.0.0.1:8089/api/time_sync")
    assert req_ts.status == 200
    ts_data = json.loads(req_ts.read().decode("utf-8"))
    print(f"\n[Time Sync API Test] Master Time: {ts_data.get('master_time_str')}")
    assert "master_time" in ts_data
    assert "nodes" in ts_data
    assert len(ts_data["nodes"]) == 9
    for n in ts_data["nodes"]:
        assert "clock_time" in n
        assert "clock_offset_sec" in n
        assert "clock_synced" in n

    # 6. Test /api/time_sync (POST Broadcast)
    post_data = json.dumps({"master_time": time.time()}).encode("utf-8")
    req_post = urllib.request.Request(
        "http://127.0.0.1:8089/api/time_sync",
        data=post_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req_post) as resp:
        assert resp.status == 200
        post_res = json.loads(resp.read().decode("utf-8"))
        print(f"[Time Sync Broadcast Test] Status: {post_res.get('status')}")
        assert post_res["status"] == "BROADCAST_COMPLETED"
        assert "master_time" in post_res

    # 7. Test /api/network_peers Clock Fields
    req_np = urllib.request.urlopen("http://127.0.0.1:8089/api/network_peers")
    assert req_np.status == 200
    np_tables = json.loads(req_np.read().decode("utf-8"))
    for local_id, table in np_tables.items():
        peers = table.get("peers", []) if isinstance(table, dict) else table
        for p in peers:
            assert "clock_time" in p
            assert "clock_offset_sec" in p
            assert "clock_offset_str" in p
            assert "clock_synced" in p

    # 8. Test HTML Index Page
    req_html = urllib.request.urlopen("http://127.0.0.1:8089/")
    assert req_html.status == 200
    html_content = req_html.read().decode("utf-8")
    print(f"\n[HTML Portal Page Test] Length: {len(html_content)} bytes")
    assert "<title>Mesh Control Plane" in html_content
    assert "btn-open-time-sync" in html_content
    assert "time-sync-modal" in html_content

    print("\n[SUCCESS] Web Dashboard Telemetry Server Tests PASSED!")


if __name__ == "__main__":
    main()

