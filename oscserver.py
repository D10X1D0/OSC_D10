import json
import queue

import janus
import pythonosc.udp_client
from pythonosc import (osc_server, udp_client, dispatcher)

from printcolors import bcolors
# default contents of parameterMaping.json
# OSCparameter, "device name", [command]
# OSCparameter, "device name", [command, motor index]

parameterMaping = [
  "/avatar/parameters/pContact1", "Lovense Edge", ["SingleMotorVibrateCmd", 0],
  "/avatar/parameters/pContact2", "Lovense Edge", ["SingleMotorVibrateCmd", 1],
  "/avatar/parameters/Mouth", "XBox (XInput) Compatible Gamepad 1", ["VibrateCmd"],
  "/avatar/parameters/Test2", "XBox (XInput) Compatible Gamepad 1", ["SingleMotorVibrateCmd", 0],
  "/avatar/parameters/Test3", "XBox (XInput) Compatible Gamepad 1", ["SingleMotorVibrateCmd", 1]
]

# default contents of passMaping.json
# OSC origin adress, OSC destination adress

passMaping = [
  "/avatar/parameters/a", "/avatar/parameters/b"
]

def sendosc(client: pythonosc.udp_client.SimpleUDPClient, parameter: str, value) -> None:
    client.send_message(parameter, value)


def sendtoque(name, qosc: queue.Queue, value) -> None:
    # printoscbridge("Sending to queue")
    valuelist = (name, value)
    # printoscbridge(valuelist)
    # printoscbridge(qosc)
    qosc.put(valuelist)
    qosc.join()


def retransmit(cli, param, value) -> None:
    sendosc(cli, param, value)
    printoscbridge("retransmitting : " + str(param) + " " + str(value))


def command_handlerbp(command, args, value):
    sendtoque(args[0], args[1], value)


def command_handlerpass(command, args, value):
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
        printoscbridge("Shutting down oscbridge, no osc messages found in configuration files to listen for.")
        return False


def tryreadjson(filename):
    with open(filename) as f:
        data = json.load(f)
        return data


def readjsonfile(filename: str, defaultvalue):
    try:
        data = tryreadjson(filename)
        return data
    except OSError as e:
        printoscbridge("Could not load " + filename)
        createdefaultfile(filename, defaultvalue)
        data = tryreadjson(filename)
        return data
    except Exception as e:
        printoscbridge("Could not load " + filename)
        printoscbridge("Exception : " + str(e))
        return False


def createdefaultfile(filename, data):
    printwarningoscb("Creating default config file: " + filename)
    try:
        with open(filename, 'w') as f:
            # print(str(data))
            json.dump(data, f)
    except:
        printwarningoscb("Could not create a default config file for " + filename)


def printoscbridge(msg) -> None:
    print(bcolors.HEADER + "OSCB : " + bcolors.ENDC + str(msg))


def printwarningoscb(msg: str):
    printoscbridge(bcolors.WARNING + msg + bcolors.ENDC)


def loadcommandlist(mainconfig, disp: dispatcher.Dispatcher, q: janus.SyncQueue[int],
                    sendclient: pythonosc.udp_client.SimpleUDPClient):
    dispatcherpopulated = False
    if mainconfig["OSCtoButtplug"]:
        # read configuration and populate the dispatcher
        butplugmaping = readjsonfile("parameterMaping.json", parameterMaping)
        populatedispatcherbp(disp, butplugmaping, q)
        dispatcherpopulated = True
    if mainconfig["OSCPass"]:
        passmaping = readjsonfile("passMaping.json", passMaping)
        populatedispatcheroscpass(disp, passmaping, sendclient)
        dispatcherpopulated = True
    return dispatcherpopulated


def populatedispatcheroscpass(disp: dispatcher.Dispatcher, comands,cli: pythonosc.udp_client.SimpleUDPClient) -> None:
    # populating the dispatcher with commands to be passed back after some processing
    # The mappinggs are stored in sets of 2, [origin, destination]
    if comands == False:
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


def populatedispatcherbp(disp: dispatcher.Dispatcher, comands, q:janus.SyncQueue[int]) -> None:
    # populating dispatcher with commands to listen for and send to buttplug
    # the mapping is stored in sets of 3
    if len(comands) % 3 == 0:
        printoscbridge("Setting nº of mappings for OSCtoButtplug:" + str(len(comands) // 3))
        for i in range(len(comands) // 3):
            if i != 0:
                a = i * 3
            else:
                a = i
            printoscbridge(comands[a] + " _ mapped to_ " + str(comands[a + 1]) + str(comands[a + 2]))
            disp.map(comands[a], command_handlerbp, (comands[a + 1], comands[a + 2]), q)
    else:
        printoscbridge(bcolors.FAIL +
                       "The number of entrys in OSCtoButtplug -> parameterMaping.json is not multiple of 3"
                       + bcolors.ENDC)


def readconfig(config, key: str, defaultvalue, deftype):
    try:
        value = config[key]
        printoscbridge(
            str(key) + " from Mainconfig file set to " + str(value))
        if not isinstance(value, deftype):
            value = defaultvalue
            printwarningoscb(
                str(key) + "is not a " + str(deftype) + " in the config file , setting it to " + str(value))
    except:
        value = defaultvalue
        printwarningoscb("Can't read " + str(key) + " from Mainconfig file set to default " + str(value))
    return value


def configsendclient(config) -> udp_client.SimpleUDPClient:
    ip = readconfig(config, "OSCSendIP", "127.0.0.1", str,)
    port = readconfig(config, "OSCSendPort", 9001, int)
    return udp_client.SimpleUDPClient(ip, port)


def configserver(config, disp: dispatcher.Dispatcher) -> osc_server.ThreadingOSCUDPServer:
    ip = readconfig(config, "OSCBListenIP", "127.0.0.1", str)
    port = readconfig(config, "OSCBListenPort", 9000, int)
    return osc_server.ThreadingOSCUDPServer((ip, port), disp)


def oscbridge(mainconfig, q_state: janus.SyncQueue[int], qsinc: janus.SyncQueue[int]) -> None:
    printoscbridge("running bridge ")
    # osc client for resending data back "oscpass"
    sendclient = configsendclient(mainconfig)
    # dispatcher that maps OSC inputs to functions
    dispatcherl = dispatcher.Dispatcher()
    # load mappings and set up mappings from configuration files
    parametermaping = loadcommandlist(mainconfig, dispatcherl, qsinc, sendclient)
    # createdefaultparametermapingfile()
    sendclient.send_message("/OSCBridge", 1)
    if not parametermaping:
        # parametermaping didn't have any prameters to listen for
        q_state.put("oscdown")
        sendclient.send_message("/OSCBridge", 0)
        exit()
    printoscbridge("Parameter Maping file loaded, continuing...")
    # read the server configuration
    server = configserver(mainconfig, dispatcherl)
    printoscbridge("Serving on {}".format(server.server_address))
    server.serve_forever()
    sendclient.send_message("/OSCBridge", 0)
