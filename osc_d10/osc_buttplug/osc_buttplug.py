import asyncio
import logging
from pprint import pprint

import buttplug
import janus
from buttplug import Client, WebsocketConnector, ProtocolSpec, Device

from osc_d10.osc.osc_server_manager import OSCServerManager
from osc_d10.osc_buttplug.osc_buttplug_configuration import load_configuration, OSCButtplugConfiguration, \
    DeviceConfiguration
from osc_d10.osc_buttplug.osc_buttplug_manager import OSCButtplugManager
from osc_d10.tools.console_colors import bcolors


def print_buttplug(text) -> None:
    """helper function to print with pretty colors the name and message to the console"""
    msg = f"{bcolors.OKCYAN} btcoms : {bcolors.ENDC} {text}"
    print(msg)


def print_buttplug_warning(text) -> None:
    """helper function to print with pretty colors the name and message to the console"""
    msg = f"{bcolors.WARNING} btcoms : {bcolors.ENDC} {text}"
    print(msg)


def check_device_config(bp_manager: OSCButtplugManager, client_devices: dict[int, Device]):
    try:
        n_client_devices = len(client_devices)

        if n_client_devices == 0:
            raise Exception("no devices connected to the buttplug server")
        dev_config = bp_manager.get_devices_configuration()
        n_configured_devices = len(dev_config)

        if n_configured_devices == 0 and n_client_devices == 0:
            raise Exception("no devices configured for OSC to Buttplug")
        # loop trough connected devices.
        for dev_index, device in client_devices.items():
            print(dev_index, device)
            # check that ther's a configuration for the device saved
            if device.name in dev_config:
                print(f"Device previously saved")
            else:
                print(f"Device to be configured")
                try:
                    new_device_configuration = DeviceConfiguration()
                    new_device_configuration.from_device(device)
                    bp_manager.configuration.add_device_configuration(new_device_configuration)
                except Exception as e:
                    print(f"device configuration error : {e}")
        bp_manager.configuration.save_configuration()

    except Exception as e:
        print(f"e: {e}")

    print(f"{bp_manager} {client_devices}")


async def buttplug_loop(osc_manager: OSCServerManager, bp_manager: OSCButtplugManager) -> None:
    try:
        client = Client(bp_manager.get_client_name(), ProtocolSpec.v3)
        connector = WebsocketConnector(bp_manager.get_websockets())
        bp_manager.set_client(client)
        try:
            await client.connect(connector)
            await client.start_scanning()
            await asyncio.sleep(10)
            await client.stop_scanning()
            check_device_config(bp_manager, client.devices)
            await client.disconnect()
        except Exception as e:
            logging.error(f"Could not connect to server, exiting: {e}")
            return
    except Exception as e:
        print(f"buttplug_loop exception {e}")
    finally:
        print(f"Exiting buttplug loop")


async def run_osc_to_buttplug(osc_manager: OSCServerManager) -> None:
    """Creates, configures and starts buttplug connections and device commands"""
    try:
        print_buttplug("Starting OSC to Buttplug")
        bp_config = load_configuration()
        print_buttplug("Buttplug load_configuration done")
        # Queue limited to 20 items, to avoid leaks.
        bp_queue: janus.Queue[20] = janus.Queue()
        bp_manager = OSCButtplugManager(bp_config, bp_queue, bp_config)
        await buttplug_loop(osc_manager, bp_manager)
    except Exception as e:
        print(f"exc {e}")
    finally:
        print_buttplug("Exiting OSC to Buttplug")

