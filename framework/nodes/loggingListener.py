import threading

class LoggingListenerNode(threading.Thread):
    
    def __init__(self, loggingSubscriber):
        super().__init__()
        self.loggingSubscriber = loggingSubscriber
        self.read = True;

    def stop(self):
        self.read = False

    def run(self):
        print("Started listener node")
        while self.read:
            print("Waiting for next message from zmq")
            data = self.loggingSubscriber.receiveData();
            print("Received: ")
            print(data)