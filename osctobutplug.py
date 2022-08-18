import asyncio
from typing import Any

import janus
import sys

from buttplug.client import ButtplugClient, ButtplugClientConnectorError, ButtplugClientDevice
from buttplug.core import ButtplugDeviceError
from D10ButtplugClientWebsocketConnector import D10ButtplugClientWebsocketConnector

import myclasses
from printcolors import bcolors


def printbpcoms(text) -> None:
    """helper fuction to print with pretty colors the name and message to the console"""
    msg = f"{bcolors.OKCYAN} btcoms : {bcolors.ENDC} {text}"
    print(msg)


def printbpcomswarning(text) -> None:
    """helper fuction to print with pretty colors the name and message to the console"""
    msg = f"{bcolors.WARNING} btcoms : {bcolors.ENDC} {text}"
    print(msg)


async def devicedump(dev: ButtplugClientDevice, serializeddevice : dict()) -> None:
    """Create a devicename.json file with all it's supported commands"""
    dname = dev.name
    try:
        # Check if the file exists by trying to read it
        myclasses.tryreadjson(f"{dname}.json")
        printbpcoms(f"Dump file already exists, skipping creating it. {dname}")
    except FileNotFoundError:
        printbpcoms(f"Dump file does not exist, creating it. {dname}")
        myclasses.createdefaultfile(f"{dname}.json", serializeddevice)
    except Exception as e:
        printbpcoms(f"Error creating a dump file for {dname} : {e}")


async def serializedevice(dev: ButtplugClientDevice) -> dict():
    """Read and format the buttplug device information into a dict() and print it to a .json file"""
    printbpcoms(f"Creating dump file for {dev.name}")
    # dictionary with devicename, osctobuttplugcomamnds:, buttplug raw commands
    serializabledata = dict()
    # dictionary that will contain the osctobuttplug supported commands
    clist = list()
    # dictionary that will contain all the device's buttplug supported commands.
    clistraw = list()
    # Start the data dictionary with the device name.
    serializabledata['devicename'] = str(dev.name)
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
            bpnamevalue = myclasses.BpDevCommandInterface[str(msg)].value
            # osctobuttplug command name's translated (BpDevCommand(Enum))
            octobpname = myclasses.BpDevCommand(bpnamevalue).name
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

    serializabledata['osctobuttplugcommands'] = clist
    serializabledata['buttplugrawcommands'] = clistraw
    return serializabledata


async def device_added_task(dev: ButtplugClientDevice) -> None:
    """Generates a dict() with the device name and propertys and creates a devicename.json file on disk"""
    printbpcoms("Device Added: {}".format(dev.name))
    # get the serialized device data
    devdata = await serializedevice(dev)
    # Print it to the console
    printbpcoms(devdata)
    # dump it to disk inside a devicename.json file
    await devicedump(dev, devdata)


def device_added(emitter, dev: ButtplugClientDevice) -> None:
    """Callback used by the client when a device is added to the server"""
    asyncio.create_task(device_added_task(dev))


def device_removed(emitter, dev: ButtplugClientDevice) -> None:
    """Callback used by the client when a device is removed from the server"""
    printbpcoms(f"Device removed: {dev}")


