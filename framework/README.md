# Simple Framework

# log.py

Opens a zmq publishing socket on `localhost:3000` (or the port configured in `config.json`) and sends
all log data received from the drone to this connection without performing any data format changes.

## TODO

* change data format?
* remove extra thread

# print_log.py

**Requires**: `python3 log.py`
Uses `nodes/loggingListener.py` to listen for logging messages and prints them. 

Start with `python3 print_log.py`

## TODO

* remove extra thread