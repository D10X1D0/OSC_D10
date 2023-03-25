from enum import Enum

from buttplug import Client, WebsocketConnector, ProtocolSpec
import janus

from osc_d10.osc_buttplug.osc_buttplug_configuration import OSCButtplugConfiguration


class OSCButtplugManager:
    """Class to store and access buttplug data"""
    def __init__(self, client: Client, queue: janus.Queue[any], bp_configuration: OSCButtplugConfiguration) -> None:
        # queue
        self.queue = queue
        # buttplug client parameters
        self.client = client
        self.configuration = bp_configuration

    def get_queue(self) -> janus.Queue[any]:
        return self.queue

    def set_queue(self, new_queue) -> None:
        self.queue = new_queue

    def get_client(self) -> Client:
        return self.client

    def set_client(self, client) -> None:
        self.client = client

    def get_devices_configuration(self) -> dict:
        return self.configuration.get_devices_configuration()

    def get_client_name(self) -> str:
        return self.configuration.get_client_name()

    def get_websockets(self) -> str:
        return self.configuration.get_web_socktes()

