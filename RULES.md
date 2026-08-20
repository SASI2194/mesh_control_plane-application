# Mesh Control Plane — Mandatory Development Rules

> [!CAUTION]
> **PROTECTED FILE & SECURITY GOVERNANCE**:
> This document (`RULES.md`) contains the immutable engineering, architecture, network, and release rules for the Mesh Control Plane application. 
> **Modifying or updating this file requires password authentication via `python3 scripts/manage_rules.py unlock --password <pwd>`.** Unauthorized edits will trigger integrity verification alerts (`manage_rules.py verify`).

---

## RULE 1: Exclusive Control Plane Transport Policy
> **Data traveling from ROS 2 to Zenoh MUST travel ONLY through this Mesh Control Plane application.**
> 
> - **Direct Transport Prohibition**: Direct bypass of raw ROS 2 DDS topics across physical network interfaces without passing through `mesh_node.py` is strictly forbidden.
> - **Filtered Key Mapping**: All inter-device topic traffic must be intercepted by `mesh_node.py`, sequence-tagged, scheduled according to priority (P1–P5), and forwarded exclusively over control plane keys (`filtered/**`).
> - **Access Control Enforcement**: Zenoh configuration (`zenoh_router_tcp.json5`) must enforce `"default_permission": "deny"` for un-admitted direct topic paths across physical interfaces.
> - **Strict Wireless Mesh Subnet Binding**: All inter-device control plane transport MUST strictly bind to the dedicated wireless mesh subnet (`192.168.3.0/24`, configured via `network.mesh_subnet_prefix` in `config/mesh.yaml`). Transport across secondary LAN/internet subnets (`192.168.12.x`) is strictly forbidden. If the wireless mesh interface is inactive, inter-device transmission MUST be held/discarded until the wireless link is established.
> - **ROS 2 Localhost Interface Isolation**: All local ROS 2 node graph communication MUST set `ROS_LOCALHOST_ONLY=1` and `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` to restrict DDS topic ingress exclusively to `127.0.0.1` (`lo`). Spilling raw ROS 2 DDS multicast traffic onto outer LAN/internet interfaces (`eth1` / `192.168.12.x`) is strictly forbidden.

---

## RULE 2: Dynamic Priority Scheduling, Role Indication & End-to-End Differential Rate Governance
- **Publisher (Tx) vs. Subscriber (Rx) Role Indications**:
  Each system running `mesh_node.py` must explicitly indicate its active operational role(s) per topic:
  - **Publisher Role (Tx)**: Measures and displays the **Published Data Rate** (Tx Hz, Tx Msg Size, Tx Published Mbps) generated locally by ROS 2 before entering the transport.
  - **Subscriber Role (Rx)**: Measures and displays the **Subscribed Data Rate** (Rx Hz, Rx Msg Size, Rx Subscribed Mbps) that actually entered and traveled through the physical network interface (`filtered/**`).
- **End-to-End Throughput Differential Calculation**:
  The system must calculate and log the throughput difference and delivery efficiency between the publisher's generated rate and the subscriber's received rate:
  $$\Delta \text{Bandwidth} = \text{Tx Published Mbps} - \text{Rx Subscribed Mbps}$$
  $$\text{Delivery Ratio (\%)} = \left(\frac{\text{Rx Subscribed Mbps}}{\text{Tx Published Mbps}}\right) \times 100$$
  This differential determines exact end-to-end transport efficiency and verifies that admitted topics achieve 100% full delivery without packet loss across the mesh network.
- **Topic Priorities & Dynamic Scheduling**: Topics must be strictly assigned to priority tiers P1 (highest) through P5 (lowest). The `BandwidthScheduler` continuously evaluates dynamic bandwidth demand and admits topics from P1 downward until available network capacity (`maximum_bandwidth_mbps` in `config/mesh.yaml`) is satisfied.

---

## RULE 3: Configurable Packet Loss Tolerance, Tx/Rx Rate Cross-Verification & Dynamic Topic Shedding
- **Loss Tolerance Limit**: Maximum allowable packet loss limit is set to `5.0%` (`packet_loss_tolerance_percent` in `config/mesh.yaml`).
- **Transmitter (Tx) Rate Sharing & Receiver (Rx) Cross-Verification**: The receiver monitor must cross-verify received data rate (`Rx Hz`, `Rx Mbps`) against expected publisher transmission rate (`Tx Hz`, `Tx Mbps`). Throughput loss is calculated as:
  $$\text{Throughput Loss (\%)} = \max\left(\text{Sequence Gap Loss (\%)},\; \frac{\text{Tx Rate (Hz)} - \text{Rx Rate (Hz)}}{\text{Tx Rate (Hz)}} \times 100\%\right)$$
  A reduction in received Hz rate (e.g., 22.5 Hz received vs. 25.0 Hz transmitted) is cross-verified and flagged as active packet loss (10.0% loss).
