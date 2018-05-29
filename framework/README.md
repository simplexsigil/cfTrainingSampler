# CFWrapper

- Base class collection which is used for all zmq & cf related classes.

Install with

`pip install -e ./cfwrapper'

# logging

Contains a python script to start our logging program.

```
cd logging;
virtualenv logging_env
source ./logging_env/bin/activate
pip install -r requirements.txt
cd ..;
mkdir data
python3 logging/log.py
```

# logging_api

Contains the API for the logging program. Communication works through zmq via a server client configuration.

Install with 

`pip install -e ./logging_api`

# logging_api_sample

Sample usage of the API

```
cd logging_api_sample;
virtualenv logging_api_sample_env
source logging_api_sample_env/bin/activate
pip install -r requirements.txt
cd ..;
python3 logging_api_sample/test.py
```

# Testing the sample and logging program

1. run cfzmq from the other repo
2. start logging
3. start logging_api_sample
4. Check that start logging prints the log messages in the console - it does not create a csv yet and i did not update the variables

**NOTE that the config.json must be in the current working directory i.e. the directory you call python from.**

## Install all packages & dependencies (global)
See setup_global.sh

python -m pip install -e ./cfwrapper
python -m pip install -r ./logging/requirements.txt
python -m pip install -e ./logging_api
python -m pip install -r ./logging_api_sample/requirements.txt