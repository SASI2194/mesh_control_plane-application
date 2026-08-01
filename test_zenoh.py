import time

from utils.logger import MeshLogger
from mesh_transport.zenoh_session import ZenohSession

MeshLogger.initialize("AGV01")

config_file = "config/zenoh/zenoh_peer_tcp.json5"
z = ZenohSession(config_file)
z.connect()
print("[SUCCESS] Zenoh Session connected successfully with enabled access_control!")

def callback(sample):
    print("Received sample on key:", sample.key_expr)
    print("Payload:", sample.payload.to_bytes().decode())

sub = z.subscribe("mesh/test", callback)
time.sleep(0.5)

z.publish("mesh/test", "Hello Mesh Control Plane")
print("[SUCCESS] Published to key: mesh/test")

time.sleep(1.0)
z.close()
print("[SUCCESS] Session closed cleanly.")
