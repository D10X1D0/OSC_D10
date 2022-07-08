import json
from dataclasses import dataclass
from enum import Enum

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
# OSCparameter, "device name", [command, [rotor index, [rotation direction]]  "true" clockwise, "false" counterclockwise
parameterMapingdefault = [
    "/avatar/parameters/pContact1", "Lovense Edge", ["Vibrate", "all"],
    "/avatar/parameters/pContact2", "Lovense Edge", ["Vibrate", [0]],
    "/avatar/parameters/stop0", "Lovense Edge", ["Stop"],
    "/avatar/parameters/rotatea", "fake rotating device", ["Rotate", "allcw"],
    "/avatar/parameters/rotateb", "fake rotating device", ["Rotate", "allccw"],
    "/avatar/parameters/rotatec", "fake rotating device", ["Rotate", [0, True]],
    "/avatar/parameters/rotated", "fake rotating device", ["Rotate", [[2, False], [7, True]]],
    "/avatar/parameters/Mouth", "XBox (XInput) Compatible Gamepad 1", ["Vibrate", "all"],
    "/avatar/parameters/Test2", "XBox (XInput) Compatible Gamepad 1", ["Vibrate", [0]],
    "/avatar/parameters/Test3", "XBox (XInput) Compatible Gamepad 1", ["Vibrate", [1]]
]
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
    print(f"{bcolors.WARNING} {msg} {bcolors.ENDC}")


def tryreadjson(filename):
    with open(filename) as f:
        data = json.load(f)
        return data


def createdefaultfile(filename, data):
    printwarning(f"Creating default config file:{filename}")
    try:
        jsondump = json.dumps(data, indent=4)
        with open(filename, "w") as f:
            f.write(jsondump)
    except Exception as e:
        printwarning(f"Could not create a default config file for {filename}, error : {e}")


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
        print(f"Could not load + {filename}")
        print(f"Exception :  {e}")
        return False


@dataclass(frozen=True, order=True)
class MainData:
    mainconfig = readjsonfile("Mainconfig.json", maindefault)


@dataclass(frozen=True, order=True)
class OscServerData:
    retransmit = readjsonfile("retransmitMaping.json", passMapingdefault)
    proces = readjsonfile("procesMaping.json", processMapingdefault)
    buttplug = readjsonfile("parameterMaping.json", parameterMapingdefault)


# enum of valid commands for devices in osctobutplug
# they have to match 1:1 in value with BpDevCommandInterface
class BpDevCommand(Enum):
    Stop = 1
    Vibrate = 2
    Rotate = 3


# enum of valid commands for devices in Buttplug and controllable in osctobutplug
# they have to match 1:1 in value with BpDevCommand
class BpDevCommandInterface(Enum):
    StopDeviceCmd = 1
    VibrateCmd = 2
    RotateCmd = 3

