# Mesh Control Plane

## Overview
**Mesh Control Plane** is an application developed to ensure loss-less, full data transmission across all topics in multi-system mesh networks. To achieve complete data delivery without loss, real-time dynamic topic bandwidth measurement, Publisher (Tx) / Subscriber (Rx) role indications, end-to-end differential rate calculation, priority scheduling, packet loss tolerance monitoring, dynamic low-priority topic shedding, an interactive 7-sided polygon web telemetry portal, automatic scheduler logging, and password-protected development governance rules (`RULES.md`) are implemented within this control plane.

> [!IMPORTANT]
> **Exclusive Network Communication Policy (Rule 1)**:
> Data traveling from ROS 2 to Zenoh **MUST travel ONLY through this Mesh Control Plane application**. All raw inter-system topics are subjected to access control rules, and only admitted topics forwarded by the Mesh Control Plane (`filtered/**`) are permitted to transmit across physical network interfaces.

## Key Features
- **Mandatory Password-Protected RULES.md**: Enforces immutable architectural rules, Rule 1 exclusive control plane transport policy, Rule 2 Publisher/Subscriber role indications & differential rate calculation, P1–P5 priority scheduling, loss tolerance shedding, and testing governance. Managed via password-authenticated security script (`scripts/manage_rules.py`).
- **Publisher (Tx) vs. Subscriber (Rx) Role Indications & Differential Rate Tracker (Rule 2)**:
  - **Publisher Role (Tx)**: Displays published rate (Hz, Msg Size, Published Mbps) generated locally by ROS 2 before entering transport.
  - **Subscriber Role (Rx)**: Displays subscribed rate (Hz, Msg Size, Subscribed Mbps) actually received through the network transport (`filtered/**`).
  - **End-to-End Throughput Differential ($\Delta$)**: Calculates $\Delta \text{Mbps} = \text{Tx Mbps} - \text{Rx Mbps}$ and delivery percentage ($\text{Rx Mbps} / \text{Tx Mbps} \times 100$) to verify complete end-to-end transport delivery.
- **Real-Time Web Dashboard Portal**: Live web dashboard (`http://<node-ip>:8080`) monitoring the availability and health of all **9 mesh devices** (6 UGVs with Jetson Orin + NetMetal AX and 3 GCSs with Processing System + Switch + NetMetal AX). Features an interactive SVG **7-Sided Polygon (Heptagon) Wireless Mesh Topology Visualizer**, node role badges (`Tx PUBLISHER`, `Rx SUBSCRIBER`, `Tx/Rx DUAL`), device filtering, and ultra-fast 500ms live telemetry streaming.
- **Priority Scheduler & Topic Admission Loggers**: Automatically records formatted text and CSV scheduler snapshots every second to `logs/priority_scheduler.log` and `logs/priority_scheduler.csv` with Tx rates, Rx rates, and Differential Mbps. Erases previous session data on script startup for clean, per-run log analytics.
- **Configurable Packet Loss Tolerance & Topic Shedding**: Configurable `packet_loss_tolerance_percent` in `config/mesh.yaml` (e.g. 5.0%). If network congestion causes loss to exceed this limit, the `CongestionController` automatically sheds (drops) low-priority topics (P5, P4, P3, P2) to protect High-Priority topics (P1) from loss.
- **Lossless Full Data Verification**: Embeds 16-byte binary sequence header metadata in forwarded payloads (`MeshSample.pack_payload`). The receiver (`scripts/mesh_verification.py`) tracks sequence numbers to verify that 100% of data (0% packet loss) is delivered for all admitted topics.
- **Exclusive Mesh Routing**: Enforces system-to-system communication exclusively through the Mesh Control Plane.
- **Real-Time Low Latency**: Configured with 1ms TCP batch flushing and custom queue management for real-time inter-device streaming.
- **ROS2 & Zenoh Middleware Integration**: Synchronized directly with ROS2 Humble `rmw_zenoh_cpp` router and peer configurations.

## Network Ports & Communication Reference
The Mesh Control Plane utilizes specific network ports for data transport, telemetry, and application health monitoring:

| Port | Protocol | Purpose / Description |
| :--- | :--- | :--- |
| **Port 8080** | HTTP | **Web Telemetry Dashboard & Application Active Probe**: Serves the live Web Portal (`http://<node-ip>:8080`), REST API endpoints (`/api/all`), and responds to node active application health checks. |
| **Port 7447** | TCP | **Zenoh Inter-Device Data Transport**: High-performance TCP transport for ROS 2 inter-system control plane data (`filtered/**`) across physical network interfaces (`enP5p1s0f1`). |
| **Port 7446** | TCP | **Zenoh Router / Peer Discovery**: Internal discovery, router peering, and access control policy management (`zenoh_router_tcp.json5`). |

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

## Version Control & Detailed Release History

