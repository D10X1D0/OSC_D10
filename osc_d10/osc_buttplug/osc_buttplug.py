import asyncio
from typing import Any

import janus

from buttplug.client import ButtplugClient, ButtplugClientConnectorError, ButtplugClientDevice
from buttplug.core import ButtplugDeviceError

import osc_d10.osc_buttplug.osc_buttplug_manager
from osc_d10.osc_buttplug.D10ButtplugClientWebsocketConnector import D10ButtplugClientWebsocketConnector
from osc_d10.osc_buttplug.osc_buttplug_manager import OSCButtplugManager

from osc_d10.osc.osc_server_manager import OSCServerManager
from osc_d10.osc_buttplug import osc_buttplug_setup

from osc_d10.tools.console_colors import bcolors
from osc_d10.tools.io_files import create_default_file, try_read_json


def print_buttplug(text) -> None:
    """helper fuction to print with pretty colors the name and message to the console"""
    msg = f"{bcolors.OKCYAN} btcoms : {bcolors.ENDC} {text}"
    print(msg)


def print_buttplug_warning(text) -> None:
    """helper fuction to print with pretty colors the name and message to the console"""
    msg = f"{bcolors.WARNING} btcoms : {bcolors.ENDC} {text}"
    print(msg)


def device_dump(dev: ButtplugClientDevice, serialized_device: dict()) -> None:
    """Create a devicename.json file with all it's supported commands"""
    d_name = dev.name
    try:
        # Check if the file exists by trying to read it
        try_read_json(f"{d_name}.json")
        print_buttplug(f"Dump file already exists, skipping creating it. {d_name}")
    except FileNotFoundError:
        print_buttplug(f"Dump file does not exist, creating it. {d_name}")
        create_default_file(f"{d_name}.json", serialized_device)
    except Exception as e:
        print_buttplug(f"Error creating a dump file for {d_name} : {e}")


async def serialize_device(dev: ButtplugClientDevice) -> dict():
    """Read and format the buttplug device information into a dict() and print it to a .json file"""
    print_buttplug(f"Creating dump file for {dev.name}")
    # dictionary with devicename, osctobuttplugcomamnds:, buttplug raw commands
    serializable_data = dict()
    # dictionary that will contain the osctobuttplug supported commands
    clist = list()
    # dictionary that will contain all the device's buttplug supported commands.
    clistraw = list()
    # Start the data dictionary with the device name.
    serializable_data['devicename'] = str(dev.name)
    for msg in dev.allowed_messages:
        """Check if it has .featurecount, indicates number of motors/vibrators."""
        fcount = None
        try:
            fcount = dev.allowed_messages[str(msg)].feature_count
            """The current message has a .featurecount"""
            # printbpcoms(f"The message {msg}, has .featurecount = {fcount}")
        except AttributeError:
            """The current message does not have a .featurecount"""
            # printbpcoms(f"The message {msg}, does not have .featurecount")

        """Check if it's implemented in OSCtobuttplug and translate its name to the internal one."""
        try:
            # buttplug command name's value from (BpDevCommandInterface(Enum))
            bpnamevalue = osc_d10.osc_buttplug.osc_buttplug_manager.BpDevCommandInterface[str(msg)].value
            # osctobuttplug command name's translated (BpDevCommand(Enum))
            octobpname = osc_d10.osc_buttplug.osc_buttplug_manager.BpDevCommand(bpnamevalue).name
            """It's implemented in OSCtobuttlug and it's name could be translated"""
            if fcount is None:
                """no featurecount for the current command, just add the command name to the list/dict"""
                clist.append(str(octobpname))
                clistraw.append(str(msg))
            else:
                """no featurecount for the current command, adding it to the command name"""
                clist.append({str(octobpname): fcount})
                clistraw.append({str(msg): fcount})
        except KeyError:
            """It's not implemented in OSCtobuttlug or could not be translated"""
            if fcount is None:
                # printbpcoms(f"appending {msg} without fcount to bprraw")
                clistraw.append(str(msg))
            else:
                # printbpcoms(f"appending {msg} with fcount = {fcount} to bprraw")
                clistraw.append({str(msg): fcount})

    serializable_data['osctobuttplugcommands'] = clist
    serializable_data['buttplugrawcommands'] = clistraw
    return serializable_data


