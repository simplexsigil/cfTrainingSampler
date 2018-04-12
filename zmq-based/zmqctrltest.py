import zmq
import time
import sys

SRV_ADDR = "tcp://127.0.0.1"
CF_URI = "radio://0/80/2M"
context = zmq.Context()

client_conn = context.socket(zmq.REQ)
client_conn.connect("{}:2000".format(SRV_ADDR))

ctrl_conn = context.socket(zmq.PUSH)
ctrl_conn.connect("{}:2004".format(SRV_ADDR))

time.sleep(2)

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

_cmd["thrust"] = 30000

i = 0

while True:
    time.sleep(0.1)
    ctrl_conn.send_json(_cmd)
    print("Sent: " + str(_cmd))
