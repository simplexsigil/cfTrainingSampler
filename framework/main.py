from config import config
from time import sleep
import zmq

print("Using config: ")
print(config)
print("--------------------------------------------------------------------------------")

zmqContext = zmq.Context()
# Create all connections
from connections import ClientConnection, LoggingConnection, ParamConnection, ControlConnection, ConnConnection
zmqAddress = config["zmq"]["url"]
clientConn = ClientConnection(zmqContext, zmqAddress, config["crazyFly"]["url"])
loggingConn = LoggingConnection(zmqContext, zmqAddress)
paramConn = ParamConnection(zmqContext, zmqAddress)
connConn = ConnConnection(zmqContext, zmqAddress)
controlConn = ControlConnection(zmqContext, zmqAddress)

# Connect to crazy flie and unlock
response = clientConn.disconnectFromCF()
if response["status"] != 0:
    raise Exception("Failed to disconnect from CF: " + response["msg"])
else:
    print("Disconnected old clients from CF")

response = clientConn.connectToCF()
if response["status"] != 0:
    raise Exception("Failed to connect to CF: " + response["msg"])
else:
    print("Connected to cf!") 

sleep(0.3)
#controlConn.unlockCF()



# Configure Logging Node
from nodes.logging import LoggingZmqPublisher, LoggingNode
loggingPublisher = LoggingZmqPublisher(zmqContext, zmqAddress, config["logging"]["zmq"]["port"])
loggingNode = LoggingNode(clientConn, loggingConn, config["logging"]["variables"], config["logging"]["name"], loggingPublisher)
loggingNode.start()
