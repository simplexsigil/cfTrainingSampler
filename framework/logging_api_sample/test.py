from logging_api import LoggingAPI
import zmq

context = zmq.Context()
api = LoggingAPI(context, "tcp://localhost", 3001)

resp = api.startLogging();
print("Start Logging: " + str(resp));

import time

time.sleep(5)

resp = api.stopLogging()
print("Stopped logging: " + str(resp));

resp = api.getInfo()
print("Info: " + str(resp))