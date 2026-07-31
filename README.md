# Mesh Control Plane

## Overview
**Mesh Control Plane** is an application developed to ensure loss-less, full data transmission across all topics. To achieve complete data delivery without loss, priority scheduling and dynamic bandwidth allocation are implemented within this control plane.

## Key Features
- **Lossless Data Transfer**: Guarantees zero data loss across published and subscribed topics.
- **Priority Scheduling**: Implements topic-based priority scheduling and dynamic queue management.
- **ROS & Zenoh Integration**: Works in tandem with ROS2 nodes and Zenoh transport mechanisms.

## Zenoh Configuration Reference
The Zenoh TCP configuration files used by this control plane are located at:
- **Router Configuration**: `/home/nvidia/ws_rmw_zenoh/src/rmw_zenoh-humble/rmw_zenoh_cpp/config/tcp/zenoh_router_tcp.json5`
- **Peer Configuration**: `/home/nvidia/ws_rmw_zenoh/src/rmw_zenoh-humble/rmw_zenoh_cpp/config/tcp/zenoh_peer_tcp.json5`

## Initial Version
- **Version**: v1.0.0
