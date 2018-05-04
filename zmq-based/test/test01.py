## make the drone take-off for 1 second and then land

import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect("tcp://localhost:1212")

command = {
	"version": 1, 
	"client_name": "test",
	"ctrl": { 
		"roll": 0.0,
		"pitch": 0.0,
		"yaw": 0.0,
		"thrust": 55.0
		}
	}

for x in range(0, 10):
	print(x)
	socket.send_json(command)
	time.sleep(0.1)

command["ctrl"]["thrust"] = 0.0
socket.send_json(command)