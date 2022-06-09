import asyncio
import janus
import myclasses
import oscprocess
import oscserver
import osctobutplug
from printcolors import bcolors


def printmain(msg):
    print(bcolors.HEADER + "Main: " + bcolors.ENDC + msg)


def printmainwarning(msg):
    print(bcolors.WARNING + msg + bcolors.ENDC)


async def cancel_me():
    printmain('cancel_me(): before sleep')

    try:
        await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass


async def main():
    # reading the main configuration file
    config = myclasses.MainData
    if not config.mainconfig:
        printmainwarning("Mainconfig.json has errors or can't be accessed, shutting down.")
        exit()
    # A async/sync queque to send the commands from the sync osc server thread to async buttplug thread
    # Queue for oscprocess
    qproc: janus.Queue[int] = janus.Queue()
    qstate: janus.Queue[int] = janus.Queue()
    # Queue for comunicating back to osctobutplug
    qbp: janus.Queue[int] = janus.Queue()
    loop = asyncio.get_running_loop()
    try:
        if config.mainconfig["OSCBridge"] or config.mainconfig["OSCPass"] or config.mainconfig["OSCprocess"]:
            """ 
                t1 will be the OSC server listening for commands
                the osc server is not async, so we run it inside a separate thread/executor.
                and get info back with a sync/async janus.Queue 
            """
            # t1 = threading.Thread(target=oscserver.oscbridge, args=(config, qstate.sync_q, qsinc.sync_q))
            # t1.start()
            bridge = loop.run_in_executor(None, oscserver.oscbridge, config, qstate.sync_q, qbp.sync_q, qproc.sync_q)
            # OSCprocess async side
            if config.mainconfig["OSCprocess"]:
                loop.create_task(oscprocess.process(qproc.async_q, config, loop), name="OSCprocess")
        else:
            printmainwarning(
                "Skipping OSCBridge, and OSCToButtplug, OSCBridge = true to enable it in Mainconfig.json")
        if config.mainconfig["OSCtoButtplug"]:
            # osctobutplug will be the buttplug client/connector to talk to Interface and control devices.
            # loop.create_task(osctobutplug.butplugcoms, config, qBP.async_q, qstate.async_q)
            taskwork = loop.create_task(osctobutplug.work(config, qbp.async_q, loop), name="OSCtoButtplug")
            # asyncio.create_task(osctobutplug.work(config, qBP.async_q, loop))
            # osctobutplug.butplugcoms(config, qBP.async_q, qstate.async_q)
        else:
            printmainwarning(
                  "Skipping OSCToButtplug, OSCtoButtplug = true to enable it in Mainconfig.json")
        # dummy task to keep the main loop running
        task = asyncio.create_task(cancel_me())
        try:
            await task
        except asyncio.CancelledError:
            pass
    except Exception as exc:
        print("Error : " + str(e))
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print(bcolors.WARNING + "Program closed...." + bcolors.ENDC)
except RuntimeError as e:
    print(bcolors.WARNING + "All shut down, error/s happened" + bcolors.ENDC + str(e))
except Exception:
    print(bcolors.WARNING + "Program closed...." + bcolors.ENDC)