async def device_added_task(dev: ButtplugClientDevice) -> None:
    """Generates a dict() with the device name and propertys and creates a devicename.json file on disk"""
    print_buttplug("Device Added: {}".format(dev.name))
    # get the serialized device data
    dev_data = await serialize_device(dev)
    # Print it to the console
    print_buttplug(dev_data)
    # dump it to disk inside a devicename.json file
    device_dump(dev, dev_data)


def device_added(emitter, dev: ButtplugClientDevice) -> None:
    """Callback used by the client when a device is added to the server"""
    asyncio.create_task(device_added_task(dev))


def device_removed(emitter, dev: ButtplugClientDevice) -> None:
    """Callback used by the client when a device is removed from the server"""
    print_buttplug(f"Device removed: {dev}")


async def vibrate_device(device: ButtplugClientDevice, device_command) -> None:
    """Ask the buttplug server to vibrate the device motor/s, rounds the speed to be inside 0->1 range"""
    name = device_command[0][0]
    motors = device_command[0][1][1]
    # make sure the value is inside the range 0->1
    value = max(min(float(device_command[1]), 1.0), 0.0)
    command = dict()
    if type(motors) is str:
        # I'ts one number, indicating all motors should be set
        # I found that my device didn't vibrate all motors sending just a float after sending a tuple once,
        # so I'm setting all motors.
        motors = device.allowed_messages["VibrateCmd"].feature_count
        for i in range(motors):
            command[i] = value

    else:
        # It's a list of numbers, indicating all individual motors to be set
        for i in motors:
            command[i] = value
    try:
        # printbpcoms(f"Command : {command} : {(type(command))}")
        print_buttplug(f"Vibrating : {device.name} : motor/s : {motors} : speed : {value}")
        await device.send_vibrate_cmd(command)
    except ButtplugDeviceError as e:
        print_buttplug(f'configured motor outside of the device range. {e}')
    except ButtplugClientConnectorError as e:
        print_buttplug(f"ButtplugClientConnectorError, disconnected? {e}")
        raise ButtplugClientConnectorError("ButtplugClientConnectorError, disconnected?")


async def rotate_device(device: ButtplugClientDevice, device_command) -> None:
    """Ask the buttplug server to rotate the device motor/s, rounds the speed to be inside 0->1 range"""
    try:
        name = device_command[0][0]
        motorlist = device_command[0][1][1]
        # make sure the value is inside the range 0->1
        value = max(min(float(device_command[1]), 1.0), 0.0)
        command = dict()
    except Exception as e:
        print(f"Could not read the command to rotatedevice : {e}")
        return
    if isinstance(motorlist, str):
        # All motors to turn
        if motorlist == "allcw":
            # clock wise
            command = (value, True)
        elif motorlist == "allccw":
            # counter clock wise
            command = (value, False)
        else:
            # invalid direction to rotate
            print_buttplug("didn't find the direction to set the rotation: allcw or allccw ")
            return
        command = tuple(command)
    elif isinstance(motorlist, list):
        # List of motors and directions
        n_motors = len(motorlist)

        if isinstance(motorlist[0], int):
            # just one motor to set : a Tuple of [float, bool]
            command = motorlist[0], motorlist[1]
            command = tuple(command)
            # printbpcoms(f"Setting one motor {command}")
        elif isinstance(motorlist[0], list):
            # more than one motor to set : a dict of int to Tuple[float, bool]
            command = dict()
            for i in range(n_motors):
                motorindex = motorlist[i]
                command[motorindex[0]] = value, motorindex[1]
            # printbpcoms(f"Setting more than one motor {command}")
        # printbpcoms(f"nmotors : {nmotors}")

    print_buttplug(f"Rotating : {name} : {command}")
    await device.send_rotate_cmd(command)


