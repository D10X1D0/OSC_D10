import asyncio

import janus
from buttplug.client import ButtplugClient, ButtplugClientWebsocketConnector, ButtplugClientConnectorError, \
    ButtplugClientDevice

import myclasses
from printcolors import bcolors

def printbpcoms(text) -> None:
    msg = bcolors.OKCYAN + "btcoms : " + bcolors.ENDC + str(text)
    print(msg)


async def device_added_task(dev: ButtplugClientDevice) -> None:
    # Ok, so we got a new device in! Neat!
    #
    # First off, we'll print the name of the devices, and its allowed messages.
    printbpcoms("Device Added: {}".format(dev.name))
    printbpcoms(dev.allowed_messages.keys())

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
        printbpcoms("Device bibrates and has " + str(dev.allowed_messages["VibrateCmd"].feature_count) + " motors")
        # If we see that "VibrateCmd" is an allowed message, it means the
        # device can vibrate. We can call send_vibrate_cmd on the device and
        # it'll tell the server to make the device start vibrating.
        """
        await dev.send_vibrate_cmd(0.5)
        # We let it vibrate at 50% speed for 1 second, then we stop it.
        "await asyncio.sleep(1)
        # We can use send_stop_device_cmd to stop the device from vibrating, as
        # well as anything else it's doing. If the device was vibrating AND
        # rotating, we could use send_vibrate_cmd(0) to just stop the
        # vibration.
        "await dev.send_stop_device_cmd()
        """

        # await dev.send_vibrate_cmd([0,0.2])
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
        printbpcoms("device rotates, not implemented to control jet")
        """we make the device rotate at 50% speed clockwise and then counterclockwise"""
        """
        await dev.send_rotate_cmd(0.5, True)
        await asyncio.sleep(1)
        await dev.send_rotate_cmd(0.0, True)
        await asyncio.sleep(1)
        await dev.send_rotate_cmd(0.5, False)
        await asyncio.sleep(1)
        await dev.send_rotate_cmd(0.0, True)
        """


def device_added(emitter, dev: ButtplugClientDevice) -> None:
    asyncio.create_task(device_added_task(dev))


def device_removed(emitter, dev: ButtplugClientDevice) -> None:
    printbpcoms("Device removed: " + str(dev))

async def vibratedevice(device: ButtplugClientDevice, items):
    # await device.send_vibrate_cmd({m: value})
    name = items[0][0]
    motorlist = items[0][1][1]
    value = float(items[1])
    command = dict()
    if isinstance(motorlist, str):
        # I'ts one number, indicating all motors should be set
        # I found that my device didn't vibrate all motors sending just a float, so I'm setting all motors.
        nmotors = device.allowed_messages["VibrateCmd"].feature_count
        try:
            i = 0
            while i < nmotors:
                command[i] = value
                i += 1
        except Exception as e:
            printbpcoms("Exception i_" + str(e))
        # printbpcoms("single comand : " + str(command))
    else:
        # It's a list of numbers, indicating all motors to be set
        try:
            for i in motorlist:
                command[i] = value
        except Exception as e:
            printbpcoms("Error : " + str(e))
    try:
        # printbpcoms("Command : " + str(command) + " : " + str(type(command)))
        printbpcoms("Vibrating : " + str(device.name) + " : motor/s : " + str(motorlist) + " : speed :" + str(value))
        await device.send_vibrate_cmd(command)
    except Exception as e :
        printbpcoms("device error, disconnected? " + str(e))

async def deviceprobe(item, dev: ButtplugClient) -> None:
    # look for a toy that matches the name passed, and if it is present execute the command
    name = item[0][0]
    command = item[0][1][0]
    try:
        if len(dev.devices) == 0:
            printbpcoms(" Device not connected : " + name)
            # we tell the server to stop and scan again.
            # this will help not to do a full reset after a dropped bt connection
            await dev.stop_scanning()
            await dev.start_scanning()
        else:
            for key in dev.devices.keys():
                if dev.devices[key].name == name:
                    # print("device is connected")
                    # print(command)
                    device = dev.devices[key]
                    if command == 'VibrateCmd':
                        await vibratedevice(device, item)
                    elif command == 'RotateCmd':
                        value = item[1]
                        printbpcoms("device rotation")
                        printbpcoms(value)
                        printbpcoms("to do, not implemented jet")
                else:
                    printbpcoms("no device found to match this name : " + name)
    except RuntimeError as e:
        printbpcoms("Device error " + str(e))
    except Exception as e:
        printbpcoms("Device error x " + str(e))

async def listenqueloop(q_listen: janus.AsyncQueue[int], dev: ButtplugClient) -> None:
    printbpcoms("listening for commands from oscbridge")
    while True:
        item = await q_listen.get()
        # printbpcoms("Reading....")
        # printbpcoms(item)
        try:
            await deviceprobe(item, dev)
        except Exception:
            print("yes1")


async def listenque(q_listen: janus.AsyncQueue[int], dev: ButtplugClient) -> None:
    try:
        await listenqueloop(q_listen, dev)
    except Exception:
        print("yes")


async def work(mainconfig : myclasses.MainData, q_in_l: janus.AsyncQueue[int], loop: asyncio.events) -> None:
    printbpcoms("Starging work")
    while True:
        try:
            printbpcoms("Starging the configuration to connect to Interface")
            """ We setup a client object to talk with Interface and it's connection"""
            client = ButtplugClient("OSC_D10")
            ws = "ws://" + str(mainconfig.mainconfig["InterfaceWS"])
            connector = ButtplugClientWebsocketConnector(ws)
            """Handler functions to catch when a device connects and disconnects from the server"""
            client.device_added_handler += device_added
            client.device_removed_handler += device_removed
            """Try to connect to the server"""
            printbpcoms("Trying to  connect to  Interface server")
            await client.connect(connector)
            printbpcoms("Could connect to  Interface server")
            break
        except ButtplugClientConnectorError:
            printbpcoms("Could not connect to Interface server, retrying in 1s")
            await asyncio.sleep(1)

    try:
        await client.start_scanning()
        """Start the queque listening"""
        task2 = asyncio.create_task(listenque(q_in_l, client))
        await task2

        """When the task stops we stop the server scanning for devices and close the connection"""
        printbpcoms("Exiting butplugcoms")
        await client.stop_scanning()
        await client.disconnect()
    except RuntimeError as e:
        printbpcoms("something went wrong" + str(e))
    except Exception as e:
        printbpcoms("something went wrong" + str(e))
    printbpcoms("work done")

