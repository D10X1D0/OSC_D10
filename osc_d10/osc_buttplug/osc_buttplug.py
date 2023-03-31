import asyncio
from datetime import datetime

import janus
from buttplug import Client, WebsocketConnector, ProtocolSpec, Device, ServerNotFoundError

from osc_d10.osc.osc_server_manager import OSCServerManager
from osc_d10.osc_buttplug.osc_buttplug_configuration import load_configuration, DeviceConfiguration
from osc_d10.osc_buttplug.osc_buttplug_manager import OSCButtplugManager
from osc_d10.tools.console_colors import bcolors


def print_buttplug(text: str) -> None:
    """helper function to print with pretty colors the name and message to the console"""
    msg = f"{bcolors.OKCYAN} btcoms : {bcolors.ENDC} {text}"
    print(msg)


def print_buttplug_warning(text: str) -> None:
    """helper function to print with pretty colors the name and message to the console"""
    msg = f"{bcolors.WARNING} btcoms : {bcolors.ENDC} {text}"
    print(msg)


async def buttplug_read_queue(client: Client, queue: janus.Queue) -> None:
    """Loops reading a queue filled with commands for buttplug devices, and runs them."""
    print_buttplug("reading the Queue for buttplug")
    loop = True
    while loop:
        if not client.connected:
            loop = False
            return
        await queue.async_q.get()
        try:
            # todo replace this test code with processing the queue
            print(f"client devices: {client.devices}")
            print("brrr")
            for device in client.devices:
                await client.devices[device].actuators[0].command(0.1)
                await asyncio.sleep(2)
                print("No brrr")
                await client.devices[device].actuators[0].command(0)
                await asyncio.sleep(2)
        except Exception as e:
            print(f"Error with device : {e}")
            print(f"x: {client.devices}")
            await asyncio.sleep(2)


async def buttplug_loop(osc_manager: OSCServerManager, bp_manager: OSCButtplugManager) -> None:
    """Creates the client object to comunicate with buttplug and reconnects if the connects is dropped"""
    try:
        butplug_loop_alive = True
        client = Client(bp_manager.get_client_name(), ProtocolSpec.v3)
        bp_manager.set_client(client)
        while butplug_loop_alive:
            try:
                # the reconnect method fails to reset the client/connector,
                # tested with a xbox controller  error: "the device is not ready to be used",
                # and won't rescan or re-populate the client.devices.
                # so we're making a new client object on every disconnection.
                # client = Client(bp_manager.get_client_name(), ProtocolSpec.v3)
                # connector = WebsocketConnector(bp_manager.get_web_sockets())
                client = Client(bp_manager.get_client_name(), ProtocolSpec.v3)
                connector = WebsocketConnector(bp_manager.get_web_sockets())
                await client.connect(connector)
                print_buttplug("scanning buttplug devices....")
                await client.start_scanning()
                await asyncio.sleep(10)
                await client.stop_scanning()
                bp_manager.update_configuration_from_client_devices(client.devices)
                bp_manager.configuration.save_configuration()
                print_buttplug(f"Devices : {client.devices} conn: {client.connected} {datetime.now()}")
                await buttplug_read_queue(client, bp_manager.get_queue())
            except ServerNotFoundError as e:
                print_buttplug_warning(f"Server not found. {e}")
            except Exception as e:
                print_buttplug_warning(f"Error : {e}")
    except Exception as e:
        print_buttplug_warning(f"Could not connect to server, exiting: {e}")
        return
    finally:
        try:
            # clinet.connected can throw an error if the clinet.connector is not set(=None)
            if client.connected:
                await client.disconnect()
        finally:
            print_buttplug(f"Exiting buttplug loop")


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
        print(f"run_osc_to_buttplug error :{e}")
    finally:
        print_buttplug("Exiting OSC to Buttplug")

