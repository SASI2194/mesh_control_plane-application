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
| **`v4.0.0`** | **Current Release** | **Major Release: NetMetal AX Hardware WiFi Radio Telemetry Panel, 3-Second Automated REST API Audit Loop, Inter-Device Zenoh Control Plane Radio Topic Broadcast (`/mesh_wifi_telemetry`) & Strict Device Telemetry Isolation**: <br/>• **NetMetal AX Hardware WiFi Radio Details Panel ([dashboard/public/app.js](file:///home/nvidia/meshcontrolplane/dashboard/public/app.js))**: Integrated live hardware radio interface details (`wifi1`, `wifi2`, `wifi2_vap`, `wifi2_vsb`, mode, band, operating frequency, RouterOS flags `MBR`, `BR`, `MBX`, `BI`, `X`) onto every device card in the Web Telemetry Portal (`http://<node-ip>:8080`).<br/>• **Automated Real-Time RouterOS REST API Audit Daemon Loop ([dashboard/server.py](file:///home/nvidia/meshcontrolplane/dashboard/server.py))**: Built non-blocking pre-emptive Basic Auth REST API hardware inspector (`_fetch_radio_interfaces()`) polling every 3 seconds for instant Winbox state updates.<br/>• **Inter-Device Zenoh Control Plane Radio Telemetry (`filtered/_mesh_wifi_telemetry/<ip>`)**: Implemented distributed Zenoh & native ROS 2 topic broadcast for sharing NetMetal AX WiFi radio status across all 9 mesh nodes in real time.<br/>• **Native ROS 2 Topic Graph Integration (`/mesh_wifi_telemetry`)**: Registered `/mesh_wifi_telemetry` in `ROSPublisherBridge` so it is 100% visible in `ros2 topic list` and echoable via `ros2 topic echo /mesh_wifi_telemetry`.<br/>• **Strict Device Telemetry Isolation & Memory Integrity**: Enforced physical host IP resolution (`_get_this_machine_ip()`) and deep-copy dictionary isolation (`copy.deepcopy`), ensuring local audit loops only update local cards, and remote broadcasts only update matching remote cards.<br/>• **RF Association Status Badge Differentiation**: Differentiated **`DISABLED`** (manually turned off in Winbox, Flag `X`) vs **`INACTIVE (NO LINK)`** (turned on, waiting for RF peer association, Flag `I`) vs **`RUNNING`** (actively connected, Flag `R`). |
| **`v3.3.0`** | Prior Release | **Feature & Governance Release: Synchronized CSV/Text Logger, Capacity Admission Control, Explicit ALLOW/DENY Topic Configuration & Native ROS 2 Publisher Bridge**: <br/>• **Synchronized CSV/Text Logger ([utils/scheduler_logger.py](file:///home/nvidia/meshcontrolplane/utils/scheduler_logger.py))**: Updated `SchedulerLogger.log_snapshot()` to write exact Rule 3 cross-verified `delivery_pct` and `verification` status strings (`6.0% LOSS DETECTED`, `TX LIVE 100%`, `FULL DATA 100%`, `SHEDDED`) to `priority_scheduler.csv` and `priority_scheduler.log`, ensuring 100% data parity between log files and web portal UI.<br/>• **Rule 2 Capacity Admission Control**: Enforced strict `maximum_bandwidth_mbps` capacity limits (800 Mbps) in `BandwidthScheduler.schedule()` using live measured topic rates to prevent total admitted transmission from exceeding network capacity.<br/>• **Receiver Self-Interception Filter**: Added timestamp-window filter `is_recently_republished()` to `ROSPublisherBridge` and subscriber callbacks, eliminating false `Tx/Rx DUAL` role indications on receiver nodes.<br/>• **Explicit `status: ALLOW / DENY` Topic Configuration ([config/topics.yaml](file:///home/nvidia/meshcontrolplane/config/topics.yaml))**: Replaced static nominal bandwidth properties in `topics.yaml` with explicit `status: ALLOW` or `status: DENY`. Topics marked with `status: DENY` (or `deny`) are automatically excluded from the admission list.<br/>• **Native ROS 2 Publisher Bridge (`/mesh_control_plane_receiver`)**: Instantiates native ROS 2 `rclpy` publishers for all admitted topics (`/topic_01` .. `/topic_20`) inside `mesh_node.py` so they are 100% visible in `ros2 topic list` and `ros2 node list`.<br/>• **Cryptographically Signed RULES.md Governance**: RULE 3 updated in `RULES.md` and signed with SHA-256 signature (`RULES.md.sig`). |
| **`v3.2.0`** | Prior Release | **Feature & Governance Release: Explicit ALLOW/DENY Topic Configuration, Native ROS 2 Publisher Bridge, 20s Wireless Stabilization Shedding Dwell Timer & Fast 5s Link Recovery**: <br/>• Initial release of explicit `status: ALLOW / DENY` topic configuration and Rule 2 capacity admission controls. |
| **`v3.1.0`** | Prior Release | **Feature Release: Native ROS 2 Publisher Bridge**: <br/>• Initial release of Native ROS 2 Publisher Bridge (`/mesh_control_plane_receiver`) for node graph topic visibility. |
| **`v3.0.0`** | Prior Release | **Major Release: Transmitter/Receiver Rate Cross-Verification, Decoupled Fast Recovery Dwell & Single Topic Step Shedding**: <br/>• Initial release of Tx/Rx rate cross-verification, decoupled recovery dwell timers, and single-topic step shedding policy. |
| **`v2.6.0`** | Prior Release | **Dynamic Real-Time Measured Bandwidth Aggregator, Re-entrant Lock Architecture & 1:1 Frequency Rectification**: <br/>• **Dynamic Real-Time Measured Bandwidth Aggregator**: Updated `get_system_summary()` in `dashboard/server.py` to dynamically sum real-time measured topic Mbps across active streams instead of reporting static nominal 560 Mbps capacity when idle. When no ROS 2 publisher nodes are active, the summary ribbon displays `0 / 600 Mbps`, dynamically scaling to `560 / 600 Mbps` under live transmission.<br/>• **Re-entrant Lock Synchronization (`RLock`) & Non-Blocking API Architecture**: Converted `TelemetryDataProvider` thread synchronization to `RLock()` and eliminated nested method lock re-entrancy in `get_system_summary()`. Guarantees sub-millisecond REST API response times (`/api/summary`, `/api/all`) with zero thread deadlock under concurrent web browser requests.<br/>• **1:1 Exact Transmit/Receive Pattern Alignment (`ros_to_zenoh`)**: Rectified 2x subscriber overcounting by mapping local ROS 2 topics to explicit domain prefix (`${ROS_DOMAIN_ID}/topic_01/**`). Prevents Zenoh wildcard pattern matching overlap with `filtered/**` control-plane keys, ensuring exact 1:1 Tx/Rx frequency alignment (25.0 Hz Tx $\leftrightarrow$ 25.0 Hz Rx). |
| **`v2.5.0`** | Prior Release | **Pure Application-Layer Control Plane Heartbeat Engine, Multi-Stage Dynamic Node IP Resolution & Web Portal Local Device Identity**: <br/>• **Web Portal Local Device Identity Indicator**: The web dashboard portal (`http://<node-ip>:8080`) displays a prominent **THIS DEVICE (LOCAL HOST)** badge in the top navigation header (`📍 THIS DEVICE (LOCAL HOST): UGV-01 • 192.168.3.65`), and highlights the local host device card with a bright cyan `[THIS DEVICE]` badge and glowing border.<br/>• **Pure Application-Layer Heartbeat Audit Engine**: Completely removed legacy ICMP ping loop subprocess overhead (`ping -c 1 -W 1`) from `dashboard/server.py`. Active device status is now 100% driven by 1 Hz Control Plane heartbeats and live topic activity, preventing false-negative drops from firewall rules or ICMP timeouts.<br/>• **Multi-Stage Dynamic Local IP Discovery Engine (`_detect_local_ip()`)**: Eliminated hardcoded fallback IP (`192.168.3.65`) in `mesh_node.py`. Implemented a 4-stage kernel route probe (`ip route get`), interface list scanner (`hostname -I`), UDP socket probe, and local fallback safety. Guarantees 100% accurate node identity resolution across all physical hardware units (UGV-01 through GCS-03).<br/>• **Origin IP Payload Header Embedding & Loopback Filter**: Encapsulated 4-byte IPv4 origin address in binary header (`!Qd4s`, 20 bytes). Subscriber callback filters out local loopback, ensuring accurate `Tx/Rx DUAL` role indications and differential rate calculations ($\Delta \text{Mbps}$). |
| **`v2.4.0`** | Prior Release | **RULE 2 Publisher/Subscriber Role Indications & 1 Hz Application Heartbeat Protocol**: <br/>• **Publisher (Tx) vs. Subscriber (Rx) Role Indications**: Tracks Tx rates (generated locally by ROS 2) and Rx rates (received over physical transport `filtered/**`). Displays `Tx PUBLISHER` (cyan), `Rx SUBSCRIBER` (purple), and `Tx/Rx DUAL` (green) badges.<br/>• **End-to-End Throughput Differential ($\Delta$)**: Computes $\Delta \text{Bandwidth} = \text{Tx Mbps} - \text{Rx Mbps}$ and Delivery Ratio ($\text{Rx Mbps} / \text{Tx Mbps} \times 100$) for every topic.<br/>• **1 Hz Control Plane Application Heartbeat Protocol**: Every running `mesh_node.py` broadcasts a 1 Hz heartbeat (`filtered/_mesh_heartbeat/<ip>`). The dashboard requires recent activity (<3.5s) for `ONLINE` status, immediately transitioning remote nodes to `OFFLINE` within 3 seconds when `mesh_node.py` is stopped without waiting for TCP timeout or WiFi state changes. |
| **`v2.3.0`** | Prior Release | **Telemetry Endpoint Sync & Dynamic Dual-Role Metrics Integration**: <br/>• **Server & Database Payload Integration**: Integrated dynamic Tx/Rx rates, diff Mbps, and delivery percentage into `/api/topics` REST API payloads.<br/>• **CSV & Text Scheduler Logger**: Updated `logs/priority_scheduler.csv` to record Tx, Rx, and Differential metrics per topic. |
| **`v2.2.0`** | Prior Release | **25 Hz Real-Time Dynamic Frequency & Msg Size Tracker & Parallel Telemetry Engine**: <br/>• **25 Hz Dynamic Rate Tracker**: Dynamically computes live publication frequency (Hz), message size (B, KB, MB), and measured Mbps for every topic in real-time.<br/>• **KeyMapper Overcounting Fix**: Updated prefix matcher to `*/<topic>/**`, matching exact 25 Hz ROS topic generation and Linux kernel `sar -n DEV 1` interface rates (~200–560 Mbps).<br/>• **Ultra-Fast Parallel Telemetry Server**: ThreadPoolExecutor ICMP pinging (<2ms API response, 500ms 2 Hz portal updates).<br/>• **Scheduler Log Reset**: Automatic log file clearing on startup and strict `0.0 Mbps` reporting for shedded topics. |
| **`v2.1.0`** | Prior Release | **Real-Time Web Telemetry Portal for 9 Mesh Devices**: <br/>• **Interactive 7-Sided Polygon (Heptagon) Wireless Topology Visualizer**: Renders wireless links across 6 UGVs and 3 GCSs with dynamic signal strength (RSSI) color coding.<br/>• **Device Health Grid & Filter Pills**: Displays device cards for 9 hardware nodes with real-time status and filter controls. |
| **`v2.0.0`** | Prior Release | **Configurable Packet Loss Tolerance & Dynamic Low-Priority Topic Shedding**: <br/>• **Congestion Controller**: Implements configurable `packet_loss_tolerance_percent` (e.g. 5.0%) and recovery hysteresis (2.0%).<br/>• **Dynamic Shedding**: Automatically drops low-priority topics (P5, P4, P3, P2) during network congestion to protect High-Priority topics (P1). |
| **`v1.3.0`** | Prior Release | **Lossless Payload Binary Sequence Packaging & Frame Gap Verification**: <br/>• **Binary Sequence Header**: Embeds 16-byte uint64 sequence number + double timestamp (`!Qd`) into forwarded payloads.<br/>• **Verification Engine**: Receiver tracks sequence gaps to confirm 100% data delivery (0% packet loss) on admitted topics. |
| **`v1.2.0`** | Prior Release | **Real-Time Bandwidth Measurement & Password-Protected RULES.md**: <br/>• **Sliding Window Monitor**: Real-time bandwidth tracking window.<br/>• **RULES.md Security Governance**: Password-authenticated locking/unlocking with SHA-256 cryptographic hash signatures (`scripts/manage_rules.py`). |
| **`v1.1.0`** | Prior Release | **P1–P5 Priority Bandwidth Scheduler & Admission Controller**: <br/>• **Priority Spectrum**: P1 (Critical) through P5 (Background) bandwidth allocation.<br/>• **Admission Controller**: Enforces strict capacity limits against configured network capacity (600 Mbps). |
| **`v1.0.0`** | Base Release | **Initial Mesh Control Plane Application**: <br/>• Base transport integration with ROS 2 Humble and Zenoh `rmw_zenoh_cpp` middleware.<br/>• Rule 1 Exclusive Transport Policy (`filtered/**`). |

## Release Information
- **Current Active Release Tag**: `v3.3.0`
