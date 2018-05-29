from cfwrapper import config
from time import sleep
import zmq

print("Using config: ")
print(config)
print("--------------------------------------------------------------------------------")

zmqContext = zmq.Context()
# Create all connections
from cfwrapper import ClientConnection, LoggingConnection, ParamConnection, ControlConnection, ConnConnection
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

while True:
    response = clientConn.connectToCF()
    if response["status"] != 0:
        print("Failed to connect to CF: " + response["msg"])
        print("Waiting 3 seconds before trying to reconnect!");
        sleep(3);
    else:
        print("Connected to cf!") 
        break

sleep(0.3)
#controlConn.unlockCF()

loggingPort = config["logging"]["zmqPorts"]["log"]
from nodes.LogReceiver import LoggingZmqPublisher, LogReceiverNode
loggingPublisher = LoggingZmqPublisher(zmqContext, zmqAddress, loggingPort)

# Configure Logging Node
def receiverFactory():
    loggingNode = LogReceiverNode(clientConn, loggingConn, config["logging"]["variables"], config["logging"]["name"], config["logging"]["frequency"], loggingPublisher)
    return loggingNode

def printNodeFactory():
    from nodes.LogPrinter import LogPrinterNode
    from cfwrapper.connections import ZmqSubscribeConnection
    loggingListener = ZmqSubscribeConnection(zmqContext, zmqAddress, loggingPort)
    listenerNode = LogPrinterNode(loggingListener)
    return listenerNode

def csvNodeFactory():
    from nodes.LogCSV import LogCSVNode
    from cfwrapper.connections import ZmqSubscribeConnection
    loggingListener = ZmqSubscribeConnection(zmqContext, zmqAddress, loggingPort)    
    logCsv = LogCSVNode("data", "%name%_%d%.csv", loggingListener)
    return logCsv

from nodes.LogController import LogController, ControllerHost

controllerHost = ControllerHost(zmqContext, zmqAddress, config["logging"]["zmqPorts"]["controller"])
controller = LogController(controllerHost, receiverFactory, [csvNodeFactory, printNodeFactory])
controller.start()