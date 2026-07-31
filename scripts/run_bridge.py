#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Bridge Application

Version 1.0

Peer Session
        │
        ▼
MeshSample
        │
        ▼
Topic Database
        │
        ▼
Admission Controller
        │
        ▼
Forwarding Engine
        │
        ▼
Router Session

===============================================================================
"""

import time

from mesh_transport.zenoh_session import ZenohSession

from routing.forwarding_engine import ForwardingEngine

from scheduler.admission_controller import AdmissionController

from ros.topic_database import TopicDatabase

from core.network_models import MeshSample


##########################################################################
# Configuration
##########################################################################

PEER_CONFIG = "/home/nvidia/ws_rmw_zenoh/src/rmw_zenoh-humble/rmw_zenoh_cpp/config/tcp/zenoh_peer_tcp.json5"

ROUTER_CONFIG = "/home/nvidia/ws_rmw_zenoh/src/rmw_zenoh-humble/rmw_zenoh_cpp/config/tcp/zenoh_router_tcp.json5"


##########################################################################
# Create Sessions
##########################################################################

peer = ZenohSession(PEER_CONFIG)

router = ZenohSession(ROUTER_CONFIG)

peer.connect()

router.connect()


##########################################################################
# Create Control Plane
##########################################################################

topic_database = TopicDatabase()

admission = AdmissionController(topic_database)

forwarding = ForwardingEngine(router)


print()
print("==============================================================")
print("Mesh Control Plane Started")
print("==============================================================")
print()


##########################################################################
# Callback
##########################################################################

def callback(sample):

    key = str(sample.key_expr)

    payload = sample.payload.to_bytes()

    print()

    print(f"[RECEIVED] {key}")

    ##############################################################

    mesh_sample = MeshSample(

        key=key,

        payload=payload

    )

    ##############################################################
    # Admission Decision
    ##############################################################

    mesh_sample.allowed = admission.evaluate(mesh_sample)

    ##############################################################
    # Forward
    ##############################################################

    forwarding.forward(mesh_sample)

    ##############################################################
    # Show Current Database
    ##############################################################

    topic_database.print_database()


##########################################################################
# Subscribe
##########################################################################

subscriber = peer.subscribe(

    "mesh/test",

    callback

)


##########################################################################
# Main Loop
##########################################################################

try:

    while True:

        time.sleep(1)

except KeyboardInterrupt:

    print()

    print("Stopping Mesh Control Plane...")

    forwarding.statistics()

    subscriber.undeclare()

    peer.close()

    router.close()
