#!bin/bash

sudo python -m pip install -e ./cfwrapper
sudo python -m pip install -e ./logging_api

cd logging 
sudo python -m pip install -r ./requirements.txt

cd ../logging_api_sample
sudo python -m pip install -r requirements.txt
