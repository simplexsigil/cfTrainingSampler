import threading
import zmq
import time
import config as cnf


class LogConnector(threading.Thread):

    def __init__(self, host, port, shared_command, shared_command_lock, command_frequency):
        threading.Thread.__init__(self)

        self.keep_running_lock = threading.Lock()
        self.keep_running = True

        self.host = host
        self.port = port

        self.context = zmq.Context()

        self.log_control_socket = None

        self.shared_command = shared_command
        self.shared_command_lock = shared_command_lock
        self.command_frequency = command_frequency

        self.is_logging = False

    def get_keep_running(self):
        with self.keep_running_lock:
            return self.keep_running

    def set_keep_running(self, keep_running):
        with self.keep_running_lock:
            self.keep_running = keep_running

    def update_log_mode(self):
        with self.shared_command_lock:
            changed = self.is_logging == self.shared_command["is_logging"]
            self.is_logging = self.shared_command["is_logging"]
            return changed

    def send_log_mode(self):
        if self.is_logging:
            self.log_control_socket.send_json({"action": "start_logging"})
        else:
            self.log_control_socket.send_json({"action": "stop_logging"})

    def open_socket(self):
        # Request-response socket.
        self.log_control_socket = self.context.socket(zmq.REQ)
        self.log_control_socket.setsockopt(zmq.RCVTIMEO, 5000)
        self.log_control_socket.setsockopt(zmq.SNDTIMEO, 5000)
        self.log_control_socket.connect("{}:{}".format(self.host, self.port))

    def start_cmd_sending_loop(self):
        """Start a continuous loop of sending control commands until it is stopped via self.stop_cmd_sending_loop()."""
        tick = 0

        keep_running = True

        # Indicate to outside thread that loop will continue.
        self.set_keep_running(keep_running)

        while keep_running:
            time.sleep(1 / self.command_frequency)

            if self.update_log_mode():
                self.send_log_mode(tick)
            tick += 1

            # Thread safe access to run indicator.
            keep_running = self.get_keep_running()

        print("Stopped log control sender loop.")

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

        if not self.get_keep_running():
            return

        # Sending control commands.
        try:
            # Keep sending our control command (Blocking, until external stop).
            self.start_cmd_sending_loop()
        except zmq.ZMQError as e:
            print(e)
            print("A zmq connection error ocurred while sending control commands.")
