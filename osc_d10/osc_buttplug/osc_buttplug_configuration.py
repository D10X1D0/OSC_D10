from buttplug import Device

from osc_d10.tools.io_files import read_json_file, create_default_file


def actuators_to_list(actuators) -> list:
    data = []
    if len(actuators) == 0:
        return data

    for item in actuators:
        # index, type, min float 0.0 -> 1.0, max float 0.0 -> 1.0
        act = (item.index, item.type, 0.0, 1.0)
        data.append(act)
    return data


def linear_actuators_to_list(linear_actuators) -> list:
    data = []
    if len(linear_actuators) == 0:
        return data

    for item in linear_actuators:
        # index, type, timing(min, max) in miliseconds, position (min, max)in % 0.0 -> 1.0.
        actuator = (item.index, item.type, 0, 10000, 0.0, 1.0)
        data.append(actuator)
    return data


def rotary_actuators_to_list(rotary_actuators) -> list:
    data = []
    if len(rotary_actuators) == 0:
        return data

    for item in rotary_actuators:
        # index, type, min, max rotating speed 0.0->1.0
        rotary_actuator = item.feature_descriptor, 0.0, 1.0
        data.append(rotary_actuator)
    return data


def sensors_to_list(sensors) -> list:
    data = []
    if len(sensors) == 0:
        return data

    for sensor in sensors:
        sensor_to_lists = (sensor.type, sensor.ranges)
        data.append(sensor_to_lists)

    return data


class DeviceConfiguration:
    tuple_size = 11

    def __init__(self):
        self.name = None
        self.actuators = None
        self.linear_actuators = None
        self.rotary_actuators = None
        self.sensors = None
        self.commands = None

    def from_device(self, device: Device):
        self.name = str(device.name)
        self.actuators = actuators_to_list(device.actuators)
        self.linear_actuators = linear_actuators_to_list(device.linear_actuators)
        self.rotary_actuators = rotary_actuators_to_list(device.rotatory_actuators)
        self.sensors = sensors_to_list(device.sensors)
        self.commands = {}

    def from_tuple(self, name, actuators, linear_actuators, rotary_actuators, sensors, commands) -> None:
        self.name = name
        self.actuators = actuators
        self.linear_actuators = linear_actuators
        self.rotary_actuators = rotary_actuators
        self.sensors = sensors
        self.commands = commands

    def to_tuple(self) -> tuple:
        # Update the constant tuple_size = 11 is this tuple changes length
        data = (# "name":
                self.name,
                # "actuators":
                "actuator list (index, description, min value, max value",
                self.actuators,
                "linear actuator list(index, type, timing(min, max) in milliseconds, "
                "position (min, max)in % 0.0 -> 1.0)",
                # "linear_actuators":
                self.linear_actuators,
                # "rotary_actuators":
                "rotary actuator list (index, type, min, max rotating speed 0.0->1.0)",
                self.rotary_actuators,
                # "sensors":
                "sensor list (type, range)",
                self.sensors,
                # "commands":
                "commands",
                self.commands)
        return data


class OSCButtplugConfiguration:
    def __init__(self, client_name: str, web_sockets: str, devices_configuration: dict[str, DeviceConfiguration]):
        self._client_name = client_name
        self._web_sockets = web_sockets
        self._devices_configuration = devices_configuration

    def get_client_name(self) -> str:
        return self._client_name

    def get_web_sockets(self) -> str:
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

    def device_configuration_from_connected(self, dev_config,
                                                 client_devices: dict[int, Device]) -> None:
        """Processes connected devices and adds a device configuration object."""
        try:
            n_client_devices = len(client_devices)
            n_configured_devices = len(dev_config)

            if n_client_devices == 0:
                raise Exception("no devices connected to the buttplug server")

            if n_configured_devices == 0 and n_client_devices == 0:
                raise Exception("no devices configured for OSC to Buttplug")

            # loop trough connected devices.
            for dev_index, device in client_devices.items():
                print(f"{dev_index}, {device}")
                # check that there's a configuration for the device saved
                if device.name in dev_config:
                    print(f"Connected Device previously saved {device.name}")
                else:
                    print(f"Connected Device to be configured {device.name}")
                    try:
                        new_device_configuration = DeviceConfiguration()
                        new_device_configuration.from_device(device)
                        self.add_device_configuration(new_device_configuration)
                    except Exception as e:
                        print(f"device configuration error : {e}")

        except Exception as e:
            print(f"error checking the devices configuration: {e}")


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
        print(f"error in load_configuration {e}")
    return config


def devices_configuration_to_objects(file_configuration) -> dict:
    configuration = {}
    if len(file_configuration) == 0:
        return configuration
    for dev_name, dev in file_configuration.items():
        dev_conf = DeviceConfiguration()
        tuple_size = dev_conf.tuple_size
        if len(dev) != tuple_size:
            print(f"device {dev_name} has errors in its configuration file, has {len(dev)} "
                  f"insted of {tuple_size} elements configured.")
            next
        # check deviceconfiguration.to_tuple() to know the order.

        dev_conf.from_tuple(dev[0], dev[2], dev[4], dev[6], dev[8], dev[10])

        if dev_name == dev[0]:
            # the device name and key are the same, otherwise there's an error in the configuration file
            configuration[dev_name] = dev_conf
    print(f"file : {file_configuration}")
    return configuration
