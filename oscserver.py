import janus
import pythonosc.udp_client
from pythonosc import (osc_server, udp_client, dispatcher)
import myclasses
from printcolors import bcolors


def sendosc(client: pythonosc.udp_client.SimpleUDPClient, parameter: str, value) -> None:
    client.send_message(parameter, value)


def sendtoque(name, qosc: janus.SyncQueue[int], value) -> None:
    valuelist = (name, value)
    # printoscbridge("Sending to butplug")
    qosc.put(valuelist)
    # printoscbridge("waiting for butplug")
    qosc.join()


def retransmit(cli, param, value) -> None:
    sendosc(cli, param, value)
    printoscbridge(f"retransmitting : {param} {value}")


def command_handlerbp(command, args, value):
    sendtoque(args[0], args[1], value)


def command_handlerpass(command, args, value):
    retransmit(args[0], args[1], value)


def printoscbridge(msg) -> None:
    print(f"{bcolors.HEADER} OSCB : {bcolors.ENDC} {msg}")


def printwarningoscb(msg: str) -> None:
    printoscbridge(f"{bcolors.WARNING} {msg} {bcolors.ENDC}")


def loadcommandlist(mainconfig: myclasses.MainData.mainconfig, oscserverconfig: myclasses.OscServerData,
                    disp: dispatcher.Dispatcher, q: janus.SyncQueue[int],
                    sendclient: pythonosc.udp_client.SimpleUDPClient, q_proc: janus.SyncQueue[int]) -> bool:
    # read configuration and populate the dispatcher
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


def queuesend(queue: janus.SyncQueue[int], data) -> None:
    # printoscbridge("sending to queque")
    queue.put(data)
    # printoscbridge("waiting for the queque to be red")
    queue.join()
    # printoscbridge("queque done...")


def command_handleprocess(command, args, value):
    # printoscbridge("command_handleprocess")
    # printoscbridge(f"{command} {value} {args}")
    queuesend(args[0], [value, args[1]])


def populateprocessmaping(disp: dispatcher.Dispatcher, comands, cli: pythonosc.udp_client.SimpleUDPClient,
                          q_proc: janus.SyncQueue[int]) -> int:
    items = 0
    # populating the dispatcher with commands to be custom processed
    if not comands:
        printwarningoscb("Could not read any commands to dispatch for process")
        return items
    if len(comands) % 3 == 0:
        printoscbridge(f"Setting n?? of mappings for OSCprocess: {len(comands) // 3}")
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
    # populating the dispatcher with commands to be passed back to a different address
    # The mappinggs are stored in sets of 2, [origin, destination, origin2, destination2]
    items = 0
    if not comands:
        printwarningoscb("Could not read any commands to dispatch for oscpass")
        return items
    if len(comands) % 2 == 0:
        printoscbridge(f"Setting n?? of mappings for OSCpass: {len(comands) // 2}")
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


def populatedispatcherbp(disp: dispatcher.Dispatcher, comands, q: janus.SyncQueue[int]) -> int:
    # populating dispatcher with commands to listen for and send to buttplug
    # the mapping is stored in sets of 3
    items = 0
    if not comands:
        printwarningoscb("Could not read any commands to dispatch for butplug")
        return items
    if len(comands) % 3 == 0:
        printoscbridge(f"Setting n?? of mappings for OSCtoButtplug: {len(comands) // 3}")
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


def configsendclient(mcon:myclasses.MainData.mainconfig) -> udp_client.SimpleUDPClient:
    ip = mcon["OSCSendIP"]
    port = mcon["OSCSendPort"]
    return udp_client.SimpleUDPClient(ip, port)


def configserver(mcon:myclasses.MainData.mainconfig, disp: dispatcher.Dispatcher) -> osc_server.ThreadingOSCUDPServer:
    ip = mcon["OSCBListenIP"]
    port = mcon["OSCBListenPort"]
    return osc_server.ThreadingOSCUDPServer((ip, port), disp)


def oscbridge(mconfig: myclasses.MainData.mainconfig, q_state: janus.SyncQueue[int],
              q_bp: janus.SyncQueue[int], q_proc: janus.SyncQueue[int]) -> None:
    try:
        printoscbridge("running bridge ")
        oscbconfig = myclasses.OscServerData
        # osc client for resending data back "oscpass"
        sendclient = configsendclient(mconfig.mainconfig)
        # dispatcher that maps OSC inputs to functions
        dispatcherl = dispatcher.Dispatcher()
        # load mappings and set up mappings from configuration files
        parametermaping = loadcommandlist(mconfig.mainconfig, oscbconfig, dispatcherl, q_bp, sendclient, q_proc)
        # createdefaultparametermapingfile()
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
