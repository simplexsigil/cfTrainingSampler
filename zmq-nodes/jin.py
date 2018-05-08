import evdev
import sys
import time
import threading
import zmq

from evdev import InputDevice, categorize, ecodes

SRV_ADDR = "tcp://127.0.0.1"
CF_URI = "radio://0/80/2M"

max_pitch_deg = 30
max_roll_deg = 30
max_yaw_rate_deg = 180
max_thrust = 0xFFFF

max_xv = 1
max_yv = 1
max_z = 3

cut_off_roll = 5
cut_off_pitch = 5
cut_off_yaw = 20

cut_off_xv = 0.1
cut_off_yv = 0.1

lock = threading.Lock()

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

class ZMQController(threading.Thread):
    def __init__(self, server_address, crazyflie_uri):
        threading.Thread.__init__(self)
        self.keep_running = True
        self.server_address = server_address
        self.crazyflie_uri = crazyflie_uri

        self.context = zmq.Context()


    def close_connection(self, client_conn):
        disconnect_cmd = {
            "version": 1,
            "cmd": "disconnect",
            "uri": "{}".format(self.crazyflie_uri)
        }

        print("Checking and closing old connections to ".format(disconnect_cmd["uri"]), end=' ')
        client_conn.send_json(disconnect_cmd)

        resp = client_conn.recv_json()

    def connect_to_cf(self, client_conn):
        connect_cmd = {
            "version": 1,
            "cmd": "connect",
            "uri": "{}".format(self.crazyflie_uri)
        }

        print("Connecting to {} ...".format(connect_cmd["uri"]), end=' ')
        client_conn.send_json(connect_cmd)

        resp = client_conn.recv_json()

        if resp["status"] != 0:
            print("Connection status: {}".format(resp["msg"]))
            sys.exit(1)

    def unlock_thrust_protection(self, ctrl_conn):
        thrust_unlock = {
            "version": 1,
            "roll": 0,
            "pitch": 0,
            "yaw": 0,
            "thrust": 0
        }

        for _ in range(0, 10):
            time.sleep(0.01)
            ctrl_conn.send_json(thrust_unlock)

        print("Sending thrust unlocking commands.")


    def send_cmd(self, ctrl_conn, tick):
        with lock:
            ctrl_conn.send_json(shared_cmd)

            if tick % 10 == 0:
                print("\033[2K", end='')
                print("\r  \rSent: " + str(shared_cmd), end='')

    def loop_cmd_sending(self, ctrl_conn):
        tick = 0

        while self.keep_running:
            time.sleep(0.01)
            self.send_cmd(ctrl_conn, tick)
            tick += 1

        print("\n")

    def run(self):

        client_conn = self.context.socket(zmq.REQ)
        client_conn.connect("{}:2000".format(self.server_address))

        self.close_connection(client_conn)

        self.connect_to_cf(client_conn)

        time.sleep(0.3)

        ctrl_conn = self.context.socket(zmq.PUSH)
        ctrl_conn.connect("{}:2004".format(self.server_address))

        self.unlock_thrust_protection(ctrl_conn)

        time.sleep(0.3)

        self.loop_cmd_sending(ctrl_conn)


class JoystickReader:

    def __init__(self, device):
        self.device = device

    def read_joystick(self):
        for event in self.device.read_loop():
            # The following are the event codes for a XBOX one Controller. It might have to be adjusted for other controllers.
            with lock:
                if event.type == ecodes.EV_ABS:

                    if event.code == ecodes.ABS_X: # Left x-axis.
                        roll = int(event.value / 32768.0 * max_roll_deg)
                        yvel = event.value / 32768.0 * max_yv

                        shared_cmd["roll"] = roll if abs(roll) > cut_off_roll else 0
                        shared_cmd["yvel"] = -yvel if abs(yvel) > cut_off_yv else 0

                    if event.code == ecodes.ABS_Y: # Left y-axis
                        pitch = int(event.value / 32768.0 * max_pitch_deg)
                        xvel = event.value / 32768.0 * max_xv

                        shared_cmd["pitch"] = -pitch if abs(pitch) > cut_off_pitch else 0
                        shared_cmd["xvel"] = -xvel if abs(xvel) > cut_off_xv else 0

                    if event.code == ecodes.ABS_RX: # Right x-axis
                        yaw = int(event.value / 32768.0 * max_yaw_rate_deg)

                        shared_cmd["yaw"] = yaw if abs(yaw) > cut_off_yaw else 0

                    if event.code == ecodes.ABS_RZ: # Right backside trigger
                        thrust = int(event.value / 1024.0 * max_thrust)
                        z = event.value / 1024.0 * max_z

                        shared_cmd["thrust"] = thrust
                        shared_cmd["z"] = z


                if event.type == ecodes.EV_KEY:
                    if event.code == ecodes.BTN_Y and event.value is 1: # Switch hover mode
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

    zmq_publisher = ZMQController(SRV_ADDR, CF_URI)

    zmq_publisher.start()

    keep_running = True

    while keep_running:
        try:
            js_reader.read_joystick()
        except KeyboardInterrupt:
            print("Closing zmq joystick controller.")
        finally:
            print("Stopping zmq thread...")
            zmq_publisher.keep_running = False
            zmq_publisher.join(3)
            if zmq_publisher.is_alive():
                print("Failed to stop zmq thread properly.")
            else:
                print("Stopped zmq thread.")

            keep_running = False


if __name__ == "__main__":
    main()