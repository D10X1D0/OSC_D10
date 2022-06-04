import asyncio
import json
import threading
import janus
import oscserver
import osctobutplug
from printcolors import bcolors


Mainconfig = {
        "OSCBridge": False,
        "OSCBListenIP": "127.0.0.1", "OSCBListenPort": 9000,
        "OSCPass": False,
        "OSCSendIP": "127.0.0.1", "OSCSendPort": 9001,
        "OSCtoButtplug": False,
        "InterfaceWS": "127.0.0.1:12345"
    }


def createdefaultmainconfig() -> None:
    with open('Mainconfig.json', 'w') as f:
        json.dump(Mainconfig, f)


def readmainconfig():
    try:
        with open('Mainconfig.json') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        createdefaultmainconfig()
        with open('Mainconfig.json') as f:
            data = json.load(f)
            return data
    except Exception as _e:
        printmainwarning("Could not load or create a new Mainconfig.json")
        printmainwarning("Exception : " + str(_e))
        return False


def printmain(msg):
    print(bcolors.HEADER + "Main:" + bcolors.ENDC + msg)


def printmainwarning(msg):
    print(bcolors.WARNING + msg + bcolors.ENDC)


async def main():
    # reading the main configuration file
    config = readmainconfig()
    if not config:
        printmainwarning("Mainconfig.json has errors or can't be accessed, shutting down.")
        exit()
    # A async/sync queque to send the commands from the sync osc server thread to async buttplug thread
    # q: janus.Queue[int] = janus.Queue()
    qstate: janus.Queue[int] = janus.Queue()
    qsinc: janus.Queue[int] = janus.Queue()
    if config["OSCBridge"] or config["OSCPass"]:
        """ 
            t1 will be the OSC server listening for commands
            the osc server is not async, so we run it inside a separate thread.
            and get info back with a sync/async janus.Queue 
        """
        t1 = threading.Thread(target=oscserver.oscbridge, args=(config, qstate.sync_q, qsinc.sync_q))
        t1.start()
    else:
        printmainwarning(
            "Skipping OSCBridge, and OSCToButtplug, OSCBridge = true to enable it in Mainconfig.json")
    if config["OSCtoButtplug"]:
        # osctobutplug will be the buttplug client/connector to talk to Interface and control devices.
        await osctobutplug.butplugcoms(config, qsinc.async_q, qstate.async_q)
    else:
        printmainwarning(
              "Skipping OSCToButtplug, OSCtoButtplug = true to enable it in Mainconfig.json")
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print(bcolors.WARNING + "Program closed...." + bcolors.ENDC)
except RuntimeError as e:
    print(bcolors.WARNING + "All shut down, error/s happened" + bcolors.ENDC + str(e))
