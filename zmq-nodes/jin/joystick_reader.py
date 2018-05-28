import threading
import config as cnf

from evdev import ecodes


class JoystickReader(threading.Thread):

    def __init__(self, device, shared_command, shared_command_lock):
        threading.Thread.__init__(self)

        self.device = device
        self.shared_command = shared_command
        self.shared_command_lock = shared_command_lock
        self.keep_reading = True
        self.keep_reading_lock = threading.Lock()

    def get_keep_reading(self):
        with self.keep_reading_lock:
            return self.keep_reading

    def set_keep_reading(self, val):
        with self.keep_reading_lock:
            self.keep_reading = val

    def read_joystick(self):
        # TODO: Thread loop does not stop if waiting for event. Needs a button push on the controller to stop.
        # For now we just ignore it and kill the thread on exit. Better solution: use asyncio instead of event polling:
        # https://docs.python.org/3/library/asyncio.html#module-asyncio
        for event in self.device.read_loop():
            if not self.get_keep_reading():
                break

            # The following are the event codes for a XBOX one Controller. It might have to be adjusted for other controllers.
            with self.shared_command_lock:
                if event.type == ecodes.EV_ABS:

                    if event.code == ecodes.ABS_X:  # Left x-axis.
                        roll = int(event.value / 32768.0 * cnf.max_roll_deg)
                        yvel = event.value / 32768.0 * cnf.max_yv

                        self.shared_command["roll"] = roll if abs(roll) > cnf.cut_off_roll else 0
                        self.shared_command["yvel"] = -yvel if abs(yvel) > cnf.cut_off_yv else 0

                    if event.code == ecodes.ABS_Y:  # Left y-axis
                        pitch = int(event.value / 32768.0 * cnf.max_pitch_deg)
                        xvel = event.value / 32768.0 * cnf.max_xv

                        self.shared_command["pitch"] = -pitch if abs(pitch) > cnf.cut_off_pitch else 0
                        self.shared_command["xvel"] = -xvel if abs(xvel) > cnf.cut_off_xv else 0

                    if event.code == ecodes.ABS_RX:  # Right x-axis
                        yaw = int(event.value / 32768.0 * cnf.max_yaw_rate_deg)

                        self.shared_command["yaw"] = yaw if abs(yaw) > cnf.cut_off_yaw else 0

                    if event.code == ecodes.ABS_RZ:  # Right backside trigger
                        thrust = int(event.value / 1024.0 * cnf.max_thrust)
                        z = event.value / 1024.0 * cnf.max_z

                        self.shared_command["thrust"] = thrust
                        self.shared_command["z"] = z

                if event.type == ecodes.EV_KEY:
                    if event.code == ecodes.BTN_Y and event.value is 1:  # Switch hover mode
                        self.shared_command["hovermode"] = not self.shared_command["hovermode"]

    def run(self):
        while self.get_keep_reading():
            self.read_joystick()

        # print("Exiting joystick reader thread.")