import threading
import zmq
import time
import config as cnf


class ZMQControlConnector(threading.Thread):
    """ Provides the capability to establish a connection to a cfzmq server, continously send control commands and
    close the connection after use.
    """

    def __init__(self, host, port, crazyflie_uri, shared_command, shared_command_lock, command_frequency):
        """
        Initializes this object and prepares it for connection.
        :param server_address: The address of the cfzmq server.
        :param crazyflie_uri: The uri of the crazyflie we want to connect to.
        """
        threading.Thread.__init__(self)

        self.keep_running_lock = threading.Lock()
        self.keep_running = True

        self.host = host
        self.port = port

        self.crazyflie_uri = crazyflie_uri

        self.context = zmq.Context()

        self.control_socket = None

        self.shared_command = shared_command
        self.shared_command_lock = shared_command_lock
        self.command_frequency = command_frequency

    def get_keep_running(self):
        with self.keep_running_lock:
            return self.keep_running

    def set_keep_running(self, keep_running):
        with self.keep_running_lock:
            self.keep_running = keep_running

    def open_socket(self):

        # Push socket without response.
        self.control_socket = self.context.socket(zmq.PUSH)
        self.control_socket.setsockopt(zmq.RCVTIMEO, 300)
        self.control_socket.setsockopt(zmq.SNDTIMEO, 300)
        self.control_socket.connect("{}:{}".format(self.host, self.port))

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
        with self.shared_command_lock:
            self.control_socket.send_json(self.shared_command)

            # Update status message of last sent command.
            if tick % 10 == 0:
                print("\033[2K", end='')
                print("\r  \rSent: " + str(self.shared_command), end='')

    def start_cmd_sending_loop(self):
        """Start a continuous loop of sending control commands until it is stopped via self.stop_cmd_sending_loop()."""
        tick = 0

        keep_running = True

        # Indicate to outside thread that loop will continue.
        self.set_keep_running(keep_running)

        while keep_running:
            time.sleep(1 / self.command_frequency)

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
            self.open_socket()
        except zmq.ZMQError as e:
            print(e)
            print("Could not establish connections to the cfzmq server.\n")
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

        # print("Exiting zmq control connection thread.")
