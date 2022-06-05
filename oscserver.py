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
    printoscbridge("retransmitting : " + str(param) + " " + str(value))


def process(dest: str, param, value) -> None:
    printoscbridge("process")
    #printoscbridge("process" + str(dest) + "__" + str(param) + "__" + str(value))
    # param [oscadress, oscclient]


def command_handlerbp(command, args, value):
    sendtoque(args[0], args[1], value)


def command_handlerpass(command, args, value):
    retransmit(args[0], args[1], value)


def printoscbridge(msg) -> None:
    print(bcolors.HEADER + "OSCB : " + bcolors.ENDC + str(msg))


def printwarningoscb(msg: str):
    printoscbridge(bcolors.WARNING + msg + bcolors.ENDC)


def loadcommandlist(mainconfig: myclasses.Mainconfig, oscserverconfig: myclasses.OscServerData,
                    disp: dispatcher.Dispatcher, q: janus.SyncQueue[int],
                    sendclient: pythonosc.udp_client.SimpleUDPClient, q_proc: janus.SyncQueue[int]):
    dispatcherpopulated = False
    # read configuration and populate the dispatcher
    if mainconfig["OSCtoButtplug"]:
        butplugmaping = oscserverconfig.buttplug
        populatedispatcherbp(disp, butplugmaping, q)
        dispatcherpopulated = True
    if mainconfig["OSCPass"]:
        passmaping = oscserverconfig.retransmit
        populatedispatcheroscpass(disp, passmaping, sendclient)
        dispatcherpopulated = True
    #disabled comunication to process, no functions need data in yet
    """ disabled, no need for data back to oscprocess.process yet.
    if mainconfig["OSCprocess"]:
        processmaping = oscserverconfig.proces
        populateprocessmaping(disp, processmaping, sendclient, q_proc)
        dispatcherpopulated = True
    """
    return dispatcherpopulated


def queuesend(queue: janus.SyncQueue[int], data) -> None:
    printoscbridge("sending to queque")
    queue.put(data)
    printoscbridge("waiting for the queque to be red")
    queue.join()
    printoscbridge("queque done...")


def command_handleprocess(command, args, value):
    # args[0] [oscadress, oscclient]
    #process(command, args, value)
    printoscbridge("command_handleprocess")
    printoscbridge(command)
    printoscbridge(value)
    printoscbridge(args)
    queuesend(args[0], args[1])


def populateprocessmaping(disp: dispatcher.Dispatcher, comands, cli: pythonosc.udp_client.SimpleUDPClient,
                          q_proc: janus.SyncQueue[int]) -> None:
    # populating the dispatcher with commands to be custom processed
    if not comands:
        printwarningoscb("Could not read any commands to dispatch")
        exit()
    if len(comands) % 3 == 0:
        printoscbridge("Setting nº of mappings for OSCprocess:" + str(len(comands) // 3))
        for i in range(len(comands) // 3):
            if i != 0:
                # any iteration past the first one
                a = i*3
            else:
                # first iteration
                a = i
            disp.map(comands[a], command_handleprocess, q_proc, (comands[a + 1], comands[a + 2]))
            printoscbridge(comands[a] + " _mapped to_ " + str(comands[a + 1]) + " _ " + str(comands[a + 2]))
    else:
        printoscbridge(bcolors.FAIL +
                       "The number of entrys in OSCprocess -> procesMaping.json is not multiple of 2"
                       + bcolors.ENDC)


def populatedispatcheroscpass(disp: dispatcher.Dispatcher, comands, cli: pythonosc.udp_client.SimpleUDPClient) -> None:
    # populating the dispatcher with commands to be passed back to a different address
    # The mappinggs are stored in sets of 2, [origin, destination]
    if not comands:
        printwarningoscb("Could not read any commands to dispatch")
        exit()
    if len(comands) % 2 == 0:
        printoscbridge("Setting nº of mappings for OSCpass:" + str(len(comands) // 2))
        for i in range(len(comands) // 2):
            if i != 0:
                # any iteration past the first one
                a = i*2
            else:
                # first iteration
                a = i

            disp.map(comands[a], command_handlerpass, cli, comands[a + 1])
            printoscbridge(comands[a] + " :_resending to_: " + comands[a + 1])
    else:
        printoscbridge(bcolors.FAIL +
                       "The number of entrys in OSCpass -> passMaping.json is not multiple of 2"
                       + bcolors.ENDC)


def populatedispatcherbp(disp: dispatcher.Dispatcher, comands, q: janus.SyncQueue[int]) -> None:
    # populating dispatcher with commands to listen for and send to buttplug
    # the mapping is stored in sets of 3
    if len(comands) % 3 == 0:
        printoscbridge("Setting nº of mappings for OSCtoButtplug:" + str(len(comands) // 3))
        for i in range(len(comands) // 3):
            if i != 0:
                a = i * 3
            else:
                a = i
            disp.map(comands[a], command_handlerbp, (comands[a + 1], comands[a + 2]), q)
            printoscbridge(comands[a] + " _ mapped to_ " + str(comands[a + 1]) + str(comands[a + 2]))
    else:
        printoscbridge(bcolors.FAIL +
                       "The number of entrys in OSCtoButtplug -> parameterMaping.json is not multiple of 3"
                       + bcolors.ENDC)


def configsendclient(mcon:myclasses.MainData) -> udp_client.SimpleUDPClient:
    ip = mcon["OSCSendIP"]
    port = mcon["OSCSendPort"]
    return udp_client.SimpleUDPClient(ip, port)


def configserver(mcon:myclasses.MainData, disp: dispatcher.Dispatcher) -> osc_server.ThreadingOSCUDPServer:
    ip = mcon["OSCBListenIP"]
    port = mcon["OSCBListenPort"]
    return osc_server.ThreadingOSCUDPServer((ip, port), disp)


def oscbridge(mconfig: myclasses.MainData, q_state: janus.SyncQueue[int],
              q_BP: janus.SyncQueue[int], q_proc: janus.SyncQueue[int]) -> None:
    printoscbridge("running bridge ")
    oscbconfig = myclasses.OscServerData
    # osc client for resending data back "oscpass"
    sendclient = configsendclient(mconfig.mainconfig)
    # dispatcher that maps OSC inputs to functions
    dispatcherl = dispatcher.Dispatcher()
    # load mappings and set up mappings from configuration files
    parametermaping = loadcommandlist(mconfig.mainconfig, oscbconfig, dispatcherl, q_BP, sendclient, q_proc)
    # createdefaultparametermapingfile()
    sendclient.send_message("/OSCBridge", 1)
    if not parametermaping:
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
