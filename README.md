# Mesh Control Plane

## Overview
**Mesh Control Plane** is an application developed to ensure loss-less, full data transmission across all topics in multi-system mesh networks. To achieve complete data delivery without loss, priority scheduling, dynamic bandwidth allocation, and strict access control are implemented within this control plane.

> [!IMPORTANT]
> **Exclusive Network Communication Policy**:
> Network communication among systems can be established **only** through this Mesh Control Plane application. All raw inter-system topics are subjected to access control rules, and only admitted topics forwarded by the Mesh Control Plane (`filtered/**`) are permitted to transmit across physical network interfaces.

## Key Features
- **Configurable Dynamic Bandwidth**: Bandwidth capacity is dynamically configurable via `config/mesh.yaml` (`scheduler.maximum_bandwidth_mbps`). The scheduler automatically admits topics from highest to lowest priority (P1 to P5) based on the configured limit.
- **Exclusive Mesh Routing**: Enforces system-to-system communication exclusively through the Mesh Control Plane.
- **Lossless Data Transfer**: Guarantees zero data loss across admitted published and subscribed topics.
- **Dynamic Priority Scheduling**: Implements topic-based priority scheduling (P1 through P5) and admission control.
- **Real-Time Low Latency**: Configured with 1ms TCP batch flushing and custom queue management for real-time inter-device streaming.
- **ROS2 & Zenoh Middleware Integration**: Synchronized directly with ROS2 Humble `rmw_zenoh_cpp` router and peer configurations.

## Bandwidth Configuration
To adjust the maximum available bandwidth for the mesh network, edit `config/mesh.yaml`:
```yaml
scheduler:
  maximum_bandwidth_mbps: 600    # Set desired capacity (e.g., 250, 600, 1000 Mbps)
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
- **Version**: `v1.3.0`
