from enum import Enum

import janus
from osc_d10.osc.osc_server_manager import OSCServerManager


class BpDevCommand(Enum):
    # enum of valid commands for devices in osctobutplug
    # they have to match 1:1 in value with BpDevCommandInterface
    Stop = 1
    Vibrate = 2
    Rotate = 3


class BpDevCommandInterface(Enum):
    # enum of valid commands for devices in Buttplug and controllable in osctobutplug
    # they have to match 1:1 in value with BpDevCommand
    StopDeviceCmd = 1
    VibrateCmd = 2
    RotateCmd = 3


class OSCButtplugManager:
    """Class to store and access buttplug data"""
    def __init__(self, queue: janus.Queue,  config: OSCServerManager):
        # buttplug client parameters
        self.client_name = "OSC_D10"

        self.web_sockets = "{protocol}://{ip}:{port}"
        if config.intiface_protocol == "":
            self.web_sockets = self.web_sockets.replace("{protocol}://", "")

        if config.intiface_port == "":
            self.web_sockets = self.web_sockets.replace(":{port}", "")

        self.web_sockets = self.web_sockets.format(protocol = config.intiface_protocol,
                                                   ip = config.intiface_ip,
                                                   port = config.intiface_port)
        # queue
        self.queue = queue

    def get_queue(self):
        return self.queue

    def get_client_name(self) -> str:
        return self.client_name

    def get_web_sockets(self) -> str:
        return self.web_sockets
