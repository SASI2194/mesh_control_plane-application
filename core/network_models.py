"""
===============================================================================
Mesh Control Plane V2

File    : network_models.py
Purpose : Common data models used throughout the Mesh Control Plane.

===============================================================================
"""

from dataclasses import dataclass, field
from typing import Dict, List
import socket
import struct
import time

HEADER_FORMAT = "!Qd4s"  # 8-byte uint64 seq_num, 8-byte float64 timestamp, 4-byte origin_ip_bytes
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # 20 bytes


# =============================================================================
# Node Information
# =============================================================================

@dataclass
class NodeInfo:
    """
    Represents one AGV or GCS in the mesh.
    """

    node_id: str
    node_type: str

    ip_address: str = ""

    alive: bool = False
    coordinator: bool = False

    status: str = "BOOTING"

    last_seen: float = 0.0

    uptime: float = 0.0


# =============================================================================
# Link Metrics
# =============================================================================

@dataclass
class LinkMetrics:
    """
    Wireless link quality to another node.
    """

    node_id: str

    rssi: float = 0.0
    snr: float = 0.0
    ccq: float = 0.0

    tx_rate: float = 0.0
    rx_rate: float = 0.0

    latency: float = 0.0
    packet_loss: float = 0.0

    available_bandwidth: float = 0.0

    last_updated: float = 0.0


# =============================================================================
# Neighbor Information
# =============================================================================

@dataclass
class NeighborInfo:
    """
    Preferred forwarding neighbors.
    """

    node_id: str

    neighbors: List[str] = field(default_factory=list)


# =============================================================================
# Topic Information
# =============================================================================

@dataclass
class TopicInfo:
    """
    ROS topic information.
    """

    topic_name: str

    publisher: str

    priority: int

    bandwidth: float

    subscribers: List[str] = field(default_factory=list)

    dropped: bool = False


# =============================================================================
# Route Information
# =============================================================================

@dataclass
class RouteInfo:
    """
    End-to-end routing path.
    """

    source: str

    destination: str

    path: List[str] = field(default_factory=list)

    total_cost: float = 0.0


# =============================================================================
# Reservation Information
# =============================================================================

@dataclass
class ReservationInfo:
    """
    Scheduler bandwidth reservation.
    """

    topic_name: str

    reserved_bandwidth: float

    granted: bool = False


# =============================================================================
# Statistics
# =============================================================================

@dataclass
class StatisticsInfo:
    """
    Runtime statistics.
    """

    total_topics: int = 0

    active_nodes: int = 0

    dropped_topics: int = 0

    forwarded_topics: int = 0

    total_bandwidth: float = 0.0


@dataclass
class MeshSample:
    """
    Internal representation of one network message.
    """

    key: str

    payload: bytes

    timestamp: float = field(default_factory=time.time)

    source: str = ""

    priority: int = 5

    bandwidth: float = 0.0

    allowed: bool = True

    sequence_number: int = 0

    origin_ip: str = "127.0.0.1"

    @staticmethod
    def pack_payload(seq_num: int, timestamp: float, raw_payload: bytes, origin_ip: str = "127.0.0.1") -> bytes:
        try:
            ip_bytes = socket.inet_aton(origin_ip)
        except Exception:
            ip_bytes = socket.inet_aton("127.0.0.1")
        header = struct.pack(HEADER_FORMAT, seq_num, timestamp, ip_bytes)
        return header + raw_payload

    @staticmethod
    def unpack_payload(payload: bytes):
        if len(payload) >= HEADER_SIZE:
            try:
                seq_num, timestamp, ip_bytes = struct.unpack(HEADER_FORMAT, payload[:HEADER_SIZE])
                origin_ip = socket.inet_ntoa(ip_bytes)
                return seq_num, timestamp, origin_ip, payload[HEADER_SIZE:]
            except Exception:
                pass
        return 0, 0.0, "127.0.0.1", payload
