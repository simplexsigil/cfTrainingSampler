import zmq

class ZmqHost:

    def __init__(self, zmqContext, zmqServerAddress, zmqType, port):
        self.connection = zmqContext.socket(zmqType)
        address = "tcp://*" + ":" + str(port)
        print("Binding to " + address)
        self.connection.bind(address)
        self.port = port
        
    def getPort(self):
        return self.port

class ZmqServer(ZmqHost):

    def __init__(self, zmqContext, zmqServerAddress, port):
        super().__init__(zmqContext, zmqServerAddress, zmq.REP, port)

    def receiveData(self):
        return self.connection.recv_json();

    def sendData(self, response):
        return self.connection.send_json(response)