async def vibratedevice(device: ButtplugClientDevice, devicecommand) -> None:
    """Ask the buttplug server to vibrate the device motor/s, rounds the speed to be inside 0->1 range"""
    # await device.send_vibrate_cmd({m: value})
    name = devicecommand[0][0]
    motorlist = devicecommand[0][1][1]
    # make sure the value is inside the range 0->1
    value = max(min(float(devicecommand[1]), 1.0), 0.0)
    command = dict()
    if isinstance(motorlist, str):
        # I'ts one number, indicating all motors should be set
        # I found that my device didn't vibrate all motors sending just a float after sending a tuple once,
        # so I'm setting all motors.
        nmotors = device.allowed_messages["VibrateCmd"].feature_count
        for i in range(nmotors):
            command[i] = value

    else:
        # It's a list of numbers, indicating all individual motors to be set
        try:
            for i in motorlist:
                command[i] = value
        except Exception as e:
            printbpcoms(f"Error in vibratedevice : {e}")
    try:
        # printbpcoms(f"Command : {command} : {(type(command))}")
        printbpcoms(f"Vibrating : {device.name} : motor/s : {motorlist} : speed : {value}")
        await device.send_vibrate_cmd(command)
    except ButtplugDeviceError as e:
        printbpcoms(f'configured motor outside of the device range. {e}')
    except ButtplugClientConnectorError as e:
        printbpcoms(f"ButtplugClientConnectorError, disconnected? {e}")
        raise ButtplugClientConnectorError("ButtplugClientConnectorError, disconnected?")


async def rotatedevice(device: ButtplugClientDevice, devicecommand) -> None:
    """Ask the buttplug server to rotate the device motor/s, rounds the speed to be inside 0->1 range"""
    try:
        name = devicecommand[0][0]
        motorlist = devicecommand[0][1][1]
        # make sure the value is inside the range 0->1
        value = max(min(float(devicecommand[1]), 1.0), 0.0)
        command = dict()
    except Exception as e:
        print("Could not read the command to rotatedevice : {e}")
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
            printbpcoms("didn't find the direction to set the rotation: allcw or allccw ")
            exit()
        command = tuple(command)
    elif isinstance(motorlist, list):
        # List of motors and directions
        nmotors = len(motorlist)

        if isinstance(motorlist[0], int):
            # just one motor to set : a Tuple of [float, bool]
            command = motorlist[0], motorlist[1]
            command = tuple(command)
            # printbpcoms(f"Setting one motor {command}")
        elif isinstance(motorlist[0], list):
            # more than one motor to set : a dict of int to Tuple[float, bool]
            command = dict()
            for i in range(nmotors):
                motorindex = motorlist[i]
                command[motorindex[0]] = value, motorindex[1]
            # printbpcoms(f"Setting more than one motor {command}")
        # printbpcoms(f"nmotors : {nmotors}")

    printbpcoms(f"Rotating : {name} : {command}")
    await device.send_rotate_cmd(command)


async def deviceprobe(devicecommand, dev: ButtplugClient) -> None:
    """Sends the incoming command to a buttplug device.
    It will ask the server to scan for devices if the one in the command is not connected.
    """
    # look for a toy that matches the name passed, and if it is present execute the command
    name = devicecommand[0][0]
    command = devicecommand[0][1][0]
    try:
        if len(dev.devices) == 0:
            printbpcoms(f"Device not connected : {name}")
            # we tell the server to stop and scan again.
            # this will help not to do a full reset after a dropped bluetooth connection
            await dev.stop_scanning()
            await dev.start_scanning()
            # test rotating device without connecting one to interface delete me after testing
            # if command == myclasses.BpDevCommand.Rotate.value:
            #    await rotatedevice(dev, item)
        else:
            for key in dev.devices.keys():
                if dev.devices[key].name == name:
                    # print(f"device is connected , command {command}")
                    device = dev.devices[key]
                    if command == myclasses.BpDevCommand.Vibrate.value:
                        await vibratedevice(device, devicecommand)
                    elif command == myclasses.BpDevCommand.Rotate.value:
                        await rotatedevice(device, devicecommand)
                    elif command == myclasses.BpDevCommand.Stop.value:
                        printbpcoms(f"Stoping : {name}")
                        await dev.devices[key].send_stop_device_cmd()
                else:
                    printbpcoms(f"no device found to match this name : {name} or command : {command}")
    except RuntimeError as e:
        printbpcoms(f"Device error {e}")


