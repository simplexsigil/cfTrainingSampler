import evdev
import sys
import time
import threading
import zmq

from evdev import InputDevice, categorize, ecodes

# The address of the cfzmq server to connect to.
SRV_ADDR = "tcp://127.0.0.1"

# The address of the crazyflie we connect to.
CF_URI = "radio://0/80/2M"

# Limits for control values which make flying for a human pilot easier.
max_pitch_deg = 30
max_roll_deg = 30
max_yaw_rate_deg = 180
max_thrust = 0xFFFF

# Limits in hover mode.
max_xv = 1
max_yv = 1
max_z = 3

# These are cut-off values which eliminate jitter from the controller input when sending zero commands.
cut_off_roll = 5
cut_off_pitch = 5
cut_off_yaw = 20

cut_off_xv = 0.1
cut_off_yv = 0.1

# For synchronization between joystick input thread and and zmq control sender thread.
shared_command_lock = threading.Lock()

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
    "z": 0
}

# Frequency of control command. Should be about 100 hz.
command_frequency = 1 / 0.01


class ZMQControlConnector(threading.Thread):
    """ Provides the capability to establish a connection to a cfzmq server, continously send control commands and
    close the connection after use.
    """

    def __init__(self, server_address, crazyflie_uri):
        """
        Initializes this object and prepares it for connection.
        :param server_address: The address of the cfzmq server.
        :param crazyflie_uri: The uri of the crazyflie we want to connect to.
        """
        threading.Thread.__init__(self)
        self.daemon = True

        self.keep_running_lock = threading.Lock()
        self.keep_running = True

        self.server_address = server_address
        self.crazyflie_uri = crazyflie_uri

        self.context = zmq.Context()

        self.command_socket = None
        self.control_socket = None

    def get_keep_running(self):
        with self.keep_running_lock:
            return self.keep_running

    def set_keep_running(self, keep_running):
        with self.keep_running_lock:
            self.keep_running = keep_running

    def open_sockets(self):
        # Request-response socket.
        self.command_socket = self.context.socket(zmq.REQ)
        self.command_socket.setsockopt(zmq.RCVTIMEO, 5000)
        self.command_socket.setsockopt(zmq.SNDTIMEO, 5000)
        self.command_socket.connect("{}:2000".format(self.server_address))

        # Push socket without response.
        self.control_socket = self.context.socket(zmq.PUSH)
        self.control_socket.setsockopt(zmq.RCVTIMEO, 300)
        self.control_socket.setsockopt(zmq.SNDTIMEO, 300)
        self.control_socket.connect("{}:2004".format(self.server_address))

    def loop_till_connect(self):
        # Closes any dangling connections from previous sessions.
        self.close_cf_connection()

        keep_connecting = True

        # Connects to the crazyflie.
        while not self.connect_to_cf() and keep_connecting:
            keep_connecting = self.get_keep_running()

            print("Connection to crazyflie was unsuccessful, trying again in 2 seconds...")
            time.sleep(2)

    def close_cf_connection(self):
        """Close the crazyflie connection on the cfzmq server side."""

        disconnect_cmd = {
            "version": 1,
            "cmd": "disconnect",
            "uri": "{}".format(self.crazyflie_uri)
        }

        print("Checking and closing old connections to {}".format(disconnect_cmd["uri"]))
        self.command_socket.send_json(disconnect_cmd)
        resp = self.command_socket.recv_json()

        # print(resp)

    def connect_to_cf(self):
        """Connect to the crazyflie on the cfzmq server side."""

        connect_cmd = {
            "version": 1,
            "cmd": "connect",
            "uri": "{}".format(self.crazyflie_uri)
        }

        print("Connecting to {} ...".format(connect_cmd["uri"]), end=' ')
        self.command_socket.send_json(connect_cmd)
        resp = self.command_socket.recv_json()

        if resp["status"] != 0:
            print("Connection status: {}".format(resp["msg"]))
            return False
        else:
            return True

    def unlock_thrust_protection(self):
        """Unlock the thrust protection on the crazyflie which would otherwise ignore any commands
        sent after initial startup.
        """

        thrust_unlock = {
            "version": 1,
            "roll": 0,
            "pitch": 0,
            "yaw": 0,
            "thrust": 0
        }

        print("Sending thrust unlocking commands.")

        for _ in range(0, 10):
            time.sleep(0.01)
            self.control_socket.send_json(thrust_unlock)

    def send_cmd(self, tick):
        """Send a control command to the crazyflie. The control socket has to be connected."""
        with shared_command_lock:
            self.control_socket.send_json(shared_cmd)

            # Update status message of last sent command.
            if tick % 10 == 0:
                print("\033[2K", end='')
                print("\r  \rSent: " + str(shared_cmd), end='')

    def start_cmd_sending_loop(self):
        """Start a continuous loop of sending control commands until it is stopped via self.stop_cmd_sending_loop()."""
        tick = 0

        keep_running = True

        # Indicate to outside thread that loop will continue.
        self.set_keep_running(keep_running)

        while keep_running:
            time.sleep(1 / command_frequency)

            self.send_cmd(tick)
            tick += 1

            # Thread safe access to run indicator.
            keep_running = self.get_keep_running()

        print("Stopped command sending loop.")

    def stop_cmd_sending_loop(self):
        """Stops the cmd sending loop."""

        # Thread safe access to run indicator.
        self.set_keep_running(False)

    def run(self):

        # Open up zmq-connections to the cfzmq crazyflie cfradio-connection and control channels.
        try:
            self.open_sockets()
        except zmq.ZMQError as e:
            print(e)
            print("Could not establish connections to the cfzmq server.")
            return

        # Connecting to the crazyflie via zmq messages.
        try:
            self.loop_till_connect()
        except zmq.ZMQError as e:
            print(e)
            print("Could not (re-)open connection to crazyflie on cfzmq server side due to a zmq error.")
            return

        time.sleep(0.3)

        if not self.get_keep_running():
            return

        # Sending control commands.
        try:
            # Needed, so the cf won't ignore our commands.
            self.unlock_thrust_protection()

            time.sleep(0.3)

            # Keep sending our control command (Blocking until external stop).
            self.start_cmd_sending_loop()
        except zmq.ZMQError as e:
            print(e)
            print("A zmq connection error ocurred while sending control commands.")

        # Closing cf connection.
        try:
            self.close_cf_connection()

        except zmq.ZMQError as e:
            print(e)
            print("Disconnecting the crazyflie failed due to a zmq error.")

        print("Exiting zmq control connection thread.")


