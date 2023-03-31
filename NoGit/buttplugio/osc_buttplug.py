import asyncio
from typing import Any

import janus
from buttplug import ProtocolSpec, Client, WebsocketConnector, Device

from NoGit.buttplugio.osc_buttplug_manager import OSCButtplugManager

from osc_d10.osc.osc_server_manager import OSCServerManager
from NoGit.buttplugio import osc_buttplug_setup

from osc_d10.tools.console_colors import bcolors


def print_buttplug(text) -> None:
    """helper fuction to print with pretty colors the name and message to the console"""
    msg = f"{bcolors.OKCYAN} btcoms : {bcolors.ENDC} {text}"
    print(msg)


def print_buttplug_warning(text) -> None:
    """helper fuction to print with pretty colors the name and message to the console"""
    msg = f"{bcolors.WARNING} btcoms : {bcolors.ENDC} {text}"
    print(msg)


async def device_probe(device_command: Device, bp_client: Client) -> None:
    """Sends the incoming command to a buttplug device."""
    # look for a toy that matches the name passed, and if it is present execute the command
    name = device_command[0][0]
    command = device_command[0][1][0]
    print_buttplug(bp_client.devices)
    if len(bp_client.devices) == 0:
        print_buttplug(f"Device not connected : {name}")
        return
    # TODO Remake the functions so they dont overlap so much
    # Check if the device with that name is listed in the connected dict().
    for key in bp_client.devices.keys():
        if bp_client.devices[key].name == name:
            device = bp_client.devices[key]
            if command == NoGit.buttplugio.osc_buttplug_manager.BpDevCommand.Vibrate.value:
                print_buttplug(f"Vibrating : {name} TODO")
            elif command == NoGit.buttplugio.osc_buttplug_manager.BpDevCommand.Rotate.value:
                print_buttplug(f"Rotating : {name} TODO")
            elif command == NoGit.buttplugio.osc_buttplug_manager.BpDevCommand.Stop.value:
                print_buttplug(f"Stoping : {name} TODO")
                await bp_client.devices[key].send_stop_device_cmd()
        else:
            print_buttplug(f"no device found to match this name : {name} - {device} or command : {command}")


async def rescan_devices(bp_client: [any]):
    await bp_client.start_scanning()
    await asyncio.sleep(10)
    await bp_client.stop_scanning()


async def listen_que_loop(q_listen: janus.AsyncQueue[any], bpclient: Client) -> None:
    """Loop that reads incoming OSC commands and sends them to the buttplug device"""
    print_buttplug("listening for commands from oscbridge")
    while True:
        # get a command item from the queue
        device_command = await q_listen.get()
        try:
            if bpclient.connected:
                await device_probe(device_command, bpclient)
            else:
                print_buttplug(f"Client disconnected from Intiface desktop.")
                raise ConnectionError
        except ConnectionError:
            print_buttplug(f"Client disconnected from Interface desktop.")
            break
        finally:
            # clear the task from the queue (leaks memory really fast if it's not cleared).
            q_listen.task_done()


async def clear_queue(q: janus.AsyncQueue[any]) -> None:
    """sync/async janus queue doesn't have a clear method, so we're geting all items to clear it manually."""
    for _ in range(q.qsize()):
        await q.get()
        await q.task_done()


async def connected_client(bp_manager: OSCButtplugManager) -> Client:
    """Returns a configured and connected buttplug client. Loops until a connection is made."""
    while True:
        try:
            # clear the queue commands so that it won't hold old commands while we can't send them to Interface
            await clear_queue(bp_manager.get_queue().async_q)
            print_buttplug("Starting the configuration to connect to Interface")
            """ We setup a client object to talk with Interface and it's connection"""
            client = Client(bp_manager.get_client_name(), ProtocolSpec.v3)
            ws = bp_manager.get_web_sockets()
            # edited websockets connector that will set itself as disconnected when the websockets connection drops.
            connector = WebsocketConnector(ws, logger=client.logger)
            print_buttplug("Trying to  connect to  Interface server")
            await client.connect(connector)
            print_buttplug("Could connect to  Interface server")
            return client
        except Exception as e:
            print_buttplug(f"Could not connect to Interface server, retrying in 1s :  {e}")
            await asyncio.sleep(1)


async def run_client_task(client: Client, q_in_l: janus.AsyncQueue[Any]) -> None:
    """Starts the buttplug client scanning and reading the incoming commands from the queue inside a task."""
    try:
        await client.start_scanning()
        await asyncio.sleep(5)
        await client.stop_scanning()
        """Start the queue listening"""
        task2 = asyncio.create_task(listen_que_loop(q_in_l, client), name="osc_bp_listen_que")
        await task2
        """When the task stops we stop the server scanning for devices and close the connection"""
        print_buttplug("Exiting client task")
        await client.disconnect()
    except Exception as e:
        task2.cancelled()
        print_buttplug_warning(f"run_client_task :{e}")
        return


async def run_osc_buttplug(osc_manager: OSCServerManager) -> None:
    """
    Creates tasks to read the incoming queue commands and sends them to the buttplug server
    The tasks will try to reconnect to the Buttplug server until a connection is made, and after it was dropped.
    It will also ask the buttplug server to rescan devices if a command asks for a device not currently connected.
    """
    print_buttplug("Starting Osc to buttplug")
    # run the client/connector in a loop to reset themselves if the connection is dropped.
    # this should prevent relaunching the full script if the ws connection is dropped
    # Queque with two sides, Async and Sync, used to communicate with the osc server
    try:
        que_buttplug: janus.Queue[Any] = janus.Queue(20)
        # manager object that will keep track of the configuration and some usefull objects
        bp_manager = NoGit.buttplugio.osc_buttplug_manager.OSCButtplugManager(que_buttplug)
        # pass the syncronous version for the dipatcher, runs blocking code.
        osc_buttplug_setup.run_initial_setup(osc_manager, bp_manager)
    except Exception as e:
        print_buttplug_warning(f"run_osc_buttplug exception  {e}")
        print_buttplug_warning("OSC To Buttplug done, could not start.")
        return
    while True:
        try:
            # instantiate a new client object from a helper function
            client = await connected_client(bp_manager)
            # start running the client and listening to messages from OSC
            await run_client_task(client, bp_manager.get_queue().async_q)

        except Exception as e:
            print_buttplug_warning(f"run_osc_buttplug Exception {e}")
            break
    print_buttplug("OSC To Buttplug done")

