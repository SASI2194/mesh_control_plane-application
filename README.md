# Mesh Control Plane

## Overview
**Mesh Control Plane** is an application developed to ensure loss-less, full data transmission across all topics in multi-system mesh networks. To achieve complete data delivery without loss, real-time dynamic topic bandwidth measurement, publication frequency (Hz) & payload size tracking, priority scheduling, packet loss tolerance monitoring, dynamic low-priority topic shedding, an interactive 7-sided polygon web telemetry portal, automatic scheduler logging, and password-protected development governance rules (`RULES.md`) are implemented within this control plane.

> [!IMPORTANT]
> **Exclusive Network Communication Policy (Rule 1)**:
> Data traveling from ROS 2 to Zenoh **MUST travel ONLY through this Mesh Control Plane application**. All raw inter-system topics are subjected to access control rules, and only admitted topics forwarded by the Mesh Control Plane (`filtered/**`) are permitted to transmit across physical network interfaces.

## Key Features
- **Mandatory Password-Protected RULES.md**: Enforces immutable architectural rules, Rule 1 exclusive control plane transport policy, P1–P5 priority scheduling, loss tolerance shedding, and testing governance. Managed via password-authenticated security script (`scripts/manage_rules.py`).
- **Real-Time Web Dashboard Portal**: Live web dashboard (`http://<node-ip>:8080`) monitoring the availability and health of all **9 mesh devices** (6 UGVs with Jetson Orin + NetMetal AX and 3 GCSs with Processing System + Switch + NetMetal AX). Features an interactive SVG **7-Sided Polygon (Heptagon) Wireless Mesh Topology Visualizer**, device filtering, and ultra-fast 500ms live telemetry streaming.
- **Real-Time Frequency (Hz) & Payload Data Size Tracker**: Dynamically computes and displays live publication frequency (Hz), message size (B, KB, MB), and measured Mbps for every topic in real-time. KeyMapper prefix matching (`*/<topic>/**`) eliminates loopback overcounting, matching exact 25 Hz ROS topic generation and Linux kernel `sar -n DEV 1` physical interface rates (~200–560 Mbps).
- **Priority Scheduler & Topic Admission Loggers**: Automatically records formatted text and CSV scheduler snapshots every second to `logs/priority_scheduler.log` and `logs/priority_scheduler.csv`. Erases previous session data on script startup for clean, per-run log analytics.
- **Configurable Packet Loss Tolerance & Topic Shedding**: Configurable `packet_loss_tolerance_percent` in `config/mesh.yaml` (e.g. 5.0%). If network congestion causes loss to exceed this limit, the `CongestionController` automatically sheds (drops) low-priority topics (P5, P4, P3, P2) to protect High-Priority topics (P1) from loss.
- **Lossless Full Data Verification**: Embeds 16-byte binary sequence header metadata in forwarded payloads (`MeshSample.pack_payload`). The receiver (`scripts/mesh_verification.py`) tracks sequence numbers to verify that 100% of data (0% packet loss) is delivered for all admitted topics.
- **Exclusive Mesh Routing**: Enforces system-to-system communication exclusively through the Mesh Control Plane.
- **Real-Time Low Latency**: Configured with 1ms TCP batch flushing and custom queue management for real-time inter-device streaming.
- **ROS2 & Zenoh Middleware Integration**: Synchronized directly with ROS2 Humble `rmw_zenoh_cpp` router and peer configurations.

## Governance & Rules Protection (`RULES.md`)
To unlock `RULES.md` for updates, authenticate with your master password:
```bash
python3 scripts/manage_rules.py unlock --password <pwd>
```
To lock and generate cryptographic SHA-256 signature:
```bash
python3 scripts/manage_rules.py lock
```
To verify file integrity:
```bash
python3 scripts/manage_rules.py verify
```

## Running the Application & Web Dashboard
Launch the Mesh Control Plane application:
```bash
python3 mesh_node.py
```
Access the dashboard portal in your browser: `http://192.168.3.65:8080` (or `http://localhost:8080`).

## Priority Scheduler Logs
- **Formatted Text Log**: `logs/priority_scheduler.log`
- **Structured CSV Data**: `logs/priority_scheduler.csv`

## Configuration Settings
Edit `config/mesh.yaml` to adjust network limits and tolerance:
```yaml
scheduler:
  maximum_bandwidth_mbps: 600           # Available network capacity limit (Mbps)
  packet_loss_tolerance_percent: 5.0    # Maximum tolerable packet loss limit (%)
  hysteresis_percent: 2.0               # Recovery hysteresis threshold (%)
```

## Zenoh Configuration Reference
The Zenoh TCP configuration files managed by this control plane are located at:
- **Router Configuration**: `config/zenoh/zenoh_router_tcp.json5` (linked to `/home/nvidia/ws_rmw_zenoh/.../zenoh_router_tcp.json5`)
- **Peer Configuration**: `config/zenoh/zenoh_peer_tcp.json5` (linked to `/home/nvidia/ws_rmw_zenoh/.../zenoh_peer_tcp.json5`)

## Sync Automation
Synchronization helper script:
```bash
./scripts/sync_zenoh_configs.sh {import|export|symlink}
```

## Release Information
- **Version**: `v2.2.0`
