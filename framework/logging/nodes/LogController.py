import threading

class LogController(threading.Thread):

    
    def __init__(self, logReceiver, logOutputNodes):
        super().__init__();