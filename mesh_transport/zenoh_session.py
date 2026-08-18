import zenoh


class ZenohSession:

    def __init__(self, config_file):

        self.config_file = config_file
        self.session = None

    #################################################################

    def connect(self, local_ip=None):

        config = zenoh.Config.from_file(self.config_file)

        if local_ip and local_ip.startswith("192.168.3."):
            # Enforce Rule 1: Bind Zenoh listening endpoints strictly to 192.168.3.x wireless mesh interface
            try:
                config.insert_json5("listen", f'{{"endpoints": ["tcp/{local_ip}:7447"]}}')
            except Exception:
                pass

        try:
            self.session = zenoh.open(config)
        except Exception as e:
            if local_ip and local_ip.startswith("192.168.3."):
                # If fixed port 7447 is occupied by another process, fallback to ephemeral port on 192.168.3.x
                try:
                    config.insert_json5("listen", f'{{"endpoints": ["tcp/{local_ip}:0"]}}')
                    self.session = zenoh.open(config)
                except Exception:
                    config.insert_json5("listen", '{"endpoints": []}')
                    self.session = zenoh.open(config)
            else:
                raise e

        print(f"[INFO] Connected : {self.config_file} (Bound to {local_ip or 'default'})")

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
