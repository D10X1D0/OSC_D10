import asyncio

import janus
import sys

from buttplug.client import ButtplugClient, ButtplugClientConnectorError, ButtplugClientDevice
from buttplug.core import ButtplugDeviceError
from D10ButtplugClientWebsocketConnector import D10ButtplugClientWebsocketConnector

import myclasses
from printcolors import bcolors


def printbpcoms(text) -> None:
    msg = f"{bcolors.OKCYAN} btcoms : {bcolors.ENDC} {text}"
    print(msg)


def printbpcomswarning(text) -> None:
    msg = f"{bcolors.WARNING} btcoms : {bcolors.ENDC} {text}"
    printbpcoms(msg)


async def devicedump(dev: ButtplugClientDevice) -> None:
    dname = dev.name
    try:
        myclasses.tryreadjson(f"{dname}.json")
        printbpcoms(f"Dump file already exists, skipping creating it. {dev.name}")
    except FileNotFoundError as e:
        printbpcoms(f"Dump file does not exist, creating it. {dev.name}")
        await serializedevice(dev)
    except Exception as e:
        printbpcoms(f"Error creating a dump file for {dev.name} : {e}")


async def serializedevice(dev: ButtplugClientDevice):
    printbpcoms(f"Creating dump file for {dev.name}")
    data = dict()
    clist = list()
    clistraw = list()
    data['devname'] = str(dev.name)
    for m in dev.allowed_messages:
        try:
            # check if the message is a implemented command and translate it to the OSCtobutplug name.
            bpnamevalue = myclasses.BpDevCommandInterface[str(m)].value
            octobpname = myclasses.BpDevCommand(bpnamevalue).name
            try:
                # check the featurecount and fail if it does not exist for the current command
                nmotors = dev.allowed_messages[str(m)].feature_count
                clist.append({str(octobpname): nmotors})
                clistraw.append({str(m): nmotors})
            except AttributeError as e:
                # the current command does not have .featurecount attribute
                clist.append(str(octobpname))
                clistraw.append(str(m))

        except Exception as e:
            print(sys.exc_info())
            printbpcoms(f"{m} is not implemented in osctobuttplug {e}")
            try:
                # check the featurecount if it has vibrating or rotating motors
                nmotors = dev.allowed_messages[str(m)].feature_count
                clistraw.append({str(m): nmotors})
            except Exception:
                clistraw.append(str(m))
                pass
    data['commands'] = clist
    data['buttplugraw'] = clistraw
    myclasses.createdefaultfile(f"{dev.name}.json", data)


async def device_added_task(dev: ButtplugClientDevice) -> None:
    # Ok, so we got a new device in! Neat!
    #
    # First off, we'll print the name of the devices, and its allowed messages.
    printbpcoms("Device Added: {}".format(dev.name))
    printbpcoms(dev.allowed_messages.keys())
    await devicedump(dev)
    # Once we've done that, we can send some commands to the device, depending
    # on what it can do. As of the current version I'm writing this for
    # (v0.0.3), all the client can send to devices are generic messages.
    # Specifically:
    #
    # - VibrateCmd
    # - RotateCmd
    # - LinearCmd
    #
    # However, this is good enough to still do a lot of stuff.
    #
    # These capabilities are held in the "messages" member of the
    # ButtplugClientDevice.

    if "VibrateCmd" in dev.allowed_messages.keys():
        printbpcoms(f"Device bibrates and has {dev.allowed_messages['VibrateCmd'].feature_count} motors")

    if "LinearCmd" in dev.allowed_messages.keys():
        printbpcoms("Device has linear motion, not implemented to control jet")
        # If we see that "LinearCmd" is an allowed message, it means the device
        # can move back and forth. We can call send_linear_cmd on the device
        # and it'll tell the server to make the device move to 90% of the
        # maximum position over 1 second (1000ms).
        """
        await dev.send_linear_cmd((1000, 0.9))
        # We wait 1 second for the move, then we move it back to the 0%
        # position.
        "await asyncio.sleep(1)
        "await dev.send_linear_cmd((1000, 0))
        """

    if "RotateCmd" in dev.allowed_messages.keys():
        printbpcoms("device rotates, not tested yet.")


def device_added(emitter, dev: ButtplugClientDevice) -> None:
    asyncio.create_task(device_added_task(dev))


def device_removed(emitter, dev: ButtplugClientDevice) -> None:
    printbpcoms(f"Device removed: {dev}")


