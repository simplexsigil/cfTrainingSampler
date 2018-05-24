
class ZmqHost:

    def __init__(self, zmqContext, zmqServerAddress, zmqType, port):
        self.connection = zmqContext.socket(zmqType)
        address = "tcp://*" + ":" + str(port)
        print("Binding to " + address)
        self.connection.bind(address)
        self.port = port
        
    def getPort(self):
        return self.port