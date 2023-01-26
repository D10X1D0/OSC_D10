import asyncio

from pythonosc.udp_client import SimpleUDPClient

from osc_d10.osc.osc_server import send_osc
from osc_d10.osc.osc_server_manager import OSCServerManager
from osc_d10.tools.console_colors import bcolors
from osc_d10.tools.io_files import read_json_file


def print_process_setup(msg):
    print(f"{bcolors.HEADER2} OSCProcSetup : {bcolors.ENDC} {msg}")


def print_warning_process_setup(msg):
    print_process_setup(f"{bcolors.WARNING} OSCProcSetup : {bcolors.ENDC} {msg}")


def read_mappings_process() -> list:
    """Returns the mappings for OSC Process and creates a configuration file"""
    # default contents of processMaping
    process_mapping_default = [
        "/avatar/parameters/Testa", "pulse", [30, 1],
        "/avatar/parameters/Testa", "pulse", [15, 0],
        "/avatar/parameters/Testc", "pulse", [10, False],
        "/avatar/parameters/Testc", "pulse", [15, True],
        "/avatar/parameters/Testd", "respond", [1, "/avatar/parameters/Testda"]
    ]
    data = read_json_file("OSCProcessMapping.json", process_mapping_default)
    return data


def command_handler_respond(command, args, value) -> None:
    """Command handler for OSCProcess, re-sends data through OSC """
    # Value to send args[0][0][0], address to send it to args[0][0][1]
    # client = args[0][0][0]
    # osc_address = args[0][0][1][1]
    # value_to_send = args[0][0][1][0]
    send_osc(args[0][0][0], args[0][0][1][1], args[0][0][1][0])


def populate_dispatcher_respond(manager: OSCServerManager, mappings: tuple) -> int:
    """Reads oscprocess commands configuration files and populates the server Dispatcher"""
    items = 0
    commands = mappings
    # populating the dispatcher with commands to be custom processed
    if not commands:
        print_warning_process_setup("Could not read any commands to dispatch for process")
        return items
    command_length = len(commands)
    if command_length % 3 != 0:
        print_warning_process_setup("The number of entrys in OSCprocess -> procesMaping.json is not multiple of 2")
        return items

    print_process_setup(f"Setting nº of mappings for OSCprocess: {command_length // 3}")
    for i in range(command_length // 3):
        if i != 0:
            # any iteration past the first one
            a = i * 3
        else:
            # first iteration
            a = i
        proces = commands[a + 1]
        if proces == "respond":
            manager.map_osc(commands[a], command_handler_respond, (manager.client, commands[a + 2]))
            print_process_setup(f"{commands[a]} _mapped to_ {proces} _ {commands[a + 2]}")
            items = items + 1
    return items


async def pulse_task(client: SimpleUDPClient, osc_address: str, time: float, value: [any]):
    """Task to run osc messages forever with a delay """
    while True:
        # wait the delay
        await asyncio.sleep(time)
        # send the message
        send_osc(client, osc_address, value)
        print(f"{bcolors.HEADER2} OSCProcess Pulse : {bcolors.ENDC} {osc_address} {value}")


def populate_dispatcher_pulse(manager: OSCServerManager, mappings: tuple) -> int:
    """Creates and starts running pulse takss from the configured commands."""
    print_process_setup("populate_dispatcher_pulse")
    for i in range(len(mappings) // 3):
        if i != 0:
            # any iteration past the first one
            a = i * 3
        else:
            # first iteration
            a = i
        task_name = mappings[a + 1]
        if task_name != "pulse":
            continue

        address = mappings[a]
        time = mappings[a + 2][0]
        value = mappings[a + 2][1]
        if float(time) < 0.1:
            print_process_setup(f"{bcolors.FAIL}pulse too fast, faster than 0.1s,skipping it timing: {time} {bcolors.FAIL}")
            continue

        print_process_setup(f"registering pulse task {i}")
        asyncio.create_task(pulse_task(manager.client, address, time, value))
        print_process_setup(f"{address}__{task_name}__{value}")
