"""
===============================================================================
Mesh Control Plane V2

File    : network_models.py
Purpose : Common data models used throughout the Mesh Control Plane.

===============================================================================
"""

from dataclasses import dataclass, field
from typing import Dict, List


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

from dataclasses import dataclass
import time


@dataclass
class MeshSample:
    """
    Internal representation of one network message.
    """

    key: str

    payload: bytes

    timestamp: float = time.time()

    source: str = ""

    priority: int = 5

    bandwidth: float = 0.0

    allowed: bool = True
