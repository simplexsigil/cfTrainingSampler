from config import config
from time import sleep
print("Using config: ")
print(config)
print("--------------------------------------------------------------------------------")

from connections import ClientConnection, LoggingConnection, ParamConnection, ControlConnection, ConnConnection
zmq = config["zmq"]["url"]
clientConn = ClientConnection(zmq, config["crazyFly"]["url"])
loggingConn = LoggingConnection(zmq)
paramConn = LoggingConnection(zmq)
connConn = ConnConnection(zmq)
controlConn = ControlConnection(zmq)

sleep(5)