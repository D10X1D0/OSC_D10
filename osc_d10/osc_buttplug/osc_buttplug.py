from osc_d10.osc.osc_server_manager import OSCServerManager
from osc_d10.osc_buttplug.osc_buttplug_configuration import OSCButtplugConfiguration
from osc_d10.osc_buttplug.osc_buttplug_manager import OSCButtplugManager
from osc_d10.tools.console_colors import bcolors


def print_buttplug(text) -> None:
    """helper fuction to print with pretty colors the name and message to the console"""
    msg = f"{bcolors.OKCYAN} btcoms : {bcolors.ENDC} {text}"
    print(msg)


def print_buttplug_warning(text) -> None:
    """helper fuction to print with pretty colors the name and message to the console"""
    msg = f"{bcolors.WARNING} btcoms : {bcolors.ENDC} {text}"
    print(msg)


async def run_osc_to_buttplug(osc_manager: OSCServerManager) -> None:
    """Creates, configures and starts buttplug connections and device commands"""
    print_buttplug("Starting OSC to Buttplug")
    bp_config = OSCButtplugConfiguration()
    bp_manager = OSCButtplugManager(bp_config.get_client_name(), bp_config.get_web_sockets())
    print_buttplug("Exiting OSC to Buttplug")
