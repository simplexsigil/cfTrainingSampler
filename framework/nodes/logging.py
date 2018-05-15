import threading
import zmq

class LoggingNode(threading.Thread):

    def __init__(self, clientConn, loggingConn, variables, loggingName, loggingPublisher):
        super().__init__()
        self.clientConn = clientConn
        self.loggingConn = loggingConn
        self.loggingPublisher = loggingPublisher
        self.variables = variables
        self.name = loggingName
        self.configuredLogging = False
        self.log  = False

    def _getLoggingConfig(self, name, variables):
            return {
            "version": 1,
            "cmd": "log",
            "action": "create",
            "name": name,
            "period": 10,
            "variables": variables
        }

    def _getStartCommand(self, name):
        return {
            "version": 1,
            "cmd": "log",
            "action": "start",
            "name": self.name
        }

    def _setUpLogging(self):
        config = self._getLoggingConfig(self.name, self.variables)
        self.configuredLogging = True
        response = self.clientConn.sendCommand(config)
        if response["status"] != 0:
            print(response)
            raise Exception("Failed to set up logging!")
        else:
            print("Setup logging...")
            return response

    def _startLogging(self):
        if not self.configuredLogging:
            raise Exception("You must set up logging first!")
        response = self.clientConn.sendCommand(self._getStartCommand(self.name))
        if response["status"] != 0:
            print(response)
            raise Exception("Failed to start logging!")
        else:
            print("Started logging....")
            self.log = True
            
    def stopLogging(self):
        self.log = False

    def _log(self):
       while self.log:
            print("Waiting for next logging message")
            log = self.loggingConn.receiveData()
            print("Received logging message!")
            if log["event"] == "data":
                print(log)
            if log["event"] == "created":
                print("Created block {}".format(log["name"]))
            if log["event"] == "started":
                print("Started block {}".format(log["name"]))
            if log["event"] == "stopped":
                print("Stopped block {}".format(log["name"]))
            if log["event"] == "deleted":
                print("Deleted block {}".format(log["name"]))

            # publish to zmq
            self.loggingPublisher.publish(log)

    def run(self):
        self._setUpLogging()
        self._startLogging()
        self._log()

from connections import ZmqConnection
class LoggingZmqPublisher(ZmqConnection):

    def __init__(self, zmqContext, zmqServerAddress, port):
        super().__init__(zmqContext, zmqServerAddress, zmq.PUB, port)
        print("Logging Publisher Connection established on " + zmqServerAddress + ":" + str(port))

    def publish(self, log):
        print("Publishing " + str(log) + " to zmq logging endpoint.")
        self.connection.send_json(log)