# OSC_D10
Python OSC bridge to other apps and send OSC messages back.
Currently able to talk with [Buttplug.io](https://buttplug.io/) , tested with [Intiface](https://intiface.com/)

# How to run
Have a python interpreter and/or IDE installed (Tested in Python 3.11 using pycharm).
Clone this repo inside a python project.
Install the python module dependencies listed inside requirements.txt.
Run main.py

I used color codes to print to console, they look like this "'\033[95m'"

## OSCBridge:
OSC server that can listen and communicate with other apps.
Sends a OSC message to the address "/OSCBridge" when it starts up with a value of "1" and a "0" when it stops running.
Sends a 1 to the "/OSCBridge" OSCSendIp when its running and a 0 when it shuts down.

Configured in Mainconfig.json to enable/disable loading different modules (true=enabled, false=disabled).
        
    Enables/disables the OSC server that's listening and sending the incoming data to be processed to other modules.
      "OSCBridge": false/true
      
    Debug console print that enables printing all recieved OSC commands.
        "OSCBridgeDEBUG": true/false
       
    IP/port to listen OSC commands from.
        "OSCBListenIP": "127.0.0.1", "OSCBListenPort": 9001

    Recieves and re-transmits OSC data
        "OSCPass": false/true 

    Ip and port to send the OSC messages.
        "OSCSendIP": "127.0.0.1","OSCSendPort": 9000

    Listens for configured OSC adresses and controlls toys sending request [Intirface](https://intiface.com/)
        "OSCtoButtplug": false/true

    Groups multiple simple processes. (Pulse, Respond)
        "OSCProcess": false/true
    

## OSCtoButplug :
Requires [Intiface](https://intiface.com/) to be running and with websockets active to control supported sex toys.

Listens to commands coming from the configured OSC addresses to control devices.

Available commands: Stop, Vibrate, Rotate.

The configuration file maps OSC address, device name to control and the command [OSC adrres, device name, command]

The first time you connect a device a new file "devicename".json
will be created with the device name and its available commands.

### Commands:
#### Stop : 
Stops all movement from a device if it receives any value on the configured address.

  Stops the device named "XBox (XInput) Compatible Gamepad 1" when the OSC address/test/s sends any value.
  
    ["/test/s", "XBox (XInput) Compatible Gamepad 1", ["Stop"]]
#### Vibrate : 
Vibrates configured motor/s to the OSC address value (float from 0.0 to 1.0). All or individual motors can be set.

    [OSC address, device name, ["Vibrate", motors]] 

where motors can be set to "all", or a list of motor indexes [0,1,2, ...]

   Vibrate: (tested with lovense edge and xbox controller)
                      
Sets all motors to vibrate at the OSC value from /test/va for the first xbox controller.

    ["/test/va", "XBox (XInput) Compatible Gamepad 1", ["Vibrate", "all"]]
                          
Sets the first motor to vibrate at the OSC value from /test/vb.

    ["/test/vb", "XBox (XInput) Compatible Gamepad 1", ["Vibrate", [0]]]
                          
Sets the first and second motors to vibrate at the OSC value from /test/vc.

    ["/test/vc", "XBox (XInput) Compatible Gamepad 1", ["Vibrate", [0,1]]]

#### Rotate : 
Rotates configured motor/s to the OSC address value (float from 0.0 to 1.0) and a set direction (true/false). 
All or individual motors can be set, and it's direction. 

[OSC address, device name, ["Rotate", motors]] 

where motors can be set to "allcw" (all clockwise),"allccw" (all counterclockwise, 
or a list of motor indexes and direction to rotate them where True = clockwise False = Counterclockwise. 

    [[0,True],[1,False],[2,True], ...]

Rotate: ( not tested jet with real toys).

Rotate all motors clockwise for the device "fake rotating device" at the OSC value from /rotatea.

    ["/rotatea", "fake rotating device", ["Rotate", "allcw"]]
                          
Rotate all motors counterclockwise for the device "fake rotating device" at the OSC value from /rotateb.
                      
    ["/rotateb", "fake rotating device", ["Rotate", "allccw"]]
                          
Rotate second motor counterclockwise for the device "fake rotating device" at the OSC value from /rotatec.

    ["/avatar/parameters/rotatec", "fake rotating device", ["Rotate", [[1, False]]]]
                          
Rotate first motor counterclockwise, and the second motor clockwise for the device "fake rotating device" at the OSC value from /rotated.

    ["/avatar/parameters/rotated", "fake rotating device", ["Rotate", [[0, False], [1, True]]]]


## Process :
Group of independent processes
Configuration file "OSCProcessMapping"

    ["OSC address", "Command Name", [Command data]]

#### Pulse :
Senda a message to an OSC adress every X seconds forever.

    ["OSC address", "pulse", [interval in seconds, Data do send]]

Sends a message to "/avatar/parameters/Test" every 10 seconds with the value "testing"

    ["/avatar/parameters/Test", "pulse", [10, "testing"]]

#### Respond:
Sends a message with a preconfigured value when any message is recieved at the OSC address.
 
    ["OSC adress to listen at","respond",[data to send,"OSC adress to reply to"]]

Listen on any message from "/avatar/parameters/Testd" and sends a 1 to "/avatar/parameters/Testda"

    ["/avatar/parameters/Testd","respond",[1,"/avatar/parameters/Testda"]]

All Process commands are saved in the sale .json file.

        [
            "/avatar/parameters/Testa",
            "pulse",
            [
                30,
                1
            ],
            "/avatar/parameters/Testa",
            "pulse",
            [
                15,
                0
            ],
            "/avatar/parameters/Testc",
            "pulse",
            [
                10,
                false
            ],
            "/avatar/parameters/Testc",
            "pulse",
            [
                15,
                true
            ],
            "/avatar/parameters/Testd",
            "respond",
            [
                1,
                "/avatar/parameters/Testda"
            ]
        ]