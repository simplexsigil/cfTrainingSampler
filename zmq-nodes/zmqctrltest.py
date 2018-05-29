### this script will power on the motors, but the cflie will still stay on the ground

import zmq
import time
import sys

SRV_ADDR = "tcp://127.0.0.1"
CF_URI = "radio://0/10/2M"
context = zmq.Context()

client_conn = context.socket(zmq.REQ)
client_conn.connect("{}:2000".format(SRV_ADDR))

ctrl_conn = context.socket(zmq.PUSH)
ctrl_conn.connect("{}:2004".format(SRV_ADDR))

time.sleep(2)


##################################################
# scan and output all cf interfaces 
print("Scanning for Crazyflies ...", end=' ')
scan_cmd = {
    "version": 1,
    "cmd": "scan"
}
client_conn.send_json(scan_cmd)
resp = client_conn.recv_json()
print("done!")
for i in resp["interfaces"]:
    print("\t{} - {}".format(i["uri"], i["info"]))


####################################################
# connect the cflie using URI
connect_cmd = {
    "version": 1,
    "cmd": "connect",
    "uri": "{}".format(CF_URI)
}
print("Connecting to {} ...".format(connect_cmd["uri"]), end=' ')
client_conn.send_json(connect_cmd)
resp = client_conn.recv_json()
if resp["status"] != 0:
    print("fail! {}".format(resp["msg"]))
    sys.exit(1)
print("done!")

##############################################
# needs this to make the crazyflie fly, to unlock the control mechanism

_cmd = {
    "version": 1,
    "roll": 0,
    "pitch": 0,
    "yaw": 0,
    "thrust": 0
    }

for _ in range(0,10):
    time.sleep(0.1)
    ctrl_conn.send_json(_cmd)
    print("Sent: " + str(_cmd))

_cmd["thrust"] = 20000

##############################################
# power on the motors, cflie shouldn't be able to "fly" yet
i = 0
for i in range(0, 20):
    time.sleep(0.1)
    ctrl_conn.send_json(_cmd)
    print("Sent " + str(i) + ": " + str(_cmd))

# land
_cmd["thrust"] = 0
ctrl_conn.send_json(_cmd)


print("Reached end of script")