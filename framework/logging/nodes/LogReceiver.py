import threading
import zmq
import math

VARIABLES_PER_BLOCK = 4.0

class LogReceiverNode(threading.Thread):

    def __init__(self, clientConn, loggingConn, variables, loggingName, loggingFrequency, loggingPublisher):
        super().__init__()
        self.clientConn = clientConn
        self.loggingConn = loggingConn
        self.loggingPublisher = loggingPublisher
        self.variables = variables
        self.loggingFrequency = loggingFrequency
        self.name = loggingName
        self.configuredLogging = False
        self.log  = False

    def _getLoggingConfigs(self, name, variables):
        configs = [];
        logConfCount = math.ceil(len(variables) / VARIABLES_PER_BLOCK)
        for i in range(0, logConfCount):
            configs.append({
                "version": 1,
                "cmd": "log",
                "action": "create",
                "name": name + "_" + str(int(i % VARIABLES_PER_BLOCK)),
                "period": 1000 / float(self.loggingFrequency),
                "variables": variables[int(VARIABLES_PER_BLOCK * i):min(int(VARIABLES_PER_BLOCK * i+VARIABLES_PER_BLOCK), len(variables))]
            })
        return configs

    def _getStartCommand(self, name):
        return {
            "version": 1,
            "cmd": "log",
            "action": "start",
            "name": name
        }

    def _setUpLogging(self):
        configs = self._getLoggingConfigs(self.name, self.variables)
        print("Configs: ")
        print(configs)
        self.configuredLogging = True
        for config in configs:
            response = self.clientConn.sendCommand(config)
            if response["status"] != 0:
                print(response)
                raise Exception("Failed to set up logging!")
            else:
                print("Setup logging for " + str(config["variables"]))
        return { "status": 0 }

    def _startLogging(self):
        if not self.configuredLogging:
            raise Exception("You must set up logging first!")

        for i in range(0, len(self._getLoggingConfigs(self.name, self.variables))):
            name = self.name + "_" + str(i)
            startCommand = self._getStartCommand(self.name + "_" + str(i));
            print("Start Command: ")
            print("Name: " + name)
            print(startCommand)
            response = self.clientConn.sendCommand(startCommand)
            if response["status"] != 0:
                print(response)
                self.log = False
                raise Exception("Failed to start logging!")
            else:
                print("Started logging....")
                self.log = True
            
    def stop(self):
        self.log = False

    def _log(self):
       while self.log:
            log = self.loggingConn.receiveData()
            # publish to zmq
            self.loggingPublisher.publish(log)

    def run(self):
        print("Starting setup");
        self._setUpLogging()
        print("Set up logging!");
        self._startLogging()
        print("started logging")
        self._log()

from cfwrapper import ZmqHost
class LoggingZmqPublisher(ZmqHost):

    def __init__(self, zmqContext, zmqServerAddress, port):
        super().__init__(zmqContext, zmqServerAddress, zmq.PUB, port)
        print("Logging Publisher Connection established on " + zmqServerAddress + ":" + str(port))

    def publish(self, log):
        self.connection.send_json(log)