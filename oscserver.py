import argparse
import json
import queue

import janus
from pythonosc import (osc_server, udp_client, dispatcher)

from printcolors import bcolors


def sendosc(parameter: str, value):
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=9000,
                        help="The port the OSC server is listening on")
    args = parser.parse_args()

    client = udp_client.SimpleUDPClient(args.ip, args.port)

    client.send_message(parameter, value)


def sendtoque(name, qosc: queue.Queue, value):
    printoscbridge("Sending to queue")
    valuelist = (name, value)
    print(valuelist)
    print(qosc)
    qosc.put(valuelist)
    qosc.join()


def command_handlerbp(command, args, value):
    sendtoque(args[0], args[1], value)


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


def printoscbridge(msg):
    print(bcolors.HEADER + "OSCB : " + bcolors.ENDC + str(msg))


def loadcommandlist(mainconfig, disp: dispatcher.Dispatcher, q: janus.SyncQueue[int]):
    if mainconfig["OSCtoButtplug"]:
        butplugmaping = readjsonfile("parameterMaping.json")
        populatedispatcher(disp, butplugmaping, q)
        return butplugmaping
    else:
        return False


def populatedispatcher(disp: dispatcher.Dispatcher, comands, q:janus.SyncQueue[int]):
    # populating dispatcher with commands to listen for and send to buttplug
    # the mapping is stored in sets of 3
    if len(comands) % 3 == 0:
        printoscbridge("Setting nº of mappings :" + str(len(comands) // 3))
        for i in range(len(comands) // 3):
            if i != 0:
                a = i * 3
                printoscbridge(comands[a] + " _ mapped to_ "
                               + str(comands[a + 1]) + str(comands[a + 2]))
                disp.map(comands[a], command_handlerbp,
                         (comands[a + 1], comands[a + 2]), q)
            else:
                printoscbridge(
                    comands[i] + " _ mapped to_ "
                    + str(comands[i + 1] + str(comands[i + 2])))
                disp.map(comands[i], command_handlerbp,
                         (comands[i + 1], comands[i + 2]), q)
    else:
        printoscbridge(bcolors.FAIL +
                       "The number of entrys in OSCtoButtplug -> parameterMaping.json is not multiple of 3"
                       + bcolors.ENDC)


def oscbridge(mainconfig, q_state: janus.SyncQueue[int], qsinc: janus.SyncQueue[int]):
    printoscbridge("running bridge ")
    dispatcherl = dispatcher.Dispatcher()
    parametermaping = loadcommandlist(mainconfig, dispatcherl, qsinc)
    # createdefaultparametermapingfile()

    if not parametermaping:
        printoscbridge("Shutting down oscbridge, no osc messages found in configuration files to listen for.")
        statemsg = "oscdown"
        q_state.put(statemsg)
        exit()
    printoscbridge("Parameter Maping file loaded, continuing...")

    "osc server config, the one that's listening"
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port",
                        type=int, default=9001, help="The port to listen on")
    args = parser.parse_args()

    server = osc_server.ThreadingOSCUDPServer(
        (args.ip, args.port), dispatcherl)
    printoscbridge("Serving on {}".format(server.server_address))

    server.serve_forever()
