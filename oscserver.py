import argparse
import json
import queue

import janus
import pythonosc.udp_client
from pythonosc import (osc_server, udp_client, dispatcher)

from printcolors import bcolors


def sendosc(client: pythonosc.udp_client.SimpleUDPClient, parameter: str, value) -> None:

    client.send_message(parameter, value)


def sendtoque(name, qosc: queue.Queue, value) -> None:
    printoscbridge("Sending to queue")
    valuelist = (name, value)
    print(valuelist)
    print(qosc)
    qosc.put(valuelist)
    qosc.join()


def retransmit(cli, param, value):
    sendosc(cli, param, value)
    printoscbridge("retransmitting : " + str(param) + str(value))

def command_handlerbp(command, args, value) -> None:
    sendtoque(args[0], args[1], value)


def command_handlerpass(command, args, value) -> None:
    retransmit(args[0], args[1], value)


def readparametermaping():
    try:
        with open('parameterMaping.json') as f:
            data = json.load(f)
            # print(type(data))
            # print(str(data))
            return data
    except Exception as e:
        printoscbridge("Could not load parameterMaping.json")
        printoscbridge("Exception : " + str(e))
        return False


def readjsonfile(filename: str):
    try:
        with open(filename) as f:
            data = json.load(f)
            return data
    except Exception as e:
        printoscbridge("Could not load " + filename)
        printoscbridge("Exception : " + str(e))
        return False


def printoscbridge(msg) -> None:
    print(bcolors.HEADER + "OSCB : " + bcolors.ENDC + str(msg))


def loadcommandlist(mainconfig, disp: dispatcher.Dispatcher, q: janus.SyncQueue[int],
                    sendclient: pythonosc.udp_client.SimpleUDPClient):
    dispatcherpopulated = False
    if mainconfig["OSCtoButtplug"]:
        # read configuration and pupulate the dispatcher
        butplugmaping = readjsonfile("parameterMaping.json")
        populatedispatcherbp(disp, butplugmaping, q)
        dispatcherpopulated = True
    if mainconfig["OSCPass"]:
        passmaping = readjsonfile("passMaping.json")
        populatedispatcheroscpass(disp, passmaping, sendclient)
        dispatcherpopulated = True
    return dispatcherpopulated


def populatedispatcheroscpass(disp: dispatcher.Dispatcher, comands,cli: pythonosc.udp_client.SimpleUDPClient) -> None:
    # populating the dispatcher with commands to be passed back after some processing
    # The mappinggs are stored in sets of 2, [origin, destination]
    if len(comands) %2 == 0:
        printoscbridge("Setting nº of mappings for OSCpass:" + str(len(comands) // 2))
        for i in range(len(comands) // 2):
            print(i)
            if i != 0:
                a = i*2
                disp.map(comands[a], command_handlerpass,cli, (comands[a + 1]))
                printoscbridge(comands[a])
                printoscbridge(comands[a + 1])
            else:
                disp.map(comands[i], command_handlerpass, cli, (comands[i + 1]))
                printoscbridge(comands[i] + " :_resending to_: " +comands[i + 1])
    else:
        printoscbridge(bcolors.FAIL +
                       "The number of entrys in OSCpass -> passMaping.json is not multiple of 2"
                       + bcolors.ENDC)

def populatedispatcherbp(disp: dispatcher.Dispatcher, comands, q:janus.SyncQueue[int]) -> None:
    # populating dispatcher with commands to listen for and send to buttplug
    # the mapping is stored in sets of 3
    if len(comands) % 3 == 0:
        printoscbridge("Setting nº of mappings for OSCtoButtplug:" + str(len(comands) // 3))
        for i in range(len(comands) // 3):
            if i != 0:
                a = i * 3
                printoscbridge(comands[a] + " _ mapped to_ " + str(comands[a + 1]) + str(comands[a + 2]))
                disp.map(comands[a], command_handlerbp, (comands[a + 1], comands[a + 2]), q)
            else:
                printoscbridge(
                    comands[i] + " _ mapped to_ " + str(comands[i + 1] + str(comands[i + 2])))
                disp.map(comands[i], command_handlerbp, (comands[i + 1], comands[i + 2]), q)
    else:
        printoscbridge(bcolors.FAIL +
                       "The number of entrys in OSCtoButtplug -> parameterMaping.json is not multiple of 3"
                       + bcolors.ENDC)


def readconfig(config, key: str, defaultvalue):
    try:
        value = config[key]
        printoscbridge(str(key) + " from Mainconfig file set to " + str(value))
    except:
        value = defaultvalue
        printoscbridge("Can't read " + str(key) + " from Mainconfig file set to default " + str(value))
    return value


def configargs(mainconfig,ipid,ipdef,portid,portdef):
    # osc server config, the one that's listening
    ip = readconfig(mainconfig, ipid, ipdef)
    port = readconfig(mainconfig, portid, portdef)

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        default=ip, help="The ip to listen on")
    parser.add_argument("--port",
                        type=int, default=port, help="The port to listen on")
    args = parser.parse_args()
    return args


def configsendclient(config):
    args = configargs(config,"OSCSendIP", "127.0.0.1", "OSCSendPort", 9001)
    cli = udp_client.SimpleUDPClient(args.ip, args.port)
    return cli


def oscbridge(mainconfig, q_state: janus.SyncQueue[int], qsinc: janus.SyncQueue[int]) -> None:
    printoscbridge("running bridge ")
    sendclient = configsendclient(mainconfig)
    dispatcherl = dispatcher.Dispatcher()
    parametermaping = loadcommandlist(mainconfig, dispatcherl, qsinc, sendclient)
    # createdefaultparametermapingfile()
    sendclient.send_message("/OSCBridge", 1)
    if not parametermaping:
        printoscbridge("Shutting down oscbridge, no osc messages found in configuration files to listen for.")
        statemsg = "oscdown"
        q_state.put(statemsg)
        exit()
    printoscbridge("Parameter Maping file loaded, continuing...")
    argsserver = configargs(mainconfig, "OSCBridgeListenIP", "127.0.0.1", "OSCBListenPort", 9001)
    server = osc_server.ThreadingOSCUDPServer(
        (argsserver.ip, argsserver.port), dispatcherl)
    printoscbridge("Serving on {}".format(server.server_address))

    server.serve_forever()
    sendclient.send_message("/OSCBridge", "stopping")
