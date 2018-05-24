import json
import os

with open("config.json") as configFile:
    print("Reading config file from " + os.path.abspath(configFile.name))
    config = json.load(configFile)
