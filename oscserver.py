from typing import Any
import janus
import pythonosc.udp_client
from pythonosc import (osc_server, udp_client, dispatcher)
import myclasses
from printcolors import bcolors


def sendosc(client: pythonosc.udp_client.SimpleUDPClient, parameter: str, value) -> None:
    """Sends an OSC message using a passed configured client"""
    client.send_message(parameter, value)


def sendtoque(name, qosc: janus.SyncQueue[Any], value) -> None:
    """Sends / puts a list with name/value pairs for OSCtobuttplug to read"""
    # Check that the queue is not full before sending new commands
    if not qosc.full():
        print("not full")
        valuelist = (name, value)
        qosc.put(valuelist)
        qosc.join()


def retransmit(cli, param, value) -> None:
    """Command handler for Retransmiting back through OSC"""
    sendosc(cli, param, value)
    printoscbridge(f"retransmitting : {param} {value}")


def command_handlerbp(command, args, value):
    """Command handler for OSCtobuttplug, sends the OSC data using a queue"""
    sendtoque(args[0], args[1], value)


def command_handlerpass(command, args, value):
    """Command handler for OSCProcess, re-sends data through OSC """
    retransmit(args[0], args[1], value)


def printoscbridge(msg) -> None:
    """Helper function to print with colors"""
    print(f"{bcolors.HEADER} OSCB : {bcolors.ENDC} {msg}")


def printwarningoscb(msg: str) -> None:
    """Helper function to print with colors"""
    printoscbridge(f"{bcolors.WARNING} {msg} {bcolors.ENDC}")


def loadcommandlist(mainconfig: myclasses.MainData.mainconfig, oscserverconfig: myclasses.OscServerData,
                    disp: dispatcher.Dispatcher, q: janus.SyncQueue[Any],
                    sendclient: pythonosc.udp_client.SimpleUDPClient, q_proc: janus.SyncQueue[Any]) -> bool:
    # read configuration and populate the dispatcher
    """Load all commands to listen from the incoming OSC data and load them into the OSCserver dispatcher.
        Uses helper functions insce the commands are quite diferent to load into the dispatcher.
        Keeps a list of number of commands in the dispatcher since it does not have an easy len() method.
    """
    ncomands = 0
    if mainconfig["OSCtoButtplug"]:
        butplugmaping = oscserverconfig.buttplug
        ncomands = ncomands + populatedispatcherbp(disp, butplugmaping, q)
    if mainconfig["OSCPass"]:
        passmaping = oscserverconfig.retransmit
        ncomands = ncomands + populatedispatcheroscpass(disp, passmaping, sendclient)
    if mainconfig["OSCprocess"]:
        processmaping = oscserverconfig.proces
        ncomands = ncomands + populateprocessmaping(disp, processmaping, sendclient, q_proc)
    if ncomands == 0:
        printwarningoscb("No commands for the OSCbridge to listen for.")
        return False
    else:
        printwarningoscb(f"Commands for the OSCbridge to listen for : {ncomands}")
        return True


def queuesend(queue: janus.SyncQueue[Any], data) -> None:
    """Sends data to the passed queue"""
    if not queue.full():
        queue.put(data)
        queue.join()


def command_handleprocess(command, args, value) -> None:
    """Wrapper function to unpack incoming args and values from the dispatcher"""
    queuesend(args[0], [value, args[1]])