async def device_probe(device_command, bp_client: ButtplugClient) -> None:
    """Sends the incoming command to a buttplug device.
    It will ask the server to scan for devices if the one in the command is not connected.
    """
    # look for a toy that matches the name passed, and if it is present execute the command
    name = device_command[0][0]
    command = device_command[0][1][0]
    if len(bp_client.devices) == 0:
        print_buttplug(f"Device not connected : {name}")
        # we tell the server to stop and scan again.
        # this will help not to do a full reset after a dropped bluetooth connection
        await rescan_devices(bp_client)
        return
    # Check if the device with that name is listed in the connected dict().
    for key in bp_client.devices.keys():
        if bp_client.devices[key].name == name:
            device = bp_client.devices[key]
            if command == osc_d10.osc_buttplug.osc_buttplug_manager.BpDevCommand.Vibrate.value:
                await vibrate_device(device, device_command)
            elif command == osc_d10.osc_buttplug.osc_buttplug_manager.BpDevCommand.Rotate.value:
                await rotate_device(device, device_command)
            elif command == osc_d10.osc_buttplug.osc_buttplug_manager.BpDevCommand.Stop.value:
                print_buttplug(f"Stoping : {name}")
                await bp_client.devices[key].send_stop_device_cmd()
        else:
            print_buttplug(f"no device found to match this name : {name} - {device} or command : {command}")


async def rescan_devices(bp_client: ButtplugClient):
    await bp_client.start_scanning()
    await asyncio.sleep(10)
    await bp_client.stop_scanning()


async def listen_que_loop(q_listen: janus.AsyncQueue[Any], bpclient: ButtplugClient) -> None:
    """Loop that reads incoming OSC commands and sends them to the buttplug device"""
    print_buttplug("listening for commands from oscbridge")
    while True:
        # get a command item from the queue
        device_command = await q_listen.get()
        try:
            if bpclient.connector.connected:
                await device_probe(device_command, bpclient)
            else:
                print_buttplug(f"Client disconnected from Intiface desktop.")
                del device_command
                raise ConnectionError
        except ConnectionError:
            del device_command
            print_buttplug(f"Client disconnected from Interface desktop.")
            break
        finally:
            # clear the task from the queue (leaks memory really fast if it's not cleared).
            q_listen.task_done()


async def clear_queue(q: janus.AsyncQueue[Any]) -> None:
    """sync/async janus queue doesn't have a clear method, so we're geting all items to clear it manually."""
    for _ in range(q.qsize()):
        await q.get()


async def connected_client(bp_manager: OSCButtplugManager) -> ButtplugClient:
    """Returns a configured and connected buttplug client. Loops until a connection is made."""
    while True:
        try:
            # clear the queue commands so that it won't hold old commands while we can't send them to Interface
            await clear_queue(bp_manager.get_queue().async_q)
            print_buttplug("Starting the configuration to connect to Interface")
            """ We setup a client object to talk with Interface and it's connection"""
            client = ButtplugClient(bp_manager.get_client_name())
            ws = bp_manager.get_web_sockets()
            # edited websockets connector that will set itself as disconnected when the websockets connection drops.
            connector = D10ButtplugClientWebsocketConnector(ws)
            """Handler functions to catch when a device connects and disconnects from the server"""
            client.device_added_handler += device_added
            client.device_removed_handler += device_removed
            """Try to connect to the server"""
            print_buttplug("Trying to  connect to  Interface server")
            await client.connect(connector)
            print_buttplug("Could connect to  Interface server")
            return client
        except ButtplugClientConnectorError as e:
            print_buttplug(f"Could not connect to Interface server, retrying in 1s :  {e}")
            await asyncio.sleep(1)


async def run_client_task(client: ButtplugClient, q_in_l: janus.AsyncQueue[Any]) -> None:
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
        await client.stop_scanning()
        await client.disconnect()
    except ButtplugClientConnectorError as e:
        print_buttplug_warning(e.message)
        return


async def run_osc_buttplug(osc_manager: OSCServerManager) -> None:
    """
    Creates tasks to read the incoming queue commands and sends them to the buttplug server
    The tasks will try to reconnect to the Buttplug server until a connection is made, and after it was dropped.
    It will also ask the buttplug server to rescan devices if a command asks for a device not currently connected.
    """
    print_buttplug("Starting Osc to buttplug")
    # run the client/connector in a looop to reset themselves if the connetion is dropped.
    # this should prevent relaunching the full script if the ws connection is dropped
    # Queque with two sides, Async and Sync, used to comunicate with the osc server
    try:
        que_buttplug: janus.Queue[Any] = janus.Queue(20)
        # manager object that will keep track of the configuration and some usefull objects
        bp_manager = osc_d10.osc_buttplug.osc_buttplug_manager.OSCButtplugManager(que_buttplug)
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