async def listenqueloop(q_listen: janus.AsyncQueue[Any], bpclient: ButtplugClient) -> None:
    """Loop that reads incoming OSC commands and sends them to the buttplug device"""
    printbpcoms("listening for commands from oscbridge")
    while True:
        # get a command item from the queue
        devicecommand = await q_listen.get()
        try:
            if bpclient.connector.connected:
                await deviceprobe(devicecommand, bpclient)
            else:
                printbpcoms(f"Client disconnected from Interface desktop.")
                raise ConnectionError
        except ConnectionError:
            break


async def listenque(q_listen: janus.AsyncQueue[Any], bpclient: ButtplugClient) -> None:
    """Wrapper for the queue reading loop"""
    await listenqueloop(q_listen, bpclient)


async def clearqueue(q: janus.AsyncQueue[Any]) -> None:
    """sync/async janus queue doesn't have a clear method, so we're geting all items to clear it manually."""
    x = q.qsize()
    for i in range(x):
        await q.get()


async def connectedclient(q_in_l: janus.AsyncQueue[Any], mainconfig) -> ButtplugClient:
    """Returns a configured and connected buttplug client. Loops until a connection is made."""
    while True:
        try:
            # clear the queue commands so that it won't hold old commands while we can't send them to Interface
            await clearqueue(q_in_l)
            printbpcoms("Starting the configuration to connect to Interface")
            """ We setup a client object to talk with Interface and it's connection"""
            client = ButtplugClient("OSC_D10")
            ws = f"ws://{mainconfig.mainconfig['InterfaceWS']}"
            # connector = ButtplugClientWebsocketConnector(ws)
            # edited websockets connector that will set itself as disconnected when the websockets connection drops.
            connector = D10ButtplugClientWebsocketConnector(ws)
            """Handler functions to catch when a device connects and disconnects from the server"""
            client.device_added_handler += device_added
            client.device_removed_handler += device_removed
            state = "client configured, ready to be connected"
            """Try to connect to the server"""
            printbpcoms("Trying to  connect to  Interface server")
            await client.connect(connector)
            printbpcoms("Could connect to  Interface server")
            state = "client connected"
            return client
        except ButtplugClientConnectorError as e:
            printbpcoms(f"Could not connect to Interface server, retrying in 1s :  {e}")
            state = "Disconnected, could not connect"
            await asyncio.sleep(1)


async def runclienttask(client, q_in_l: janus.AsyncQueue[Any]) -> None:
    """Starts the buttplug client scanning and reading the incoming commands from the queue inside a task."""
    try:
        await client.start_scanning()
        """Start the queue listening"""
        task2 = asyncio.create_task(listenque(q_in_l, client), name="oscbplistenque")
        await task2
        """When the task stops we stop the server scanning for devices and close the connection"""
        printbpcoms("Exiting client task")
        await client.stop_scanning()
        await client.disconnect()
    except ButtplugClientConnectorError as e:
        printbpcomswarning(e.message)
        return

    except RuntimeError as e:
        printbpcoms(f"runclientlopg OSCtobutplug re {e} {sys.exc_info()}")


async def work(mainconfig : myclasses.MainData.mainconfig, q_in_l: janus.AsyncQueue[Any]) -> None:
    """
    Creates tasks to read the incoming queue commands and sends them to the buttplug server
    The tasks will try to reconnect to the Buttplug server until a connection is made, and after it was dropped.
    It will also ask the buttplug server to rescan devices if a command asks for a device not currently connected.
    """
    printbpcoms("Starging Osc to butplug")
    # run the client/connector in a looop to reset themselves if the connetion is dropped.
    # this should prevent relaunching the full script if the ws connection is dropped
    while True:
        try:
            # instantiate a new client object from a helper function
            client = await connectedclient(q_in_l, mainconfig)
            # start running the client and listening to messages from OSC
            await runclienttask(client, q_in_l)

        except Exception as e:
            print(f"Exception {e}")
            break
    printbpcoms("OSCToButtplug shutting down.")

