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

log_base_path = "logdata/"
log_file_prefix = "CF_{address}_{time}_".format(address=address.strip("/").replace("/","-"), time=strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()))

def log_file_name(config, id = 0):
    base_name = log_base_path + log_file_prefix + config.name
    if (id == 0):
        return base_name + ".log"
    else:
        return base_name + str(id) + ".log"

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

    	loggers = []


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