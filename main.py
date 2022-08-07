import asyncio
from typing import Any
import janus
import myclasses
import oscprocess
import oscserver
import osctobutplug
from printcolors import bcolors


def printmain(msg):
    print(f"{bcolors.HEADER} Main: {bcolors.ENDC} {msg} ")


def printmainwarning(msg):
    print(f"{bcolors.WARNING} {msg} {bcolors.ENDC}")


async def cancel_me(ntasks):
    if ntasks != 0:
        printmain(f'Running active task/s : {ntasks}')
    else:
        printmain(f'No tasks to run, shutting down')
        exit()
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
    qproc: janus.Queue[Any] = janus.Queue()
    qstate: janus.Queue[Any] = janus.Queue()
    # Queue for comunicating back to osctobutplug
    qbp: janus.Queue[Any] = janus.Queue()
    loop = asyncio.get_running_loop()
    #number of tasks that will be running
    ntasks = 0
    taskobjectlist = list()
    try:
        if config.mainconfig["OSCBridge"] or config.mainconfig["OSCPass"] or config.mainconfig["OSCprocess"]:
            """ 
                bridge will be the OSC server listening for commands
                the osc server is not async, so we run it inside a separate thread/executor.
                and get info back with a sync/async janus.Queue 
            """
            bridge = loop.run_in_executor(None, oscserver.oscbridge, config, qstate.sync_q, qbp.sync_q, qproc.sync_q)
            ntasks += 1
            # OSCprocess async side
            if config.mainconfig["OSCprocess"]:
                taskoscp = asyncio.create_task(oscprocess.process(qproc.async_q, config, qstate.async_q), name="OSCprocess")
                taskobjectlist.append(taskoscp)
                ntasks += 1
        else:
            printmainwarning(
                "Skipping OSCBridge, and OSCToButtplug, OSCBridge = true to enable it in Mainconfig.json")
        if config.mainconfig["OSCtoButtplug"]:
            # osctobutplug will be the buttplug client/connector to talk to Interface and control devices.
            # loop.create_task(osctobutplug.butplugcoms, config, qBP.async_q, qstate.async_q)
            taskbtplug = asyncio.create_task(osctobutplug.work(config, qbp.async_q), name="OSCtoButtplug")
            taskobjectlist.append(taskbtplug)
            ntasks += 1
            # asyncio.create_task(osctobutplug.work(config, qBP.async_q, loop))
            # osctobutplug.butplugcoms(config, qBP.async_q, qstate.async_q)
        else:
            printmainwarning(
                  "Skipping OSCToButtplug, OSCtoButtplug = true to enable it in Mainconfig.json")
        # dummy task to keep the main loop running
        taskdummy = asyncio.create_task(cancel_me(ntasks))
        taskobjectlist.append(taskdummy)
        # check the states of the tasks as they finish
        try:
            done, pending = await asyncio.wait(
                taskobjectlist,
                return_when=asyncio.ALL_COMPLETED
            )
            for task in done:
                name = task.get_name()
                print(f"Done {name}")
                exception = task.exception()
                if isinstance(exception, Exception):
                    print(f"{name} threw {exception}")
                try:
                    result = task.result()
                    print(f"{name} returned {result}")
                except ValueError as e:
                    print(f"valueError : {e}")
        except Exception as e:
            print(f"Outer Exception {e}")
    except Exception as exc:
        print(f"Error in Main: {exc}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"{bcolors.WARNING} Program closed....{ bcolors.ENDC}")
    except RuntimeError as e:
        print(f"{bcolors.WARNING} All shut down, error/s happened {bcolors.ENDC} {e}")
    except Exception:
        print(f"{bcolors.WARNING} Program closed....{bcolors.ENDC}")
