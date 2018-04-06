# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2016 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA  02110-1301, USA.
"""
Simple example that connects to the first Crazyflie found, logs the Stabilizer
and prints it to the console. After 10s the application disconnects and exits.

This example utilizes the SyncCrazyflie and SyncLogger classes.
"""
import logging
import time
from time import strftime
import queue

import cflib.crtp
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

address = "//0/10/2M"
URI = 'radio:' + address
n_loggers = 7

log_base_path = "logdata/"
log_file_prefix = "CF_{address}_{time}.".format(address=address.strip("/").replace("/","-"), time=strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()))

def log_file_name(config, id = 0):
    base_name = log_base_path + log_file_prefix + config.name
    if (id == 0):
        return base_name + ".log"
    else:
        return base_name + str(id) + ".log"

def log_stab():
    lg_stab = LogConfig(name='Stabilizer', period_in_ms=10)

    lg_stab.add_variable('stabilizer.roll', 'float')
    lg_stab.add_variable('stabilizer.pitch', 'float')
    lg_stab.add_variable('stabilizer.yaw', 'float')
    lg_stab.add_variable('stabilizer.thrust', 'float')
    return lg_stab

def main():
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)
    # Scan for Crazyflies and use the first one found
    print('Scanning interfaces for Crazyflies...')
    available = cflib.crtp.scan_interfaces()
    print('Crazyflies found:')
    for i in available:
        print(i[0])

    if len(available) == 0:
        print('No Crazyflies found, cannot run example')
    else:

        with SyncCrazyflie(URI) as scf:
            cf = scf.cf

            loggers = []

            for i in range(n_loggers):
                lg = SyncLogger(scf, log_stab() )
                loggers.append(lg)
                loggers[i].connect()    #start 

            cf.param.set_value('kalman.resetEstimation', '1')
            time.sleep(0.1)
            cf.param.set_value('kalman.resetEstimation', '0')
            time.sleep(2)

            for y in range(10):
                cf.commander.send_hover_setpoint(0, 0, 0, y / 20)
                time.sleep(0.1)


            log_start = loggers[0].qsize()

            for i in range(50):
                print_message("Going " + str(i))
                cf.commander.send_hover_setpoint(0, 0, 0, 0.3)
                time.sleep(0.1)

            log_end = loggers[0].qsize()
            log_count = log_end - log_start 
                    

            print_message("Start:{}, end:{}".format(log_start, log_end))
            print_message("To log {} lines.".format(log_end-log_start+1))

            for _ in range(10):
                cf.commander.send_hover_setpoint(0, 0, 0, 0.2)
                time.sleep(0.1)

            cf.commander.send_hover_setpoint(0, 0, 0, 0.1)
            time.sleep(0.2)
            cf.commander.send_stop_setpoint()       #land
            time.sleep(1.5) 


            print_message("Landed, start logging...")

            lg_stab = log_stab()

            for i in range(n_loggers):
                with open(log_file_name(lg_stab, i+1), "w") as f:
                    log_count = write_out_log(loggers[i], f, log_start, log_end)
                
            print_message("Logged {} lines".format(log_count))


def write_out_log(logger, file, start, end):
    count = 0
    log_count = 0
    try:
        for log_entry in logger:
            count +=1
            if (count >= end):
                break

            if (count >= start):
                log_count += 1
                timestamp = log_entry[0]
                data = log_entry[1]
                log_conf_name = log_entry[2]
                file.write('\"%d\":%s\n' % (timestamp, data))

    except queue.Empty:
        pass

    return log_count


def print_message(message):
    print("[{}] ".format(strftime("%Y-%m-%d | %H:%M:%S", time.gmtime())) + message)

if __name__ == '__main__':
    main()