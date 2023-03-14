from osc_d10.tools.io_files import read_json_file


class OSCButtplugConfiguration:
    def __init__(self):
        self.client_name = None
        self.web_sockets = None
        self.devices_configuration = None

    def __str__(self):
        return f"Name: {self.client_name}, WS: {self.web_sockets}, Devices: {self.devices_configuration}"

    def __repr__(self):
        return f"Name: {self.client_name}, WS: {self.web_sockets}, Devices: {self.devices_configuration}"

    def get_client_name(self):
        return self.client_name

    def set_client_name(self, name: str):
        self.client_name = name

    def get_web_sockets(self):
        return self.get_web_sockets

    def set_web_sockets(self, web_sockets: str):
        self.web_sockets = web_sockets

    def get_devices_configuration(self):
        return self.devices_configuration

    def set_devices_configuration(self, new_configuration):
        self.devices_configuration = new_configuration


async def load_configuration(configuration: OSCButtplugConfiguration):
    print("Buttplug load_configuration")
    buttplug_configuration = {"client_name": "OSC_D10", "web_sockets": "ws://127.0.0.1:12345"}
    devices_configuration = {}
    defaults = {"buttplug_configuration": buttplug_configuration, "devices_configuration": {}}
    data = read_json_file("osc_to_buttplug_configuration.json", defaults)
    if not data:
        print("Could not load/create the configuration for osc_to_buttplug")
        return

    configuration.set_client_name(data["buttplug_configuration"]["client_name"])
    configuration.set_web_sockets(data["buttplug_configuration"]["web_sockets"])
    configuration.set_devices_configuration(data["devices_configuration"])
    print(f"loaded osc configuration : {str(configuration)}")


