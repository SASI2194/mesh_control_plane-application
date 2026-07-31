"""
===============================================================================
Mesh Control Plane V2
File    : constants.py
Author  : Mesh Control Plane Project
Purpose : Global constants used throughout the Mesh Control Plane
===============================================================================
"""

from enum import Enum

# =============================================================================
# PROJECT INFORMATION
# =============================================================================

PROJECT_NAME = "Mesh Control Plane"
PROJECT_VERSION = "2.0"

# =============================================================================
# NODE TYPES
# =============================================================================

class NodeType(Enum):
    GCS = "GCS"
    AGV = "AGV"

# =============================================================================
# NODE STATUS
# =============================================================================

class NodeStatus(Enum):
    OFFLINE = "OFFLINE"
    BOOTING = "BOOTING"
    DISCOVERY = "DISCOVERY"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"

# =============================================================================
# MESH STATES
# =============================================================================

class MeshState(Enum):
    INITIALIZATION = "INITIALIZATION"
    DISCOVERY = "DISCOVERY"
    NETWORK_FORMATION = "NETWORK_FORMATION"
    COORDINATOR_ELECTION = "COORDINATOR_ELECTION"
    NEIGHBOR_SELECTION = "NEIGHBOR_SELECTION"
    ROUTING = "ROUTING"
    NORMAL_OPERATION = "NORMAL_OPERATION"
    CONGESTION = "CONGESTION"
    FAILOVER = "FAILOVER"
    RECOVERY = "RECOVERY"
    SHUTDOWN = "SHUTDOWN"

# =============================================================================
# TOPIC PRIORITIES
# =============================================================================

class Priority(Enum):
    LEVEL1 = 1      # Mesh Management (Never Drop)
    LEVEL2 = 2      # Mission Critical
    LEVEL3 = 3      # High Priority
    LEVEL4 = 4      # Medium Priority
    LEVEL5 = 5      # Low Priority

# =============================================================================
# NETWORK PARAMETERS
# =============================================================================

TOTAL_GCS = 3
TOTAL_AGV = 6
TOTAL_NODES = TOTAL_GCS + TOTAL_AGV

DEFAULT_MAX_NEIGHBORS = 2

DEFAULT_MAX_BANDWIDTH_MBPS = 600

HYSTERESIS_PERCENT = 10

HEARTBEAT_INTERVAL = 1.0

DISCOVERY_INTERVAL = 2.0

LINK_MONITOR_INTERVAL = 1.0

BANDWIDTH_MONITOR_INTERVAL = 1.0

STATISTICS_INTERVAL = 5.0

ROUTE_UPDATE_INTERVAL = 5.0

TOPIC_ADVERTISEMENT_INTERVAL = 5.0

NEIGHBOR_TIMEOUT = 5.0

# =============================================================================
# LINK QUALITY WEIGHTS
# =============================================================================

RSSI_WEIGHT = 0.30

SNR_WEIGHT = 0.15

PACKET_LOSS_WEIGHT = 0.20

LATENCY_WEIGHT = 0.15

AVAILABLE_BANDWIDTH_WEIGHT = 0.20

# =============================================================================
# MESH TOPICS
# =============================================================================

MESH_DISCOVERY_TOPIC = "/mesh/discovery"

MESH_HEARTBEAT_TOPIC = "/mesh/heartbeat"

MESH_NEIGHBOR_TOPIC = "/mesh/neighbors"

MESH_BANDWIDTH_TOPIC = "/mesh/bandwidth"

MESH_STATUS_TOPIC = "/mesh/status"

MESH_TOPIC_DATABASE = "/mesh/topics"

MESH_DROPPED_TOPICS = "/mesh/dropped_topics"

MESH_ROUTE_TOPIC = "/mesh/routes"

MESH_CHANNEL_STATUS = "/mesh/channel_status"

# =============================================================================
# BANDWIDTH MANAGEMENT
# =============================================================================

MINIMUM_RESERVED_CONTROL_MBPS = 20

WARNING_UTILIZATION = 0.80

CRITICAL_UTILIZATION = 0.95

# =============================================================================
# LOGGING
# =============================================================================

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

DEFAULT_LOG_LEVEL = "INFO"

# =============================================================================
# FILES
# =============================================================================

CONFIG_FILE = "config/mesh.yaml"

PRIORITY_FILE = "config/priorities.yaml"

ROUTING_FILE = "config/routing.yaml"

# =============================================================================
# END OF FILE
# =============================================================================
