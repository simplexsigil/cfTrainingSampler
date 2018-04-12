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
from cflib.crazyflie.console import Console

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

address = "//0/10/2M"
URI = 'radio:' + address

log_base_path = "logdata/"
log_file_name = "CF_{address}_{time}.log".format(address=address.strip("/").replace("/", "-"),
                                                 time=strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()))


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

        lg_stab = LogConfig(name='Stabilizer', period_in_ms=10)

        lg_stab.add_variable('stabilizer.roll', 'float')
        lg_stab.add_variable('stabilizer.pitch', 'float')
        lg_stab.add_variable('stabilizer.yaw', 'float')
        lg_stab.add_variable('stabilizer.thrust', 'float')

        # In order to log more variables than fit in a log block, we need to define multiple lock blocks/configs.
        # This means they wont have the same time stamp, since they are sent in different packets.
        # It might still be acceptable
        # In order to use this, we have to work with the asynchronous API.

        """
        lg_state = LogConfig(name='State', period_in_ms=10)
        lg_state.add_variable('stateEstimate.x', 'float')
        lg_state.add_variable('stateEstimate.y', 'float')
        lg_state.add_variable('stateEstimate.z', 'float')

        lg_ctrl_target = LogConfig(name='ControlTarget', period_in_ms=10)
        lg_ctrl_target.add_variable('ctrltarget.roll', 'float')
        lg_ctrl_target.add_variable('ctrltarget.pitch', 'float')
        lg_ctrl_target.add_variable('ctrltarget.yaw', 'float')

        lg_mpow = LogConfig(name='MotorPower', period_in_ms=10)
        lg_mpow.add_variable('motor.m1', 'int32_t')
        lg_mpow.add_variable('motor.m2', 'int32_t')
        lg_mpow.add_variable('motor.m3', 'int32_t')
        lg_mpow.add_variable('motor.m4', 'int32_t')
        """

        with SyncCrazyflie(URI) as scf:
            cf = scf.cf

            max_thrust = 0.7

            with open(log_base_path + log_file_name, "w") as f:

                with SyncLogger(scf, lg_stab) as logger:

                    cf.param.set_value('kalman.resetEstimation', '1')
                    time.sleep(0.1)

                    cf.param.set_value('kalman.resetEstimation', '0')
                    time.sleep(2)

                    for y in range(16):
                        cf.commander.send_setpoint(0, 0, 0, int(max_thrust * y / 16 * (0xFFFF - 1)))
                        time.sleep(0.1)

                    for _ in range(30):
                        cf.commander.send_setpoint(0, 0, 0, int(max_thrust * ( 0xFFFF - 1)))
                        time.sleep(0.1)

                    print_message("Start logging...")
                    log_count = 0

                    for _ in range(70):
                        cf.commander.send_setpoint(0, 0, 0, int(max_thrust * (0xFFFF - 1)))
                        log_count += write_out_log(logger, f)
                        time.sleep(0.1)

                    print_message("Stopped logging.")
                    print_message("Logged {} lines.".format(log_count))

                    for _ in range(30):
                        cf.commander.send_setpoint(0, 0, 0, int(max_thrust * (0xFFFF - 1)))

                        time.sleep(0.1)

                    for y in range(16):
                        cf.commander.send_hover_setpoint(0, 0, 0, int(max_thrust * (1 - (y / 16)) * (0xFFFF - 1)))
                        time.sleep(0.1)

                    cf.commander.send_stop_setpoint()


def write_out_log(logger, file):
    log_count = 0

    try:
        for log_entry in logger:
            timestamp = log_entry[0]
            data = log_entry[1]
            log_conf_name = log_entry[2]

            file.write('\"%d\":%s\n' % (timestamp, data))

            log_count += 1
    except queue.Empty:
        pass

    return log_count


def print_message(message):
    print("[{}] ".format(strftime("%Y-%m-%d | %H:%M:%S", time.gmtime())) + message)


if __name__ == '__main__':
    main()
