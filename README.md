# Crazyflie Training Sampler
This repository contains python scripts to control the crazyflie via computer and sample training data.

For more information about our project, please have a look at our documentation repository [crazyflie-documents](https://github.com/simplexsigil/crazyflie-documents).

## cflib based scripts
This folder contains python scripts which use cflib (Bitcrazes library for controlling the crazyflie) directly in order to send commands to the crazyflie.

Please note, that there can only be one simultaneous connection to a crazyflie, therefore it is not possible to have two separate applications running and connecting to the cf for example to add a separate logger.

## ZMQ based scripts
This folder contains python scripts which work with ZMQ, a publish/subribe like technology. Bitcraze has provided a wrapper around the cflib which can be used to control the crazyflie via zmq messages.
The advantage is, that multiple nodes can connect to the cfzmq node (the wrapper around cflib) and control the crazyflie or exchange data in a loosely coupled way.

Testing the cfzmq server, we found that it does not support flying the crazyflie in hovermode, we therefore forked the repository containing the cfzmq server and added some lines to enable hovermode control via ZMQ:
https://github.com/simplexsigil/crazyflie-clients-python

## Installing ZMQ
Just run the script setup-zmq.sh
For python: sudo pythom -m pip install zmq

## ZMQ as input method for the python client 
Enable by setting "enable_zmq_input": true in the config file, by default located at /home/user/.config/cfclient/config.json
Start the client, choose Input device = ZMQ@tcp:127.0.0.1:1122
For example use, refer to the test scripts in zmq-based/test

### zmq-node-joystick-xboxone
This zmq node detects input devices and is able to translate and send joystick commands to cfzmq in order to control the crazyflie.

**This script does work with the standard cfzmq node provided by bitcraze, but control is only possible in standard mode, not in hovermode. Use the cfzmq implementation from our own repository in order to use hovermode.**

**It will close and reopen any existing connection to the specified crazyflie in order to avoid problems with lingering connections. Please consider this, since it might interfer with other nodes, which already opened up a connection. Maybe it is better to make a separate script which only opens and closes connections.**

It is designed to work with an xbox one controller, roll and pitch are mapped to the left joystick's x and y axis, yaw is mapped to the right joystick's x axis, thrust is mapped to the right trigger and button y switches hovermode.
The script shows the currently sent cf commands on the console.

Please make a separate file if you use another controller or transfer the controller specific parts of the sript in external files which can be switched easily.

The settings inlude the cfzmq server address and the crazyflie connection string:
```python
SRV_ADDR = "tcp://127.0.0.1"
CF_URI = "radio://0/80/2M"
```

If the cfzmq server is running, establishing control with this script should be possible fast and smoothly.
