import janus


class OSCButtplugManager:
    def __init__(self, queue: janus.Queue):
        # buttplug client parameters
        self.client_name = "OSC_D10"
        self.web_sockets = "ws://127.0.0.1:12345"
        # queue
        self.queue = queue

    def get_queue(self):
        return self.queue

    def get_client_name(self) -> str:
        return self.client_name

    def get_web_sockets(self) -> str:
        return self.web_sockets
