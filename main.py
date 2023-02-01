import asyncio

import myclasses
import osc_d10
from osc_d10.osc import osc_server_manager
from osc_d10.osc.osc_process import run_process
from osc_d10.osc_buttplug import osc_buttplug

from osc_d10.tools.console_colors import bcolors


def print_main(msg) -> None:
    print(f"{bcolors.HEADER} Main: {bcolors.ENDC} {msg} ")


def print_main_warning(msg) -> None:
    print(f"{bcolors.WARNING} {msg} {bcolors.ENDC}")


async def cancel_me(n_tasks) -> None:
    if n_tasks != 0:
        print_main(f'Running active task/s : {n_tasks}')
    else:
        print_main(f'No tasks to run, shutting down')
        return
    try:
        await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass


async def main() -> None:
    # reading the main configuration file
    config = myclasses.MainData()
    if not config.mainconfig:
        print_main_warning("Mainconfig.json has errors or can't be accessed, shutting down.")
        return
    # get the current running loop to start all tasks inside the same loop.
    loop = asyncio.get_running_loop()
    # number of tasks that will be running
    n_tasks = 0
    task_objects = list()
    try:
        if config.mainconfig["OSCBridge"]:
            """ 
                bridge will be the OSC server listening for commands
                the osc server is not async, so we run it inside a separate thread/executor.
                and get info back with a sync/async janus.Queue 
            """
            osc_manager = osc_server_manager.OSCServerManager(config.mainconfig)
            osc_bridge = loop.run_in_executor(None, osc_d10.osc.osc_server.run_osc_bridge, osc_manager)
            n_tasks += 1
            # OSCprocess async side
            if config.mainconfig["OSCProcess"]:
                """Process task that will get OSC commands"""
                task_osc_process = asyncio.create_task(osc_d10.osc.osc_process.run_process(osc_manager),
                                                       name="OSCProcess")
                task_objects.append(task_osc_process)
                n_tasks += 1
        else:
            print_main_warning(
                "Skipping OSCBridge, and OSCToButtplug, OSCBridge = true to enable it in Mainconfig.json")
        if config.mainconfig["OSCtoButtplug"]:
            # osctobutplug will be the buttplug client/connector to talk to Intiface and control devices.
            task_btplug = asyncio.create_task(osc_d10.osc_buttplug.osc_buttplug.run_osc_buttplug(osc_manager),
                                              name="OSCtoButtplug")
            task_objects.append(task_btplug)
            n_tasks += 1

        else:
            print_main_warning(
                  "Skipping OSCToButtplug, OSCtoButtplug = true to enable it in Mainconfig.json")
        # dummy task to keep the main loop running
        task_dummy = asyncio.create_task(cancel_me(n_tasks))
        task_objects.append(task_dummy)
        # check the states of the tasks as they finish
        try:
            done, pending = await asyncio.wait(
                task_objects,
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
                except ValueError as ve:
                    print(f"valueError : {ve}")
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
    except Exception as e:
        print(f"{bcolors.WARNING} Program closed....{e} {bcolors.ENDC}")
