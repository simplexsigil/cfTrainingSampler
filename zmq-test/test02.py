## this script will send a constant thrust=30 to the drone

import time

try:
    import zmq
except Exception as e:
    raise Exception("ZMQ library probably not installed ({})".format(e))

context = zmq.Context()
sender = context.socket(zmq.PUSH)
bind_addr = "tcp://127.0.0.1:1212"
sender.connect(bind_addr)

thrust_step = 100
thrust_max = 30000
thrust_min = 20000
thrust = thrust_min

cmdmess = {
    "version": 1,
    "ctrl": {
        "roll": 0.0,
        "pitch": 0.0,
        "yaw": 0.0,
        "thrust": 30
        }
}

print("starting to send control commands!")

# Unlocking thrust protection
cmdmess["ctrl"]["thrust"] = 0
sender.send_json(cmdmess)

while 1:
    cmdmess["ctrl"]["thrust"] = 30
    time.sleep(0.01)
    sender.send_json(cmdmess)