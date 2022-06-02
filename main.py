import asyncio
import json
import threading

import janus

import oscserver
import osctobutplug
from printcolors import bcolors


def createdefaultmainconfig() -> None:
    data = {
        "OSClistener": False, "OSCtoButtplug": False
    }
    with open('Mainconfig.json', 'w') as f:
        # print(str(data))
        json.dump(data, f)
        # print("Reading back the parametermaping to a jsonfile")


def readmainconfig(prefix):
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
        print(prefix + "Could not load or create a new Mainconfig.json")
        print(prefix + "Exception : " + str(e))
        return False


async def main():
    # reading the main configuration file
    config = readmainconfig("main")
    # A async/sync queque to send the commands from the sync osc server thread to async buttplug thread
    q: janus.Queue[int] = janus.Queue()
    qstate: janus.Queue[int] = janus.Queue()
    qsinc: janus.Queue[int] = janus.Queue()
    if config["OSCBridge"]:
        """ 
            t1 will be the OSC server listening for commands
            the osc server is not async, so we run it inside a separate thread.
            and get info back with a sync/async janus.Queue 
        """
        t1 = threading.Thread(target=oscserver.oscbridge, args=(config, qstate.sync_q, qsinc.sync_q))
        t1.start()
    else:
        print(bcolors.WARNING +
              "Skipping OSCBridge, and OSCToButtplug, OSCBridge = true to enable it in Mainconfig.json"
              + bcolors.ENDC)
    if config["OSCtoButtplug"]:
        # osctobutplug will be the buttplug client/connector to talk to Interface and control devices.
        await osctobutplug.butplugcoms(config, qsinc.async_q, qstate.async_q)
    else:
        print(bcolors.WARNING +
              "Skipping OSCToButtplug, OSCtoButtplug = true to enable it in Mainconfig.json"
              + bcolors.ENDC)
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print(bcolors.WARNING + "Program closed...." + bcolors.ENDC)
except RuntimeError as e:
    print(bcolors.WARNING + "All shut down, error/s happened" + bcolors.ENDC + str(e))
