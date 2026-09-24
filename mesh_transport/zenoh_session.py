import os
import zenoh


def resolve_zenoh_config_path(config_path: str) -> str:
    """
    Dynamically resolves Zenoh configuration file paths across different workspaces,
    devices (e.g. ugv01..ugv06), and Docker containers.
    """
    if config_path and os.path.exists(config_path):
        return config_path

    filename = os.path.basename(config_path) if config_path else "zenoh_peer_tcp.json5"
    env_var = "ZENOH_SESSION_CONFIG_URI" if "peer" in filename else "ZENOH_ROUTER_CONFIG_URI"
    if os.getenv(env_var) and os.path.exists(os.getenv(env_var)):
        return os.getenv(env_var)

    ws_dir_env = os.getenv("WS_ZENOH_DIR")
    if ws_dir_env:
        cand = os.path.join(ws_dir_env, filename)
        if os.path.exists(cand):
            return cand

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join("/home/nvidia/ugv/ros2_ws/src/ws_rmw_zenoh/src/rmw_zenoh-humble/rmw_zenoh_cpp/config/tcp", filename),
        os.path.join("/home/nvidia/ws_rmw_zenoh/src/rmw_zenoh-humble/rmw_zenoh_cpp/config/tcp", filename),
        os.path.join(base_dir, "config", "zenoh", filename),
        os.path.join(os.getcwd(), "config", "zenoh", filename),
    ]

    for cand in candidates:
        if os.path.exists(cand):
            return cand

    return config_path


class ZenohSession:

    def __init__(self, config_file):

        self.config_file = config_file
        self.session = None
        self.publishers = {}

    #################################################################

    def connect(self):

        resolved_file = resolve_zenoh_config_path(self.config_file)
        config = zenoh.Config.from_file(resolved_file)

        self.session = zenoh.open(config)

        print(f"[INFO] Connected : {resolved_file}")

    #################################################################

    def close(self):

        if self.session is not None:
            for pub in self.publishers.values():
                try:
                    pub.undeclare()
                except Exception:
                    pass
            self.session.close()

            print("[INFO] Session Closed")

    #################################################################

    def get_publisher(self, key):
        if not self.session:
            return None
        if key not in self.publishers:
            try:
                self.publishers[key] = self.session.declare_publisher(key)
            except Exception:
                return None
        return self.publishers.get(key)

    def publish(self, key, payload):
        pub = self.get_publisher(key)
        if pub:
            pub.put(payload)
        else:
            self.session.put(key, payload)

    def has_matching_subscribers(self, key):
        return True

    #################################################################

    def subscribe(self, key, callback):

        return self.session.declare_subscriber(
            key,
            callback
        )