- **Publisher (Tx) vs. Subscriber (Rx) Verification Display**:
  - **Publisher Role (Tx)**: Displays `TX LIVE 100%` or `ALLOWED` to reflect active data transmission without false receiver loss warnings on the publisher node.
  - **Subscriber Role (Rx)**: Displays `FULL DATA 100%` when Rx rate equals Tx rate, or `X% LOSS DETECTED` / `SHEDDED (X% LOSS)` when throughput is reduced.
- **Dynamic Shedding Mechanism**: If physical link quality degrades and cross-verified packet loss exceeds 5.0%, the `CongestionController` target-drops low-priority topics (P5, P4, P3, P2) one topic per step with a 20s shedding dwell timer to protect Priority 1 topics (`/topic_01` to `/topic_04`).
- **Decoupled Fast Hysteresis Recovery**: When packet loss settles below 3.0% (tolerance minus hysteresis), topics are rapidly re-admitted using a 5s fast recovery dwell timer.

---

## RULE 4: 9-Device Mesh Telemetry & Web Dashboard Standards
- **Supported Architecture**: Web portal must support all **9 mesh devices**:
  - **6 UGVs** (`UGV-01` to `UGV-06`): Jetson Orin compute + NetMetal AX radio.
  - **3 GCSs** (`GCS-01` to `GCS-03`): Processing System + Ethernet Switch + NetMetal AX radio.
- **Port & Access**: Web telemetry portal operates on HTTP port `8080` (`dashboard/server.py`) and must auto-start with `mesh_node.py`.

---

## RULE 5: Lossless Payload Sequence Verification
- **Sequence Header Format**: Every forwarded `MeshSample` payload must be packed with a 16-byte binary header (`!Qd`: 8-byte uint64 sequence number + 8-byte double timestamp).
- **Receiver Verification**: The receiver monitor (`scripts/mesh_verification.py`) must unpack sequence headers and track sequence gaps to verify 100% full data delivery (`[FULL DATA 100%]`).

---

## RULE 6: Non-Blocking Architecture & Low-Latency Performance
- **1ms Batching Limit**: Zenoh TCP transport configuration must enforce `batching.time_limit: 1` ms to prevent buffer delays over physical wireless links.
- **Thread Safety**: All state updates in memory must use thread synchronization (`threading.Lock`).

---

## RULE 7: Testing, Verification & Release Governance
- **Automated Testing**: Every code change must pass all automated test scripts in `test/` (`test_zenoh.py`, `test_realtime_bandwidth.py`, `test_congestion_controller.py`, `test_dashboard_server.py`, `test_manage_rules.py`).
- **Semantic Versioning**: All release tags must follow `vX.Y.Z` semantic versioning guidelines.
- **Manual Approval Directive**: Code must NEVER be pushed to GitHub (`git push`) automatically without explicit manual user approval following local verification.

---

## RULE 8: Mandatory Release History Synchronization & Documentation Policy
- **Itemized Release History**: Every software release tag (`vX.Y.Z`) MUST contain an itemized, line-by-line version control entry in `README.md` documenting all feature additions, parameter updates, architectural refactors, and bug fixes before git commits are finalized or tags are created.
- **Pre-Push Documentation Audit**: Git tags MUST NOT be pushed to remote repositories (`git push origin --tags`) without verified release history alignment in `README.md`.

---

## RULE 9: Mandatory Version Release Documentation & Deprecation Governance Policy
- **Mandatory README Update Per Version**: Every version update MUST update `README.md` with explicit release notes detailing configuration changes (e.g., `node_offline_timeout_seconds` updated to 60.0 seconds).
- **Explicit Version Deprecation Notice**: Non-recommended or experimental interim versions (such as `v5.2.0`, `v5.3.0`, and `v5.4.0`) MUST be explicitly marked as **NOT RECOMMENDED / DEPRECATED** in the `README.md` version control release table.

