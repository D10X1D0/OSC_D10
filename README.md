# OSC_D10
Python OSC bridge to other apps and send OSC messages back. 
Curretly able to talk with [Buttplug.io](https://buttplug.io/) , tested with [Interface](https://intiface.com/)
If no configuration files are found, new .json configuration files with examples will be created.

## OSCBridge:
OSC server that can listen and communicate with other apps. 
Sends a 1 to the "/OSCBridge" OSCSendIp when i'ts running and a 0 when it shuts down.

Configured in Mainconfig.json to enable/disable loading different modules (true=enabled, false=disabled).
        
    Enables/disables the OSC server that's listening and sending the incoming data to be processed to other modules.
      "OSCBridge": false/true

    IP/port to listen OSC commands from.
      "OSCBListenIP": "127.0.0.1" "OSCBListenPort": 9001

    Recieves and re-transmits OSC data
      "OSCPass": false/true 

    Ip and port to send the re-transmision.
      "OSCSendIP": "127.0.0.1","OSCSendPort": 9000

    Listens for configured OSC adresses and controlls toys sending request [Interface](https://intiface.com/)
      "OSCtoButtplug": false/true

    Websocket ip and port where interface will be listening.
      "InterfaceWS": "127.0.0.1:12345"

    Sends its OSC data to the same "OSCSendIP"/"OSCSendPort" destination.
      "OSCprocess": false/true. 
    

## OSCtoButplug :
Requires [Interface](https://intiface.com/) to be running and with websockets active to control supported sex toys.

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


## OSCPass:
Listens to a osc address, re-transmits it to a different one or passes the address/value to other modules to be processed.

The configuration file stores OSC addresses a list [OSCorigin, OSCdestination, origin2, destination2, ...]

Retransmit from OSC address /test/a to /test/b :

                ["/test/a", "/test/b"]
                
Retransmit from OSC address, and from /test/c to /test/d

                ["/test/a", "/test/b", "/test/c", "/test/d"]

                  
## OSCprocess :
Module that can run different processes.

Configured in processMaping.json.

Implemented processes.

### Pulse: 
Sends OSC messages to a adress with a custom every x seconds. [OSCAdress, "pulse", [delay in seconds, value]]

Send the value 2 every 30 seconds to the OSC address "/beat".

              ["/beat", "pulse", [30, 2]]
              
### Respond:
Listens for a value comming from a OSCadress and sends back a configured address/value.
  
Send True to the OSCadress "/b" when a value of 1 is received from "/a"
            
              ["/a", "respond", [1, True, "/b"]

                        
