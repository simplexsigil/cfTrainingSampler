import zmq
import threading
CLIENT_PORT = 2000
LOGGING_PORT = 2001
PARAM_PORT = 2002
CONN_PORT = 20003
CONTROL_PORT = 2004

class ZmqConnection:

    def __init__(self, zmqServerAddress, zmqType, port):
        self.context = zmq.Context()
        self.connection = self.context.socket(zmqType )

        address = zmqServerAddress + ":" + str(port)
        print("Connecting to " + address)
        self.lock = threading.Lock()
        self.connection.connect(address)

    """
        to be implemented by the child class
    """
    def sendCommand(self, json):
        raise Exception("Send command needs to be overwritten in sub classes of zmqconnection")

    def disconnect(self):
        with self.lock:
            self.connection.close()

class ZmqSubscribeConnection(ZmqConnection):
    
    def __init__(self, zmqServerAddress, port):
        super().__init__(zmqServerAddress, zmq.SUB, port)

    def sendCommand(self, json):
        raise Exception("Can't send message to zmq.SUB connection!");

    """
        @param shouldContinueFunc: () => bool
        @param onData: (data) => void
    """
    def listen(self, shouldContinueFunc, onData):
        while shouldContinueFunc():
            # TODO: check timeout?
            package = self.connection.recv_json()
            onData(package)


class ClientConnection(ZmqConnection):

    def __init__(self, zmqServerAddress, crazyFlyAddress):
        super().__init__(zmqServerAddress, zmq.REQ, CLIENT_PORT)
        self.crazyFlyAddress = crazyFlyAddress
        print("Controller connection established.\n")

    def connectToCF(self, cfUrl):
        connect_cmd = {
            "version": 1,
            "cmd": "connect",
            "uri": "{}".format(self.crazyFlyAddress)
        }
        print("Connecting to crazy fly at " + connect_cmd["uri"])
        return self.sendCommand(connect_cmd)


    def disconnectFromCF(sefl, cfUrl):
        disconnect_cmd = {
            "version": 1,
            "cmd": "disconnect",
            "uri": "{}".format(self.crazyflie_uri)
        }

        print("Disconnecting from crazy fly at " + connect_cmd["uri"])
        return self.sendCommand(disconnect_cmd)

    def sendCommand(self, json):
        with self.lock:
            self.connection.send_json(json)
            return self.connection.recv_json()

class LoggingConnection(ZmqSubscribeConnection): 

    def __init__(self, zmqServerAddress):
        super().__init__(zmqServerAddress, LOGGING_PORT)
        print("Connected to logging server\n")


class ParamConnection(ZmqSubscribeConnection):
    
    def __init__(self, zmqServerAddress):
        super().__init__(zmqServerAddress, PARAM_PORT)
        print("Param Connection established.\n")

    def sendCommand(self, json):
        raise Exception("Can't send message to zmq.SUB connection!");

# TODO rename
# TODO logging library => levels from config filter by tags?
class ConnConnection(ZmqSubscribeConnection):
    
    def __init__(self, zmqServerAddress):
        super().__init__(zmqServerAddress, CONN_PORT)
        print("ConnConnection established.\n")

    def sendCommand(self, json):
        raise Exception("Can't send message to zmq.SUB connection!");

class ControlConnection(ZmqConnection) :
    def __init__(self, zmqServerAddress):
        super().__init__(zmqServerAddress, zmq.PUSH, CONTROL_PORT)
        print("Control Connection established.")

    def unlockCF(self): 
        thrust_unlock = {
            "version": 1,
            "roll": 0,
            "pitch": 0,
            "yaw": 0,
            "thrust": 0
        }

        with lock:
            print("Sending thrust unlocking commands.")
            for _ in range(0, 10):
                time.sleep(0.01)
                self.sendCommand(thrust_unlock)
            print("Send unlock commands.")

    def sendCommand(self, json):
        with self.lock:
            self.connection.send_json(json)