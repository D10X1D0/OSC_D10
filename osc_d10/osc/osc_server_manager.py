from pythonosc import udp_client

import myclasses

# custom dispatcher with a bug patched
from osc_d10.osc import osc_dispatcher_d10


class OSCServerManager:
    """Class to store and share server data and functions"""
    def __init__(self, main_configuration: myclasses.MainData.mainconfig) -> None:
        self.osc_debug = main_configuration["OSCBridgeDEBUG"]
        self.server_ip = main_configuration["OSCBListenIP"]
        self.server_port = main_configuration["OSCBListenPort"]
        self.client_ip = main_configuration["OSCSendIP"]
        self.client_port = main_configuration["OSCSendPort"]
        self.dispatcher = osc_dispatcher_d10.D10Dispatcher()
        self.client = udp_client.SimpleUDPClient(self.client_ip, self.client_port)
        self.mapped_commands = 0
        self.commands_data = dict()

    def map_osc(self, osc_adress, function, *args) -> None:
        """registers a function to listen to an osc adress"""
        self.dispatcher.map(osc_adress, function, args)

    def unmap_osc(self, osc_adress, function, *args) -> None:
        """un-registers a function to listen to an osc adress"""
        print("not implemented ")

    def default_dispatcher_handler(self, func_name):
        self.dispatcher.set_default_handler(func_name)

    def add_command_data(self, module_name: str, data: dict) -> None:
        try:
            self.commands_data[module_name] = data
        except Exception as e:
            print(f"add_command_data error : {e}")

    def get_command_data(self, module_name, module_data) -> object:
        return self.commands_data[module_name][module_data]