| Version | Release Status | Feature Additions, Governance Updates & Architectural Fixes |
| :--- | :--- | :--- |
| **`v2.4.0`** | **Current Release** | **RULE 2 Publisher/Subscriber Role Indications & End-to-End Throughput Differential Calculation**: <br/>• **Publisher (Tx) vs. Subscriber (Rx) Role Indications**: Tracks Tx rates (generated locally by ROS 2) and Rx rates (received over physical transport `filtered/**`). Displays `Tx PUBLISHER` (cyan), `Rx SUBSCRIBER` (purple), and `Tx/Rx DUAL` (green) badges.<br/>• **End-to-End Throughput Differential ($\Delta$)**: Computes $\Delta \text{Bandwidth} = \text{Tx Mbps} - \text{Rx Mbps}$ and Delivery Ratio ($\text{Rx Mbps} / \text{Tx Mbps} \times 100$) for every topic.<br/>• **Active Zenoh Transport Peer Audit**: Audits established Zenoh TCP transport sockets (`:7447`/`:7446`) to verify `mesh_node.py` is actively running on remote devices before marking them `ONLINE`. Default initial remote device status set to `OFFLINE`. |
| **`v2.3.0`** | Prior Release | **Telemetry Endpoint Sync & Dynamic Dual-Role Metrics Integration**: <br/>• **Server & Database Payload Integration**: Integrated dynamic Tx/Rx rates, diff Mbps, and delivery percentage into `/api/topics` REST API payloads.<br/>• **CSV & Text Scheduler Logger**: Updated `logs/priority_scheduler.csv` to record Tx, Rx, and Differential metrics per topic. |
| **`v2.2.0`** | Prior Release | **25 Hz Real-Time Dynamic Frequency & Msg Size Tracker & Parallel Telemetry Engine**: <br/>• **25 Hz Dynamic Rate Tracker**: Dynamically computes live publication frequency (Hz), message size (B, KB, MB), and measured Mbps for every topic in real-time.<br/>• **KeyMapper Overcounting Fix**: Updated prefix matcher to `*/<topic>/**`, matching exact 25 Hz ROS topic generation and Linux kernel `sar -n DEV 1` interface rates (~200–560 Mbps).<br/>• **Ultra-Fast Parallel Telemetry Server**: ThreadPoolExecutor ICMP pinging (<2ms API response, 500ms 2 Hz portal updates).<br/>• **Scheduler Log Reset**: Automatic log file clearing on startup and strict `0.0 Mbps` reporting for shedded topics. |
| **`v2.1.0`** | Prior Release | **Real-Time Web Telemetry Portal for 9 Mesh Devices**: <br/>• **Interactive 7-Sided Polygon (Heptagon) Wireless Topology Visualizer**: Renders wireless links across 6 UGVs and 3 GCSs with dynamic signal strength (RSSI) color coding.<br/>• **Device Health Grid & Filter Pills**: Displays device cards for 9 hardware nodes with real-time status and filter controls. |
| **`v2.0.0`** | Prior Release | **Configurable Packet Loss Tolerance & Dynamic Low-Priority Topic Shedding**: <br/>• **Congestion Controller**: Implements configurable `packet_loss_tolerance_percent` (e.g. 5.0%) and recovery hysteresis (2.0%).<br/>• **Dynamic Shedding**: Automatically drops low-priority topics (P5, P4, P3, P2) during network congestion to protect High-Priority topics (P1). |
| **`v1.3.0`** | Prior Release | **Lossless Payload Binary Sequence Packaging & Frame Gap Verification**: <br/>• **Binary Sequence Header**: Embeds 16-byte uint64 sequence number + double timestamp (`!Qd`) into forwarded payloads.<br/>• **Verification Engine**: Receiver tracks sequence gaps to confirm 100% data delivery (0% packet loss) on admitted topics. |
| **`v1.2.0`** | Prior Release | **Real-Time Bandwidth Measurement & Password-Protected RULES.md**: <br/>• **Sliding Window Monitor**: Real-time bandwidth tracking window.<br/>• **RULES.md Security Governance**: Password-authenticated locking/unlocking with SHA-256 cryptographic hash signatures (`scripts/manage_rules.py`). |
| **`v1.1.0`** | Prior Release | **P1–P5 Priority Bandwidth Scheduler & Admission Controller**: <br/>• **Priority Spectrum**: P1 (Critical) through P5 (Background) bandwidth allocation.<br/>• **Admission Controller**: Enforces strict capacity limits against configured network capacity (600 Mbps). |
| **`v1.0.0`** | Base Release | **Initial Mesh Control Plane Application**: <br/>• Base transport integration with ROS 2 Humble and Zenoh `rmw_zenoh_cpp` middleware.<br/>• Rule 1 Exclusive Transport Policy (`filtered/**`). |

## Release Information
- **Current Active Release Tag**: `v2.4.0`
