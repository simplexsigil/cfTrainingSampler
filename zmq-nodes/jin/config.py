

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

# Frequency of control command. Should be about 100 hz.
command_frequency = 1 / 0.01

# Time to wait for a connoection retry for zmq connections in seconds
zmq_connection_repeat_pause = 5

# Timeout to wait for a connection retry for crazyflie cf radio connections in seconds
cf_connection_repeat_pause = 5