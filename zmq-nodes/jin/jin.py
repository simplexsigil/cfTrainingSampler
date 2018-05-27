import evdev
import sys
import threading
import config as cnf
import time
import zmq
from cfwrapper import ClientConnection

from joystick_reader import JoystickReader
from zmq_connector import ZMQControlConnector
from logging_connector import LogConnector

# This is the shared control command which is read from input device and then sent via zmq. There is no queue since we
# only send the most recent command.
shared_cmd = {
    "version": 1,
    "roll": 0,
    "pitch": 0,
    "yaw": 0,
    "thrust": 0,
    "hovermode": False,
    "xvel": 0,
    "yvel": 0,
    "z": 0,
    "is_logging": False
}

# For synchronization between joystick input thread and and zmq control sender thread.
shared_command_lock = threading.Lock()

def establish_cf_connection(cf_connector):
    # Connect to crazy flie and unlock
    response = cf_connector.disconnectFromCF()

    if response["status"] != 0:
        raise Exception("Failed to disconnect from CF: " + response["msg"])
    else:
        print("Disconnected old clients from CF")

    response = cf_connector.connectToCF()
    if response["status"] != 0:
        raise Exception("Failed to connect to CF: " + response["msg"])
    else:
        print("Connected to cf!")

def main():
    devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]

    for device in devices:
        print(device.fn, device.name, device.phys)

    if len(devices) is 0:
        print("No input device found. Exiting.")
        sys.exit(1)

    if len(devices) is 1:
        print("Found only one device. Using it as default.")
        device_idx = 0

    if len(devices) > 1:
        device_idx = input("Enter index of device:")

    device = devices[device_idx]

    print("Selected device: " + str(device))

    # print(device.capabilities(verbose=True))

    cf_connector = ClientConnection(zmq.Context(), cnf.SRV_ADDR, cnf.CF_URI)
    establish_cf_connection(cf_connector)


    # Initialize and start joystick reader thread which continuously reads input values from joystick and updates
    # the current control command.
    js_reader = JoystickReader(device, shared_cmd, shared_command_lock)
    js_reader.daemon = True
    js_reader.start()

    # Initialize and start cfzmq connector thread which continuously sends our control commands.
    cfzmq_connector = ZMQControlConnector(cnf.SRV_ADDR, cnf.CFZMQ_CONTROL_PORT, cnf.CF_URI,
                                          shared_cmd, shared_command_lock, cnf.command_frequency)
    cfzmq_connector.daemon = True
    cfzmq_connector.start()

    # Initialize and start log connector to control start and stop of log sequences.
    log_connector = LogConnector(cnf.LOG_SRV_ADDR, cnf.LOG_CONTROL_PORT,
                                 shared_cmd, shared_command_lock, cnf.command_frequency)
    log_connector.daemon = True
    log_connector.start()

    quit = False

    while not quit:
        try:
            time.sleep(60)
        except KeyboardInterrupt:
            quit = True
            cfzmq_connector.set_keep_running(False)
            js_reader.set_keep_reading(False)
            log_connector.set_keep_running(False)

            # We do not wait for joystick reader, since it does not have dangling connections opened.
            # Also it is currently blocking in loop waiting for input events (blocking io) and does not join.

            cfzmq_connector.join(5)
            log_connector.join(5)

    if cfzmq_connector.is_alive():
        print("Failed to stop zmq thread properly.")

    if log_connector.is_alive():
        print("Failed to stop log control thread properly.")

    cf_connector.disconnect()

if __name__ == "__main__":
    main()
