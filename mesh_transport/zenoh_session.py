import zenoh


class ZenohSession:

    def __init__(self, config_file):

        self.config_file = config_file
        self.session = None

    #################################################################

    def connect(self):

        config = zenoh.Config.from_file(self.config_file)

        self.session = zenoh.open(config)

        print(f"[INFO] Connected : {self.config_file}")

    #################################################################

    def close(self):

        if self.session is not None:

            self.session.close()

            print("[INFO] Session Closed")

    #################################################################

    def publish(self, key, payload):

        self.session.put(key, payload)

    #################################################################

    def subscribe(self, key, callback):

        return self.session.declare_subscriber(

            key,

            callback

        )
