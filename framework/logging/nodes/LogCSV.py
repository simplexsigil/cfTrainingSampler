import threading
import datetime
import os
"""
    {'version': 1, 'name': 'LoggingConfig', 'event': 'data', 'timestamp': 1376140, 'variables': {'pm.vbat': 3.7161290645599365, 'stabilizer.roll': -0.45266175270080566}}
"""
class LogCSVNode(threading.Thread):
    
    def __init__(self, outputDirectory, fileNameFormat, loggingSubscriber):
        super().__init__()
        self.loggingSubscriber = loggingSubscriber
        self.read = True;
        self.fileNameFormat = fileNameFormat
        self.files = { }
        self.firstLine = {}
        self.outputDirectory = outputDirectory
        self.fileNames = {}

    def stop(self):
        self.read = False

    def run(self):
        print("Started listener node")
        while self.read:
            data = self.loggingSubscriber.receiveData();
            baseFileName = self.makeFileName(data["name"])
            file = None
            if data["name"] in self.fileNames:
                file = self.files[self.fileNames[data["name"]]]
            else: 
                i = 0
                fileName = baseFileName + "_" + str(i) + ".csv"
                while fileName not in self.files:
                    try:
                        fileName = baseFileName + "_" + str(i) + ".csv"
                        file = self.createFile(fileName)
                    except Exception:
                        print("Failed to create file for " + fileName)
                    i += 1

                file = self.files[fileName]
                self.fileNames[data["name"]] = fileName
                print("Using file name " + fileName + " for logging config " + data["name"]);

            self.writeData(file, data, fileName)

    def writeData(self, file, data, fileName):
        if data["event"] == "data":
            outputString = str(data["timestamp"])
            columnString = "timestamp"
            for key in sorted(data["variables"]):
                columnString += "," + key
                outputString += "," + str(data["variables"][key]) 
            if self.firstLine[fileName]:
                file.write(columnString + "\n")
                self.firstLine[fileName] = False
            file.write(outputString + "\n")
        
    def makeFileName(self, configName):
        return self.fileNameFormat.replace("%d%", str(datetime.datetime.now().date())).replace("%name%", configName);

    def createFile(self, fileName):
        file = os.path.join(self.outputDirectory, fileName)
        if (os.path.isfile(file)):
            raise Exception("File " + fileName + " exists")
        self.files[fileName] = open(file, "a")
        test = open(os.path.join(self.outputDirectory, fileName), "r")
        self.firstLine[fileName] = test.readline() == ""
        return self.files[fileName]

    def closeFiles(self):
        for file in self.files:
            self.files[file].close()
