import zmq
from cfwrapper import ZmqConnection

class LoggingConnection(ZmqConnection):
    def __init__(self, zmqContext, zmqServerAddress, port):
        super().__init__(zmqContext, zmqServerAddress, zmq.REQ, port)     

    def sendCommand(self, json):
            print("Sending command: " + str(json))
            self.connection.send_json(json)
            print("Send command! Waiting for receive!")
            response = self.connection.recv_json()
            print("Received response!")
            return response

class LoggingAPI:

    def __init__(self, zmqContext, zmqServerAddress, port):
        self.connection = LoggingConnection(zmqContext, zmqServerAddress, port)

    """
        Returns true if command was received
    """
    def startLogging(self):
        return self.connection.sendCommand({ "action": "start_logging"})["success"]

    def stopLogging(self):
        return self.connection.sendCommand({ "action": "stop_logging"})["success"]        

    def getInfo(self):
        return self.connection.sendCommand({"action": "info"});