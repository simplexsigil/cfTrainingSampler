from cfwrapper import config
from time import sleep
import zmq

print("Using config: ")
print(config)
print("--------------------------------------------------------------------------------")

zmqContext = zmq.Context()
zmqAddress = config["zmq"]["url"]
loggingPort = config["logging"]["zmq"]["port"]

from nodes.LogPrinter import LogPrinterNode
from cfwrapper.connections import ZmqSubscribeConnection
loggingListener = ZmqSubscribeConnection(zmqContext, zmqAddress, loggingPort)
listenerNode = LogPrinterNode(loggingListener)
listenerNode.start()