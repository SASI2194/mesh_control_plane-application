import zenoh


class ZenohSession:

    def __init__(self, config_file):

        self.config_file = config_file
        self.session = None
        self.publishers = {}

    #################################################################

    def connect(self):

        config = zenoh.Config.from_file(self.config_file)

        self.session = zenoh.open(config)

        print(f"[INFO] Connected : {self.config_file}")

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
        pub = self.get_publisher(key)
        if pub and hasattr(pub, "matching_status"):
            try:
                return pub.matching_status.matching
            except Exception:
                pass
        return True

    #################################################################

    def subscribe(self, key, callback):

        return self.session.declare_subscriber(
            key,
            callback
        )
