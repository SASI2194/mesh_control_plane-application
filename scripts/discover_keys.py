#!/usr/bin/env python3

import time
import zenoh

CONFIG = "/home/nvidia/ws_rmw_zenoh/src/rmw_zenoh-humble/rmw_zenoh_cpp/config/tcp/zenoh_peer_tcp.json5"

cfg = zenoh.Config.from_file(CONFIG)

session = zenoh.open(cfg)


def callback(sample):

    print(sample.key_expr)


#
# Subscribe to everything
#

subscriber = session.declare_subscriber(
    "**",
    callback
)

print("Listening for all Zenoh keys...")

try:

    while True:
        time.sleep(1)

except KeyboardInterrupt:

    subscriber.undeclare()

    session.close()
