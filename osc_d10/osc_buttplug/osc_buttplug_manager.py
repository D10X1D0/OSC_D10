from enum import Enum

from buttplug import Client, WebsocketConnector, ProtocolSpec
import janus


class OSCButtplugManager:
    """Class to store and access buttplug data"""
    def __init__(self, client: Client, queue: janus.Queue[any], devices_configuration) -> None:
        # queue
        self.queue = queue
        # buttplug client parameters
        self.client = client
        self.devices_configuration = devices_configuration

    def get_queue(self):
        return self.queue

    def get_client(self):
        return self.client

    def set_client(self, client):
        self.client = client

    def get_devices_configuration(self):
        return self.devices_configuration

    def set_devices_configuration(self, new_configuration):
        self.devices_configuration = new_configuration
