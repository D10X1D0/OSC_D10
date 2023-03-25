import json
from dataclasses import dataclass

from buttplug import Device

from osc_d10.tools.io_files import read_json_file, create_default_file


class DeviceConfiguration:
    def __init__(self):
        self.name = None
        self.actuators = None
        self.linear_actuators = None
        self.rotary_actuators = None
        self.sensors = None
        self.commands = None

    def from_device(self, device: Device):
        self.name = device.name
        self.actuators = device.actuators
        self.linear_actuators = device.linear_actuators
        self.rotary_actuators = device.rotatory_actuators
        self.sensors = device.sensors
        self.commands = {}

    def to_file(self):
        print("todo")

    def to_tuple(self) -> tuple:
        data = (#"name":
                self.name,
                #"actuators":
                "actuator list (index, description, min value, max value",
                self.actuators_to_list(),
                "linear actuator list(index, type, timing(min, max) in miliseconds, position (min, max)in % 0.0 -> 1.0)",
                #"linear_actuators":
                self.linear_actuators_to_list(),
                #"rotary_actuators":
                "rotary actuator list (index, type, min, max rotating speed 0.0->1.0)",
                self.rotary_actuators_to_list(),
                #"sensors":
                "sensor list (type, range)",
                self.sensors_to_list(),
                #"commands":
                "commands",
                "not implemented yet")
        return data

    def actuators_to_list(self) -> list:
        data = []
        actuators = self.actuators
        if len(actuators) == 0:
            return data

        for item in actuators:
            # index, type, min float 0.0 -> 1.0, max float 0.0 -> 1.0
            act = (item.index, item.type, 0.0, 1.0)
            data.append(act)
        return data

    def linear_actuators_to_list(self) -> list:
        data = []
        linear_actuators = self.linear_actuators
        if len(linear_actuators) == 0:
            return data

        for item in linear_actuators:
            # index, type, timing(min, max) in miliseconds, position (min, max)in % 0.0 -> 1.0.
            actuator = (item.index, item.type, 0, 10000, 0.0, 1.0)
            data.append(actuator)
        return data

    def rotary_actuators_to_list(self) -> list:
        data = []
        rotary_actuators = self.rotary_actuators
        if len(rotary_actuators) == 0:
            return data

        for item in rotary_actuators:
            # index, type, min, max rotating speed 0.0->1.0
            rotary_actuator = item.feature_descriptor, 0.0, 1.0
            data.append(rotary_actuator)
        return data

    def sensors_to_list(self) -> list:
        data = []
        sensors = self.sensors
        if len(sensors) == 0:
            return data

        for sensor in sensors:
            sensor_to_lits = (sensor.type, sensor.ranges)
            data.append(sensor_to_lits)

        return data



class OSCButtplugConfiguration:
    def __init__(self, client_name: str, web_sockets: str, devices_configuration: dict[str, DeviceConfiguration]):
        self._client_name = client_name
        self._web_sockets = web_sockets
        self._devices_configuration = devices_configuration

    def get_client_name(self) -> str:
        return self._client_name

    def get_web_socktes(self) -> str:
        return self._web_sockets

    def get_devices_configuration(self) -> dict:
        return self._devices_configuration

    def add_device_configuration(self, device_config: DeviceConfiguration) -> dict:
        self._devices_configuration[device_config.name] = device_config

    def save_configuration(self) -> None:
        try:
            bp_config = {"client_name": self._client_name, "web_sockets": self._web_sockets}
            # dev_dict = {"device_name" : device_to_tuple}
            dev_dict = {}
            for dev_index, device in self._devices_configuration.items():
                dev_to_list = device.to_tuple()
                dev_dict[device.name] = dev_to_list
            dev_list = ("name", "actuators", "linear_actuators", "rotary_actuators", "sensors", "commands")
            # data = self.get_devices_configuration()
            config = {"buttplug_configuration": bp_config, "devices_configuration": dev_dict}
            create_default_file("osc_to_buttplug_configuration.json", config)
        except Exception as e:
            print(f"Error saving the configuration: {e}")


def load_configuration() -> OSCButtplugConfiguration:
    try:
        print("OSCButtplugConfiguration: Buttplug load_configuration")
        buttplug_configuration = {"client_name": "OSC_D10", "web_sockets": "ws://127.0.0.1:12345"}
        devices_configuration = {}
        defaults = {"buttplug_configuration": buttplug_configuration, "devices_configuration": {}}
        data = read_json_file("osc_to_buttplug_configuration.json", defaults)
        if not data:
            print("OSCButtplugConfiguration: Could not load/create the configuration for osc_to_buttplug")
            raise Exception("OSCButtplugConfiguration: Could not load/create the configuration for osc_to_buttplug")
        config = OSCButtplugConfiguration(data["buttplug_configuration"]["client_name"],
                                          data["buttplug_configuration"]["web_sockets"],
                                          devices_configuration_to_objects(data["devices_configuration"]))

        print(f"OSCButtplugConfiguration: loaded osc configuration : {str(config)}")
    except Exception as e:
        print(e)
    return config

def devices_configuration_to_objects(file_configuration):
    print("Todo devices_configuration_to_objects")
    return {}