async def vibratedevice(device: ButtplugClientDevice, items) -> None:
    # await device.send_vibrate_cmd({m: value})
    name = items[0][0]
    motorlist = items[0][1][1]
    # make sure the value is inside the range 0->1
    try:
        value = max(min(float(items[1]), 1.0), 0.0)
    except Exception as e:
        printbpcoms(f"received a value outside of the valid float range (0.0-> 1.0) : {e}")
        return
    command = dict()
    if isinstance(motorlist, str):
        # I'ts one number, indicating all motors should be set
        # I found that my device didn't vibrate all motors sending just a float after sending a tuple once,
        # so I'm setting all motors.
        nmotors = device.allowed_messages["VibrateCmd"].feature_count
        try:
            for i in range(nmotors):
                command[i] = value
        except Exception as e:
            printbpcoms(f"Exception i_ {e}")
        # printbpcoms(f"single comand : {command}")
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
        # ask the connection loop to retry the connection
        printbpcoms(f"ButtplugClientConnectorError, disconnected? {e}")
        raise ButtplugClientConnectorError(e)
    except Exception as e:
        printbpcoms(f"device error, disconnected? {e}")


async def rotatedevice(device: ButtplugClientDevice, items) -> None:
    try:
        name = items[0][0]
        motorlist = items[0][1][1]
        # make sure the value is inside the range 0->1
        value = max(min(float(items[1]), 1.0), 0.0)
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

    try:
        printbpcoms(f"Rotating : {name} : {command}")
        await device.send_rotate_cmd(command)
    except Exception as e:
        printbpcoms(f"Error trying to rotate device : name {name} : command {command} : error {e}")
        return


async def deviceprobe(item, dev: ButtplugClient) -> None:
    # look for a toy that matches the name passed, and if it is present execute the command
    name = item[0][0]
    command = item[0][1][0]
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
                        await vibratedevice(device, item)
                    elif command == myclasses.BpDevCommand.Rotate.value:
                        await rotatedevice(device, item)
                    elif command == myclasses.BpDevCommand.Stop.value:
                        printbpcoms(f"Stoping : {name}")
                        await dev.devices[key].send_stop_device_cmd()
                else:
                    printbpcoms(f"no device found to match this name : {name} or command : {command}")
    except RuntimeError as e:
        printbpcoms(f"Device error {e}")
    except Exception as e:
        printbpcoms(f"Device error x {e}")


async def listenqueloop(q_listen: janus.AsyncQueue[int], dev: ButtplugClient) -> None:
    printbpcoms("listening for commands from oscbridge")
    while True:
        item = await q_listen.get()
        # printbpcoms("Reading....")
        # printbpcoms(item)
        try:
            if dev.connector.connected:
                await deviceprobe(item, dev)
            else:
                printbpcoms(f"Client disconnected from Interface desktop.")
                raise ConnectionError
        except ConnectionError:
            break
        except Exception as e :
            print(f"listenqueloop error : {e}")


async def listenque(q_listen: janus.AsyncQueue[int], dev: ButtplugClient) -> None:
    try:
        await listenqueloop(q_listen, dev)
    except Exception as e:
        print(f"listenque error : {e}")


async def clearqueue(q: janus.AsyncQueue[int])-> None:
    # this sync/async janus queue doesn't have a clear method, so we're geting all items to clear it manually.
    try:
        x = q.qsize()
        for i in range(x):
            await q.get()
        # printbpcoms(f"q.length {q.unfinished_tasks}")
    except Exception as e:
        printbpcoms(f"error clearing the command queue {e}")
        pass


async def connectedclient(q_in_l: janus.AsyncQueue[int], mainconfig) -> ButtplugClient:
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
            """Try to connect to the server"""
            printbpcoms("Trying to  connect to  Interface server")
            await client.connect(connector)
            printbpcoms("Could connect to  Interface server")
            return client
        except ButtplugClientConnectorError as e:
            printbpcoms(f"Could not connect to Interface server, retrying in 1s :  {e}")
            await asyncio.sleep(1)
        except Exception as e:
            printbpcoms(f"Exception in work : {e}")


async def runclienttask(client, q_in_l: janus.AsyncQueue[int]) -> None:
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

    except Exception as e:
        printbpcoms(f"runclientlop running OSCtobutplug ex {e} {sys.exc_info()}")


async def work(mainconfig : myclasses.MainData, q_in_l: janus.AsyncQueue[int], q_estate: janus.AsyncQueue[int]) -> None:
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