class JoystickReader:

    def __init__(self, device):
        self.device = device

    def read_joystick(self):
        for event in self.device.read_loop():
            # The following are the event codes for a XBOX one Controller. It might have to be adjusted for other controllers.
            with shared_command_lock:
                if event.type == ecodes.EV_ABS:

                    if event.code == ecodes.ABS_X:  # Left x-axis.
                        roll = int(event.value / 32768.0 * max_roll_deg)
                        yvel = event.value / 32768.0 * max_yv

                        shared_cmd["roll"] = roll if abs(roll) > cut_off_roll else 0
                        shared_cmd["yvel"] = -yvel if abs(yvel) > cut_off_yv else 0

                    if event.code == ecodes.ABS_Y:  # Left y-axis
                        pitch = int(event.value / 32768.0 * max_pitch_deg)
                        xvel = event.value / 32768.0 * max_xv

                        shared_cmd["pitch"] = -pitch if abs(pitch) > cut_off_pitch else 0
                        shared_cmd["xvel"] = -xvel if abs(xvel) > cut_off_xv else 0

                    if event.code == ecodes.ABS_RX:  # Right x-axis
                        yaw = int(event.value / 32768.0 * max_yaw_rate_deg)

                        shared_cmd["yaw"] = yaw if abs(yaw) > cut_off_yaw else 0

                    if event.code == ecodes.ABS_RZ:  # Right backside trigger
                        thrust = int(event.value / 1024.0 * max_thrust)
                        z = event.value / 1024.0 * max_z

                        shared_cmd["thrust"] = thrust
                        shared_cmd["z"] = z

                if event.type == ecodes.EV_KEY:
                    if event.code == ecodes.BTN_Y and event.value is 1:  # Switch hover mode
                        shared_cmd["hovermode"] = not shared_cmd["hovermode"]


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

    js_reader = JoystickReader(device)

    print("Selected device: " + str(device))

    # print(device.capabilities(verbose=True))

    # Initialize and start cfzmq connector thread which continously sends our control commands.
    cfzmq_connector = ZMQControlConnector(SRV_ADDR, CF_URI)
    cfzmq_connector.start()

    keep_reading = True

    while keep_reading:
        try:
            js_reader.read_joystick()
        except KeyboardInterrupt:
            if cfzmq_connector.is_alive():
                cfzmq_connector.stop_cmd_sending_loop()
            print("Closing zmq joystick controller.")
        finally:
            print("Stopping zmq thread...")
            cfzmq_connector.stop_cmd_sending_loop()
            cfzmq_connector.join(6)
            if cfzmq_connector.is_alive():
                print("Failed to stop zmq thread properly.")
            else:
                print("Stopped zmq thread.")

            keep_reading = False
            print("Exiting program")
            sys.exit(0)


if __name__ == "__main__":
    main()
