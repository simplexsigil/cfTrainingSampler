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
