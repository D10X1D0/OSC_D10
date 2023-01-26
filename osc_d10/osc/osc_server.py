from typing import Any

import janus
import pythonosc.udp_client
from pythonosc import (osc_server, udp_client)


from osc_d10.tools.console_colors import bcolors
from osc_d10.osc.osc_server_manager import OSCServerManager


def send_osc(client: pythonosc.udp_client.SimpleUDPClient, parameter: str, value) -> None:
    """Sends an OSC message using a passed configured client"""
    client.send_message(parameter, value)


def send_to_que(name, qosc: janus.SyncQueue[Any], value) -> None:
    """Sends / puts a list with name/value pairs for OSCtobuttplug to read"""
    # Check that the queue is not full before sending new commands
    if not qosc.full():
        values = (name, value)
        qosc.put(values)
        qosc.join()


def retransmit(cli, param, value) -> None:
    """Command handler for Retransmiting back through OSC"""
    send_osc(cli, param, value)
    print_osc_bridge(f"retransmitting : {param} {value}")


def print_osc_bridge(msg) -> None:
    """Helper function to print with colors"""
    print(f"{bcolors.HEADER} OSCB : {bcolors.ENDC} {msg}")


def print_warning_oscb(msg: str) -> None:
    """Helper function to print with colors"""
    print_osc_bridge(f"{bcolors.WARNING} {msg} {bcolors.ENDC}")


def osc_print_all_debug(address, *args):
    print_osc_bridge(f"Adress {address} arguments : {args}")


def queue_send(queue: janus.SyncQueue[Any], data) -> None:
    """Sends data to the passed queue"""
    if not queue.full():
        queue.put(data)
        queue.join()


def run_osc_bridge(manager: OSCServerManager) -> None:
    """Main function to run OSCBridge, it will load configure and start the OSCserver and OSCclients"""
    try:
        print_osc_bridge("running bridge ")

        if manager.osc_debug:
            # set the default handler if printdebug is true
            print_osc_bridge("setting the osc debug ON")
            manager.default_dispatcher_handler(osc_print_all_debug)

        # Ping a client with a simple message to tell it we're running
        sendclient = udp_client.SimpleUDPClient(manager.client_ip, manager.client_port)
        sendclient.send_message("/OSCBridge", 1)

        # read the server configuration
        server = osc_server.ThreadingOSCUDPServer((manager.server_ip, manager.server_port), manager.dispatcher)
        print_osc_bridge("Serving on {}".format(server.server_address))

        server.serve_forever()
        # Ping a client with a simple message to tell it we're stopping
        sendclient.send_message("/OSCBridge", 0)
    except Exception as e:
        print_warning_oscb(f"Error in the main loop, shuting down {e}")
