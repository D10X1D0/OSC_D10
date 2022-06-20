# OSC_D10
python OSC bridge to other apps
OSC server that can listen and comunicate with other apps:
  Configured in Mainconfig.json to enable/disable loading diferent modules (true=enabled,false=disabled).
    "OSCBridge": false/true . Enables/disables the OSC server that's listening and sending the incoming data to be processed to other modules.
    "OSCBListenIP": "127.0.0.1" "OSCBListenPort": 9001 . IP/port to listen OSC commands from.
    "OSCPass": false/true . Recieves and re-transmits OSC data
    "OSCSendIP": "127.0.0.1","OSCSendPort": 9000 . Ip and port to send the re-transmision.
    "OSCtoButtplug": false/true, listens for configured OSC adresses and controlls toys sending request [Interface](https://intiface.com/)
    "InterfaceWS": "127.0.0.1:12345"  Websocket ip and port where interface will be listening.
    "OSCprocess": false/true. Sends its OSC data to the same "OSCSendIP"/"OSCSendPort" destination.
    
OSCPass: 

  Listens to a osc acress, re-transmits it to a diferent one or passes the adress/value to other modules to be processed.
    The configuration file stores OSC adresses a list [OSCorigin, OSCdestination, origin2, destination2, ...]
        example configuration file:
          from /test/a to /test/b : 
              ["/test/a", "/test/b"]
          from /test/a to /test/b, and from /test/c to /test/d
              ["/test/a", "/test/b", "/test/c", "/test/d"]
              
OSCtoButplug :

  Requires [Interface](https://intiface.com/) to be running and with websockets active to control suported sex toys.
  Listens to commands coming from the configured OSC adresses to controll devices.
      Available commands: Stop, Vibrate, Rotate.
        The configuration file maps OSC adress, device name to controll and the command [OSCadrres, device name, command]
          commands:
              Stop : Stops all movement from a device.
              Vibrate : Vibrates configured motor/s to the OSC adress value. All or individual motors can be set.
              Rotate : Rotates configured motor/s to the OSC adress value and a set direction. All or individual motors can be set, and it's direction.
                configuration file examples:
                Vibrate: (tested with lovense edge and xbox controller)
                    Stops the device named "XBox (XInput) Compatible Gamepad 1" when the OSC adress/test/s sends any value.
                        ["/test/s", "XBox (XInput) Compatible Gamepad 1", ["Stop"]]
                    Sets all motors to vibrate at the OSC value from /test/va.
                        ["/test/va", "XBox (XInput) Compatible Gamepad 1", ["Vibrate", "all"]]
                    Sets the first motor to vibrate at the OSC value from /test/vb.
                        ["/test/vb", "XBox (XInput) Compatible Gamepad 1", ["Vibrate", [0]]]
                    Sets the first and second motors to vibrate at the OSC value from /test/vc.
                        ["/test/vc", "XBox (XInput) Compatible Gamepad 1", ["Vibrate", [0,1]]]
                Rotate: ( not tested jet with real toys)
                    Rotate all motors clockwise for the device "fake rotating device" at the OSC value from /rotatea.
                        ["/rotatea", "fake rotating device", ["Rotate", "allcw"]]
                    Rotate all motors counterclockwise for the device "fake rotating device" at the OSC value from /rotateb.
                        ["/rotateb", "fake rotating device", ["Rotate", "allccw"]]
                    Rotate second motor clockwise for the device "fake rotating device" at the OSC value from /rotatec.
                        ["/avatar/parameters/rotatec", "fake rotating device", ["Rotate", [[1, False]]]]
                    Rotate first motor counterclockwise, and the second motor clockwise for the device "fake rotating device" at the OSC value from /rotated.
                        ["/avatar/parameters/rotated", "fake rotating device", ["Rotate", [[0, False], [1, True]]]]
                  
OSCprocess :
    Module that can run different processes.
      configured in processMaping.json
    Implemented processes:
        Pulse: sends OSC messages to a adress with a custom every x seconds. [OSCAdress, "pulse", [delay in seconds, value]]
          Send the value 2 every 30 seconds to the OSC adress "/beat"
            ["/beat", "pulse", [30, 1]]
        Respond: listens for a value comming from a OSCadress and sends back a configured adress/value.
          Send True to the OSCadress "/b" when a value of 1 is recieved from "/a"
            ["/a", "respond", [1, True, "/b"]
        
                        
