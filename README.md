# Mesh Control Plane

## Overview
**Mesh Control Plane** is an application developed to ensure loss-less, full data transmission across all topics in multi-system mesh networks. To achieve complete data delivery without loss, real-time dynamic topic bandwidth measurement, priority scheduling, packet loss tolerance monitoring, and dynamic low-priority topic shedding are implemented within this control plane.

> [!IMPORTANT]
> **Exclusive Network Communication Policy**:
> Network communication among systems can be established **only** through this Mesh Control Plane application. All raw inter-system topics are subjected to access control rules, and only admitted topics forwarded by the Mesh Control Plane (`filtered/**`) are permitted to transmit across physical network interfaces.

## Key Features
- **Configurable Packet Loss Tolerance & Topic Shedding**: Allows configuring `packet_loss_tolerance_percent` in `config/mesh.yaml` (e.g. 5.0%). If network congestion causes loss to exceed this limit, the `CongestionController` automatically sheds (drops) low-priority topics (P5, P4, P3, P2) to protect High-Priority topics (P1) from loss.
- **Real-Time Dynamic Topic Bandwidth Measurement**: Measures incoming ROS topic bit-rates (Mbps) and packet rates in real-time using a sliding window monitor (`monitoring/bandwidth_monitor.py`). Non-stationary topic bandwidths (e.g. camera streams, lidar, point clouds) are dynamically measured as they change.
- **Lossless Full Data Verification**: Embeds 16-byte binary sequence header metadata in forwarded payloads (`MeshSample.pack_payload`). The receiver (`scripts/mesh_verification.py`) tracks sequence numbers to verify that 100% of data (0% packet loss) is delivered for all admitted topics.
- **Dynamic Priority Scheduling**: The `BandwidthScheduler` continuously evaluates live measured topic bandwidths against network capacity (`config/mesh.yaml`) and admits topics from highest to lowest priority (P1 to P5).
- **Exclusive Mesh Routing**: Enforces system-to-system communication exclusively through the Mesh Control Plane.
- **Real-Time Low Latency**: Configured with 1ms TCP batch flushing and custom queue management for real-time inter-device streaming.
- **ROS2 & Zenoh Middleware Integration**: Synchronized directly with ROS2 Humble `rmw_zenoh_cpp` router and peer configurations.

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
- **Version**: `v2.0.0`
