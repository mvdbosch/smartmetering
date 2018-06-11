import datetime
from influxdb import InfluxDBClient
import requests
import daemon
import lockfile
import time
import json

import tsl2591
from bmp280_smbus import *

first_output = True;

def getSensors():

    tsl = tsl2591.Tsl2591()
    data_temp_pres = getBMP280()
    time.sleep(0.2)
    full, ir = tsl.get_full_luminosity()
    tsl.bus.close()

    data =  { "temperature" : "%.2f" % (data_temp_pres[0]),
              "temperature_unit" : "Celcius",
              "pressure" : "%.2f" % (data_temp_pres[1]),
              "pressure_unit" : "Millibar",
              "luminosity_full" : "%.2f" % (tsl.calculate_lux(full, ir)),
              "luminosity_full_unit" : "Lux",
              "luminosity_visible" : "%.2f" % (full),
              "luminosity_visisble_unit" : "Raw",
              "luminosity_ir" : "%.2f" % (ir),
              "luninosity_ir_unit" : "Raw" }

    #return { json.dumps(data) }
    return(data)


def main(host='192.168.2.29', port=8086):  # Replace parameters below with your InfluxDB connection details
        user = 'xxxxxxxxxxxxxxx'
        password = 'xxxxxxxxxxxxxx'
        dbname = 'marcel_sensors'
        dbuser = 'xxxxxxx'
        dbuser_password = 'xxxxxxxxx'

        data = getSensors()

        global first_output

        json_body = [
                {
                "measurement": "Sensors",
                "time": datetime.datetime.now().isoformat(),
                "fields": {
                        "TEMPERATURE" : float(data['temperature']),
                        "PRESSURE" : float(data['pressure']),
                        "LUMINOSITY_FULL": float(data['luminosity_full']),
                        "LUMINOSITY_VISIBLE": float(data['luminosity_visible']),
                        "LUMINOSITY_IR": float(data['luminosity_ir']),
                }
                } ,
        ]


        client = InfluxDBClient(host, port, user, password, dbname)
        if (first_output == True):
            print("Write points: {0}".format(json_body))
            first_output = False;

        client.write_points(json_body)



def do_something():
        while True:
                main()
                time.sleep(30)

def run():
        logfile = open('sensor_service_daemon.log', 'w')
        with daemon.DaemonContext(stdout = logfile, stderr = logfile, pidfile=lockfile.FileLock('/var/run/sensor_service_service.pid')):
            print("Started")    
            do_something()

if __name__ == "__main__":
        print("Starting Sensor to InfluxDB Service")
        run()

