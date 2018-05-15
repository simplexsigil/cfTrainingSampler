from config import config
from time import sleep
import zmq

print("Using config: ")
print(config)
print("--------------------------------------------------------------------------------")

zmqContext = zmq.Context()
zmqAddress = config["zmq"]["url"]
loggingPort = config["logging"]["zmq"]["port"]

from nodes.loggingListener import LoggingListenerNode
from connections import ZmqSubscribeConnection
loggingListener = ZmqSubscribeConnection(zmqContext, zmqAddress, loggingPort)
listenerNode = LoggingListenerNode(loggingListener)
listenerNode.start()