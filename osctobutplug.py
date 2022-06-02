import asyncio

import janus
from buttplug.client import ButtplugClient, ButtplugClientWebsocketConnector, ButtplugClientConnectorError, \
    ButtplugClientDevice

from printcolors import bcolors


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
    print("Device removed: ", dev)


async def deviceprobe(item, dev: ButtplugClient) -> None:
    # look for a toy that matches the name passed, and if it is present execute the command
    if len(dev.devices) == 0:
        printbpcoms(" Device not connected : ")
    else:
        for key in dev.devices.keys():
            command = item[0][1][0]
            name = item[0][0]
            if dev.devices[key].name == name:
                # print("device is connected")
                # print(command)
                device = dev.devices[key]
                value = item[1]
                if command == 'VibrateCmd':
                    printbpcoms(" Vibrating all motors :" + name + "_at speed_" + str(value))
                    await device.send_vibrate_cmd(value)

                elif command == 'SingleMotorVibrateCmd':
                    m = item[0][1][1]
                    printbpcoms("Vibrating single motor : " + name + "_motor nº_" + str(m) + "_at speed_" + str(value))
                    await device.send_vibrate_cmd({m: value})

                elif command == 'RotateCmd':
                    print("device rotation")
                    print(value)
                    print("to do, not implemented jet")
            else:
                printbpcoms("no device found to match this name : " + name)


async def listenqueloop(q_listen: janus.AsyncQueue[int], dev: ButtplugClient) -> None:
    printbpcoms("listening for commands from oscbridge")
    while True:
        item = await q_listen.get()
        # printbpcoms("Reading....")
        # printbpcoms(item)
        await deviceprobe(item, dev)


async def listenque(q_listen: janus.AsyncQueue[int], dev: ButtplugClient) -> None:
    await listenqueloop(q_listen, dev)


def printbpcoms(text) -> None:
    msg = bcolors.OKCYAN + "btcoms : " + bcolors.ENDC + str(text)
    print(msg)


async def work(mainconfig, q_in_l) -> None:
    while True:
        try:
            """ We setup a client object to talk with Interface and it's connection"""
            client = ButtplugClient("OSC_D10")
            ws = "ws://" + mainconfig["InterfaceWS"]
            connector = ButtplugClientWebsocketConnector(ws)
            """Handler functions to catch when a device connects and disconnects from the server"""
            client.device_added_handler += device_added
            client.device_removed_handler += device_removed
            """Try to connect to the server"""
            await client.connect(connector)
            printbpcoms("Could connect to  Interface server")
            break
        except ButtplugClientConnectorError as e:
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


async def butplugcoms(mainconfig, q_in: janus.AsyncQueue[int], q_state: janus.AsyncQueue[int]) -> None:
    prefix = bcolors.OKCYAN + "btcoms : " + bcolors.ENDC
    printbpcoms("running butplugcoms")
    task = asyncio.create_task(work(mainconfig, q_in))
    await task
    printbpcoms("Finished sever work")
