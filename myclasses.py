from dataclasses import dataclass

import osc_d10.tools.io_files

maindefault = {
    "OSCBridge": True,
    "OSCBridgeDEBUG": False,
    "OSCBListenIP": "127.0.0.1", "OSCBListenPort": 9001,
    "OSCSendIP": "127.0.0.1", "OSCSendPort": 9000,
    "OSCProcess": False,
    "OSCtoButtplug": True,
    "IntifaceProtocol": "ws",
    "IntifaceIP": "127.0.0.1", "IntifacePort": 12345
}


class MainData:
    mainconfig = osc_d10.tools.io_files.read_json_file("Mainconfig.json", maindefault)