def populateprocessmaping(disp: dispatcher.Dispatcher, comands, cli: pythonosc.udp_client.SimpleUDPClient,
                          q_proc: janus.SyncQueue[Any]) -> int:
    """Reads oscprocess commands configuration files and populates the server Dispatcher"""
    items = 0
    # populating the dispatcher with commands to be custom processed
    if not comands:
        printwarningoscb("Could not read any commands to dispatch for process")
        return items
    if len(comands) % 3 == 0:
        printoscbridge(f"Setting nº of mappings for OSCprocess: {len(comands) // 3}")
        for i in range(len(comands) // 3):
            if i != 0:
                # any iteration past the first one
                a = i*3
            else:
                # first iteration
                a = i
            proces = comands[a + 1]
            if proces == "respond":
                disp.map(comands[a], command_handleprocess, q_proc, (proces, comands[a + 2]))
                printoscbridge(f"{comands[a]} _mapped to_ {proces} _ {comands[a + 2]}")
                items = items + 1
    else:
        printoscbridge(bcolors.FAIL +
                       "The number of entrys in OSCprocess -> procesMaping.json is not multiple of 2"
                       + bcolors.ENDC)
    return items


def populatedispatcheroscpass(disp: dispatcher.Dispatcher, comands, cli: pythonosc.udp_client.SimpleUDPClient) -> int:
    """Reads oscprocess commands configuration files and populates the server Dispatcher"""
    # The mappinggs are stored in sets of 2, [origin, destination, origin2, destination2]
    items = 0
    if not comands:
        printwarningoscb("Could not read any commands to dispatch for oscpass")
        return items
    if len(comands) % 2 == 0:
        printoscbridge(f"Setting nº of mappings for OSCpass: {len(comands) // 2}")
        for i in range(len(comands) // 2):
            if i != 0:
                # any iteration past the first one
                a = i*2
            else:
                # first iteration
                a = i

            disp.map(comands[a], command_handlerpass, cli, comands[a + 1])
            printoscbridge(comands[a] + " :_resending to_: " + comands[a + 1])
            items = items + 1
    else:
        printoscbridge(
            f"{bcolors.FAIL} The number of entrys in OSCpass -> passMaping.json is not multiple of 2 {bcolors.ENDC}")
    return items


def populatedispatcherbp(disp: dispatcher.Dispatcher, comands, q: janus.SyncQueue[Any]) -> int:
    """Reads OSCtoButtplug commands configuration files and populates the server Dispatcher"""
    # the mapping is stored in sets of 3
    items = 0
    if not comands:
        printwarningoscb("Could not read any commands to dispatch for butplug")
        return items
    if len(comands) % 3 == 0:
        printoscbridge(f"Setting nº of mappings for OSCtoButtplug: {len(comands) // 3}")
        for i in range(len(comands) // 3):
            if i != 0:
                a = i * 3
            else:
                a = i
            try:
                oscaddr = comands[a]
                devname = comands[a + 1]
                command = comands[a + 2]
                commandname = comands[a + 2][0]
                if len(comands[a + 2]) == 2:
                    commanddata = comands[a + 2][1]
                else:
                    commanddata = ''
                # replacing the command name str(), for it's assigned value, if its
                command[0] = myclasses.BpDevCommand[commandname].value
                # registering command in internal valid list
                disp.map(oscaddr, command_handlerbp, (devname, command), q)
                printoscbridge(f"{oscaddr}_ mapped to_ {devname} {commandname} {commanddata}")
                items = items + 1
            except ValueError:
                printwarningoscb(f" Invalid command for osctobutplug in configuration, skipping it. "
                                 f"{command} {commandname}")
            except Exception as e:
                printwarningoscb(f" This command could not be mapped to OSCtoButtplug : {command} : error {e}")
    else:
        printoscbridge(bcolors.FAIL +
                       "The number of entry's in OSCtoButtplug -> parameterMaping.json is not multiple of 3"
                       + bcolors.ENDC)
    return items


def configsendclient(mcon: myclasses.MainData.mainconfig) -> udp_client.SimpleUDPClient:
    """Helper function that returns a configured udp OSC client"""
    ip = mcon["OSCSendIP"]
    port = mcon["OSCSendPort"]
    return udp_client.SimpleUDPClient(ip, port)


def configserver(mcon: myclasses.MainData.mainconfig, disp: dispatcher.Dispatcher) -> osc_server.ThreadingOSCUDPServer:
    """Helper function that returns a configured udp OSC server"""
    ip = mcon["OSCBListenIP"]
    port = mcon["OSCBListenPort"]
    return osc_server.ThreadingOSCUDPServer((ip, port), disp)


def oscbridge(mconfig: myclasses.MainData.mainconfig, q_state: janus.SyncQueue[Any],
              q_bp: janus.SyncQueue[Any], q_proc: janus.SyncQueue[Any]) -> None:
    """Main function to run OSCBridge, it will load configure and start the OSCserver and OSCclients"""
    try:
        printoscbridge("running bridge ")
        oscbconfig = myclasses.OscServerData
        # osc client for resending data back "oscpass"
        sendclient = configsendclient(mconfig.mainconfig)
        # dispatcher that maps OSC inputs to functions
        dispatcherl = dispatcher.Dispatcher()
        # load mappings and set up mappings from configuration files
        parametermaping = loadcommandlist(mconfig.mainconfig, oscbconfig, dispatcherl, q_bp, sendclient, q_proc)
        sendclient.send_message("/OSCBridge", 1)
        if parametermaping == 0:
            # parametermaping didn't have any prameters to listen for
            q_state.put("oscdown")
            sendclient.send_message("/OSCBridge", 0)
            exit()
        printoscbridge("Parameter Maping file loaded, continuing...")
        # read the server configuration
        server = configserver(mconfig.mainconfig, dispatcherl)
        printoscbridge("Serving on {}".format(server.server_address))
        server.serve_forever()
        sendclient.send_message("/OSCBridge", 0)
    except Exception as e:
        printwarningoscb(f"Error in the main loop, shuting down {e}")
    except SystemExit:
        printwarningoscb("Shutting down this side.")
