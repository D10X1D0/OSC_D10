from osc_d10.osc.osc_process_setup import populate_dispatcher_respond, read_mappings_process, populate_dispatcher_pulse

from osc_d10.osc.osc_server_manager import OSCServerManager
from osc_d10.tools.console_colors import bcolors


def print_process(msg: str) -> None:
    """Helper function to print with colors"""
    print(f"{bcolors.HEADER2} OSCProc : {bcolors.ENDC} {msg}")


def print_process_err(msg: str) -> None:
    """Helper function to print with colors"""
    print_process(f"{bcolors.WARNING} {msg} {bcolors.ENDC}")


def run_respond(manager: OSCServerManager, mappings: tuple) -> None:
    # load the osc commands in the dispatcher and store how many we loaded
    n_commands = populate_dispatcher_respond(manager,mappings)
    if n_commands < 1:
        print_process_err("There were no commands loaded for OSC Process. Turning this part off.")
        return
    print_process(f"Loaded {n_commands} commands for respond.")


def run_pulse(manager: OSCServerManager, mappings: tuple):
    """Configures and runs OSC pulses, repeating messages with a  delay"""
    n_commands = populate_dispatcher_pulse(manager, mappings)


async def run_process(manager: OSCServerManager):
    """configures and starts process taks : pulse, and respond"""
    print_process("Proces task")
    mappings = read_mappings_process()
    run_respond(manager, mappings)
    run_pulse(manager, mappings)

