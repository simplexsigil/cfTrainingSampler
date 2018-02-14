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

address = "//0/80/2M"
URI = 'radio:' + address

log_base_path = "logdata/"
log_file_prefix = "CF_{address}_{time}_".format(address=address.strip("/").replace("/","-"), time=strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()))

small_log = False

height = 1
log_time = 50
maneuver_time = 1
balance_time = 2

log_intervall = 20
time_step = 0.1

maneuver_iterations = int(maneuver_time / time_step)
maneuver_step = height / maneuver_iterations
balance_iterations = int(balance_time / time_step)
log_iterations = int(log_time / time_step)



def log_file_name(config):
    return log_base_path + log_file_prefix + config.name + ".log"

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

        if (small_log):
            logConfig_stab = LogConfig(name='Stabilizer', period_in_ms=log_intervall)

            logConfig_stab.add_variable('stabilizer.roll', 'float')
            logConfig_stab.add_variable('stabilizer.pitch', 'float')
            logConfig_stab.add_variable('stabilizer.yaw', 'float')
            logConfig_stab.add_variable('stabilizer.thrust', 'float')

            logConfig_state = LogConfig(name='State', period_in_ms=log_intervall)
            logConfig_state.add_variable('stateEstimate.x', 'float')
            logConfig_state.add_variable('stateEstimate.y', 'float')
            logConfig_state.add_variable('stateEstimate.z', 'float')

            logConfig_target = LogConfig(name='ControlTarget', period_in_ms=log_intervall)
            logConfig_target.add_variable('ctrltarget.roll', 'float')
            logConfig_target.add_variable('ctrltarget.pitch', 'float')
            logConfig_target.add_variable('ctrltarget.yaw', 'float')

            logConfig_mpow = LogConfig(name='MotorPower', period_in_ms=log_intervall)
            logConfig_mpow.add_variable('motor.m1', 'int32_t')
            logConfig_mpow.add_variable('motor.m2', 'int32_t')
            logConfig_mpow.add_variable('motor.m3', 'int32_t')
            logConfig_mpow.add_variable('motor.m4', 'int32_t')  

        logConfig_all = LogConfig(name='PositionLog', period_in_ms=log_intervall)
        logConfig_all.add_variable('stateEstimate.x', 'float')
        logConfig_all.add_variable('stateEstimate.y', 'float')
        logConfig_all.add_variable('stateEstimate.z', 'float')


        with SyncCrazyflie(URI) as scf:
            cf = scf.cf

            if (small_log):
                logger_stab = SyncLogger(scf, logConfig_stab)
                logger_state = SyncLogger(scf, logConfig_state)
                logger_target = SyncLogger(scf, logConfig_target)
                logger_mpow = SyncLogger(scf, logConfig_mpow)
                logger_stab.connect()
                logger_state.connect()
                logger_target.connect()
                logger_mpow.connect()
            
            logger_all = SyncLogger(scf, logConfig_all)
            logger_all.connect()

            cf.param.set_value('kalman.resetEstimation', '1')
            time.sleep(0.1)
            cf.param.set_value('kalman.resetEstimation', '0')
            time.sleep(2)

            for y in range(maneuver_iterations):
                cf.commander.send_hover_setpoint(0, 0, 0, y * maneuver_step)
                time.sleep(time_step)

            for i in range(balance_iterations):
                print_message("Balancing out " + str(i))
                cf.commander.send_hover_setpoint(0, 0, 0, height)
                time.sleep(time_step)

            log_start = logger_all._queue.qsize()

            for i in range(log_iterations):
                print_message("Logging " + str(i))
                cf.commander.send_hover_setpoint(0, 0, 0, height)
                time.sleep(time_step)

            log_end = logger_all._queue.qsize()
            log_count = log_end - log_start 
                    

            print_message("Start:{}, end:{}".format(log_start, log_end))
            print_message("To log {} lines.".format(log_end-log_start+1))

            for y in range(maneuver_iterations - 1):
                cf.commander.send_hover_setpoint(0, 0, 0, height - (y * maneuver_step))
                time.sleep(time_step)

            cf.commander.send_hover_setpoint(0, 0, 0, 0.1)
            time.sleep(time_step)
            time.sleep(time_step)
            cf.commander.send_stop_setpoint()       #land
            time.sleep(1.5) 

            print_message("Landed, writing out log...")
            
            
            if (small_log):
                with open(log_file_name(logConfig_stab), "w") as f:
                    log_count = write_out_log(logger_stab, f, log_start, log_end)
                    print_message("logged stabilizer")

                with open(log_file_name(logConfig_state), "w") as f:
                    log_count = write_out_log(logger_state, f, log_start, log_end)
                    print_message("logged state")

                with open(log_file_name(logConfig_target), "w") as f:
                    log_count = write_out_log(logger_target, f, log_start, log_end)
                    print_message("logged control target")

                with open(log_file_name(logConfig_mpow), "w") as f:
                    log_count = write_out_log(logger_mpow, f, log_start, log_end)
                    print_message("logged motor power")
                logger_stab.disconnect()
                logger_state.disconnect()
                logger_target.disconnect()
                logger_mpow.disconnect()
        
            with open(log_file_name(logConfig_all), "w") as f:
                log_count = write_out_log(logger_all, f, log_start, log_end)
            logger_all.disconnect()
            print_message("Done logging.")


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
