import threading
from cfwrapper import ZmqHost, ZmqServer
import zmq

class ControllerHost(ZmqServer):
    
    def __init__(self, zmqContext, zmqServerAddress, port):
        super().__init__(zmqContext, zmqServerAddress, port);

class LogController(threading.Thread):
    
    def __init__(self, controllerHost, logReceiverFactory, logOutputNodeFactories):
        super().__init__();
        self.running = True;
        self.controllerHost = controllerHost
        self.logReceiverFactory = logReceiverFactory
        self.logOutputNodeFactories = logOutputNodeFactories
        self.isLogging = False
        self._initNodes()

    def stop(self):
        self.running = False;

    def _initNodes(self):
        self.logReceiverNode  = self.logReceiverFactory()
        self.logOutputNodes = [];
        for factory in self.logOutputNodeFactories:
            self.logOutputNodes.append(factory())
        
    def run(self):
        while self.running:
            data = self.controllerHost.receiveData();
            if data["action"] == "start_logging":
                if self.logReceiverNode.ident is None:
                    self.logReceiverNode.start();
                for node in self.logOutputNodes:
                    if node.ident is None:
                        node.start();
                self.controllerHost.sendData({ "success": True})
            elif data["action"] == "stop_logging": 
                if self.logReceiverNode.ident is not None:
                    self.logReceiverNode.stop()
                for node in self.logOutputNodes:
                    if node.ident is not None:
                        node.stop()
                for node in self.logOutputNodes:
                    if node.ident is not None:
                        node.join()
                if self.logReceiverNode.ident is not None:
                    self.logReceiverNode.join()
                self._initNodes()
                self.controllerHost.sendData({ "success": True})
            elif data["action"] == "info":
                self.controllerHost.sendData({ "success": True, "msg": "None"})
