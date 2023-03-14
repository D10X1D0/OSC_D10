import janus

import osc_d10.osc.osc_server

from osc_d10.osc.osc_server_manager import OSCServerManager
from NoGit.buttplugio.osc_buttplug_manager import OSCButtplugManager, BpDevCommand
from osc_d10.tools.console_colors import bcolors
from osc_d10.tools.io_files import read_json_file


def print_config(text):
    print(f"{bcolors.OKCYAN} OscButtplugSetup {bcolors.ENDC} {text}")


def run_initial_setup(osc_manager: OSCServerManager, bp_manager: OSCButtplugManager) -> None:
    map_dispatcher_buttplug(osc_manager, bp_manager.get_queue().sync_q)


def read_mappings() -> list:
    # default contents to help a new install
    # OSCparameter, "device name", [command]
    # OSCparameter, "device name", [command, motor index]
    # OSCparameter, "device name", [command, rotation direction]  "allcw" clockwise "allccw" counterclockwise
    # OSCparameter, "device name", [command, [rotor index, [rotation direction]]
    #                                                       "true" clockwise, "false" counterclockwise
    parameter_default = [
        "/avatar/parameters/pContact1", "Lovense Edge", ["Vibrate", "all"],
        "/avatar/parameters/pContact2", "Lovense Edge", ["Vibrate", [0]],
        "/avatar/parameters/stop0", "Lovense Edge", ["Stop"],
        "/avatar/parameters/rotatea", "fake rotating device", ["Rotate", "allcw"],
        "/avatar/parameters/rotateb", "fake rotating device", ["Rotate", "allccw"],
        "/avatar/parameters/rotatec", "fake rotating device", ["Rotate", [0, True]],
        "/avatar/parameters/rotated", "fake rotating device", ["Rotate", [[2, False], [7, True]]],
        "/avatar/parameters/Mouth", "XBox (XInput) Compatible Gamepad 1", ["Vibrate", "all"],
        "/avatar/parameters/Test2", "XBox (XInput) Compatible Gamepad 1", ["Vibrate", [0]],
        "/avatar/parameters/Test3", "XBox (XInput) Compatible Gamepad 1", ["Vibrate", [1]]
    ]
    data = read_json_file("OscToButtplugConfiguration.json", parameter_default)
    return data


def command_handler_buttplug(osc_address, args, osc_value) -> None:
    """Command handler for OSCtobuttplug, sends the OSC data using a queue"""
    osc_d10.osc.osc_server.send_to_que(args[0][0], args[0][1], osc_value)


def map_dispatcher_buttplug(osc_manager: OSCServerManager, queue: janus.SyncQueue) -> None:
    """Reads OSCtoButtplug commands configuration files and populates the server Dispatcher"""
    commands = read_mappings()
    # the mapping is stored in sets of 3
    if not commands:
        print_config("Could not read any commands to dispatch for butplug")
        return

    if not len(commands) % 3 == 0:
        print_config(bcolors.FAIL +
                     "The number of entry's in OSCtoButtplug -> parameterMaping.json is not multiple of 3"
                     + bcolors.ENDC)
        return

    print_config(f"Setting nº of mappings for OSCtoButtplug: {len(commands) // 3}")
    for i in range(len(commands) // 3):
        if i != 0:
            a = i * 3
        else:
            a = i
        try:
            osc_addr = commands[a]
            dev_name = commands[a + 1]
            command = commands[a + 2]
            command_name = commands[a + 2][0]
            if len(commands[a + 2]) == 2:
                command_data = commands[a + 2][1]
            else:
                command_data = ''
            # replacing the command name str(), for it's assigned value, if its
            command[0] = BpDevCommand[command_name].value
            # registering command in internal valid list
            osc_manager.map_osc(osc_addr, command_handler_buttplug, (dev_name, command), queue)
            print_config(f"{osc_addr} _ mapped to_ {dev_name} {command_name} {command_data}")
        except ValueError:
            print_config(f" Invalid command for osctobutplug in configuration, skipping it. "
                             f"{command} {command_name}")
        except Exception as e:
            print_config(f" This command could not be mapped to OSCtoButtplug : {command} : error {e}")

