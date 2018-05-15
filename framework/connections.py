import zmq
import threading
import time

CLIENT_PORT = 2000
LOGGING_PORT = 2001
PARAM_PORT = 2002
CONN_PORT = 20003
CONTROL_PORT = 2004

class ZmqConnection:

    def __init__(self, zmqContext, zmqServerAddress, zmqType, port):
        self.context = zmqContext
        self.connection = self.context.socket(zmqType )
        self.port = port
        address = zmqServerAddress + ":" + str(port)
        print("Connecting to " + address)
        self.lock = threading.Lock()
        self.connection.connect(address)

    """
        to be implemented by the child class
    """
    def sendCommand(self, json):
        raise Exception("Send command needs to be overwritten in sub classes of zmqconnection")
    
    def getPort(self):
        return self.port

    def disconnect(self):
        with self.lock:
            self.connection.close()

class ZmqSubscribeConnection(ZmqConnection):
    
    def __init__(self, zmqContext, zmqServerAddress, port):
        super().__init__(zmqContext, zmqServerAddress, zmq.SUB, port)
        self.connection.setsockopt_string(zmq.SUBSCRIBE, u"")


    def sendCommand(self, json):
        raise Exception("Can't send message to zmq.SUB connection!");

    def receiveData(self):
        return self.connection.recv_json()


class ClientConnection(ZmqConnection):

    def __init__(self, zmqContext, zmqServerAddress, crazyFlyAddress):
        super().__init__(zmqContext, zmqServerAddress, zmq.REQ, CLIENT_PORT)
        self.crazyFlyAddress = crazyFlyAddress
        print("Controller connection established.\n")

    def connectToCF(self):
        connect_cmd = {
            "version": 1,
            "cmd": "connect",
            "uri": "{}".format(self.crazyFlyAddress)
        }
        print("Connecting to crazy fly at " + connect_cmd["uri"])
        return self.sendCommand(connect_cmd)


    def disconnectFromCF(self):
        disconnect_cmd = {
            "version": 1,
            "cmd": "disconnect",
            "uri": "{}".format(self.crazyFlyAddress)
        }

        print("Disconnecting from crazy fly at " + disconnect_cmd["uri"])
        return self.sendCommand(disconnect_cmd)

    def sendCommand(self, json):
        with self.lock:
            print("Sending command: " + str(json))
            self.connection.send_json(json)
            print("Send command! Waiting for receive!")
            response = self.connection.recv_json()
            print("Received response!")
            return response

class LoggingConnection(ZmqSubscribeConnection): 

    def __init__(self, zmqContext, zmqServerAddress):
        super().__init__(zmqContext, zmqServerAddress, LOGGING_PORT)
        print("Connected to logging server\n")


class ParamConnection(ZmqSubscribeConnection):
    
    def __init__(self, zmqContext, zmqServerAddress):
        super().__init__(zmqContext, zmqServerAddress, PARAM_PORT)
        print("Param Connection established.\n")

    def sendCommand(self, json):
        raise Exception("Can't send message to zmq.SUB connection!");

# TODO rename
# TODO logging library => levels from config filter by tags?
class ConnConnection(ZmqSubscribeConnection):
    
    def __init__(self, zmqContext, zmqServerAddress):
        super().__init__(zmqContext, zmqServerAddress, CONN_PORT)
        print("ConnConnection established.\n")

    def sendCommand(self, json):
        raise Exception("Can't send message to zmq.SUB connection!");

class ControlConnection(ZmqConnection) :
    def __init__(self, zmqContext, zmqServerAddress):
        super().__init__(zmqContext, zmqServerAddress, zmq.PUSH, CONTROL_PORT)
        print("Control Connection established.")

    def unlockCF(self): 
        thrust_unlock = {
            "version": 1,
            "roll": 0,
            "pitch": 0,
            "yaw": 0,
            "thrust": 0
        }

        with self.lock:
            print("Sending thrust unlocking commands.")
            for _ in range(0, 10):
                print("Unlock Command: " + str(_))
                time.sleep(0.01)
                self.sendCommand(thrust_unlock)
                print("Send command!")
            print("Send unlock commands complete.")

    def sendCommand(self, json):
        with self.lock:
            self.connection.send_json(json)