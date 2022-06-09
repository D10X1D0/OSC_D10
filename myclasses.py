import json
from dataclasses import dataclass
from printcolors import bcolors

maindefault = {
    "OSCBridge": False,
    "OSCBListenIP": "127.0.0.1", "OSCBListenPort": 9001,
    "OSCPass": False,
    "OSCSendIP": "127.0.0.1", "OSCSendPort": 9000,
    "OSCtoButtplug": False,
    "InterfaceWS": "127.0.0.1:12345",
    "OSCprocess": False
}
# default contents of parameterMaping.json
# OSCparameter, "device name", [command]
# OSCparameter, "device name", [command, motor index]
# OSCparameter, "device name", [command, rotation direction]  "allcw" clockwise "allccw" counterclockwise
parameterMapingdefault = [
    "/avatar/parameters/pContact1", "Lovense Edge", ["VibrateCmd", "all"],
    "/avatar/parameters/pContact2", "Lovense Edge", ["VibrateCmd", [0]],
    "/avatar/parameters/Mouth", "XBox (XInput) Compatible Gamepad 1", ["VibrateCmd", "all"],
    "/avatar/parameters/Test2", "XBox (XInput) Compatible Gamepad 1", ["VibrateCmd", [0]],
    "/avatar/parameters/Test3", "XBox (XInput) Compatible Gamepad 1", ["VibrateCmd", [1]]
]
#  "/avatar/parameters/pContact3", "rotatingdevice", ["RotateCmd",["allcw"]]
# "/avatar/parameters/pContact3", "rotatingdevice", ["RotateCmd",["allccw"]]
# default contents of passMaping.json
# OSC origin adress, OSC destination adress
passMapingdefault = [
    "/avatar/parameters/a", "/avatar/parameters/b"
]
# default contents of processMaping
processMapingdefault = [
    "/avatar/parameters/Testa", "pulse", [30, 1],
    "/avatar/parameters/Testa", "pulse", [15, 0],
    "/avatar/parameters/Testc", "pulse", [10, False],
    "/avatar/parameters/Testc", "pulse", [15, True],
    "/avatar/parameters/Testd", "respond", [1, True, "/avatar/parameters/Testda"],
    "/avatar/parameters/Testd", "respond", [0.5, False, "/avatar/parameters/Testda"]
]


def printwarning(msg):
    print(bcolors.WARNING + msg + bcolors.ENDC)


def tryreadjson(filename):
    with open(filename) as f:
        data = json.load(f)
        return data


def createdefaultfile(filename, data):
    printwarning("Creating default config file: " + filename)
    try:
        with open(filename, 'w') as f:
            # print(str(data))
            json.dump(data, f)
    except:
        printwarning("Could not create a default config file for " + filename)


def readjsonfile(filename: str, defaultvalue):
    # read a .json file, if it fails creates a default one.
    try:
        data = tryreadjson(filename)
        return data
    except OSError as e:
        printwarning("Could not load " + filename)
        createdefaultfile(filename, defaultvalue)
        data = tryreadjson(filename)
        return data
    except Exception as e:
        print("Could not load " + filename)
        print("Exception : " + str(e))
        return False


@dataclass(frozen=True, order=True)
class MainData:
    mainconfig = readjsonfile("Mainconfig.json", maindefault)


@dataclass(frozen=True, order=True)
class OscServerData:
    retransmit = readjsonfile("retransmitMaping.json", passMapingdefault)
    proces = readjsonfile("procesMaping.json", processMapingdefault)
    buttplug = readjsonfile("parameterMaping.json", parameterMapingdefault)
