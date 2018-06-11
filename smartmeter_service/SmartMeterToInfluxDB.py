import datetime
from influxdb import InfluxDBClient
import requests
import daemon
import lockfile
import time
import json

import sys
import serial
import re

ser = serial.Serial()
ser.baudrate = 115200
ser.bytesize=serial.EIGHTBITS
ser.parity=serial.PARITY_NONE
ser.stopbits=serial.STOPBITS_ONE
ser.xonxoff=0
ser.rtscts=0
ser.timeout=20
ser.port="/dev/ttyUSB0"

first_output = True

def openPort():
	#Open COM port
	try:
	    ser.open()
	except:
	    print ("Cannot open device:"  % ser.name)


def getSmartMeterData(inSerial,printOutput = False,verbose = False):
    buffer=[]
    telegram_start = False;
    # Empty dict
    data = {}
    
    while True:
        p1_line_in=''
        
        try:
            p1_raw = ser.readline()
        except:
            print ("Error reading from port." % ser.name )
            return(False)
        
        p1_str=str(p1_raw, "utf-8")
        p1_line_in=p1_str.strip()
        
        if telegram_start == False:
            if len(p1_line_in) >0:
                if p1_line_in[0] == "/":
                    buffer.append(p1_line_in)
                    if verbose == True: print ("Line:",p1_line_in)
                    telegram_start = True
        else:
            buffer.append(p1_line_in)
            if verbose == True: print ("Line:",p1_line_in)
            
            if len(p1_line_in) >0:
                if p1_line_in[0] == "!":
                    telegram_start = False
                    if len(buffer) == 26:
                        break
                    else:
                        print("Corrupt packet, expected length %i got %i -> Retrying!" % (26,len(buffer)))
                        buffer = []

    for line in buffer:
        if re.search("1-0:1.8.1", line):
            data['READING_POWER_IN_LOW_TARIFF'] = float(re.search(r'\(([\d\.]*)\*', line).group(1));
            if printOutput == True: print("Meter Reading electricity delivered to client (low tariff) in 0,001 kWh:\t\t%.3f kWh" %
                                     float(re.search(r'\(([\d\.]*)\*', line).group(1)))
        elif re.search("1-0:1.8.2", line):
            data['READING_POWER_IN_NORM_TARIFF'] = float(re.search(r'\(([\d\.]*)\*', line).group(1));
            if printOutput == True: print("Meter Reading electricity delivered to client (normal tariff) in 0,001 kWh:\t\t%.3f kWh" %
                                      float(re.search(r'\(([\d\.]*)\*', line).group(1)))
        elif re.search("1-0:2.8.1", line):
            data['READING_POWER_OUT_LOW_TARIFF'] = float(re.search(r'\(([\d\.]*)\*', line).group(1))
            if printOutput == True: print("Meter Reading electricity delivered by client (low tariff) in 0,001 kWh:\t\t%.3f kWh" % 
                                      float(re.search(r'\(([\d\.]*)\*', line).group(1)))
        elif re.search("1-0:2.8.2", line):
            data['READING_POWER_OUT_NORM_TARIFF'] = float(re.search(r'\(([\d\.]*)\*', line).group(1))
            if printOutput == True: print("Meter Reading electricity delivered by client (normal tariff) in 0,001 kWh:\t\t%.3f kWh" %
                                      float(re.search(r'\(([\d\.]*)\*', line).group(1)))
        elif re.search("1-0:1.7.0", line):
            data['ACTUAL_POWER_IN'] = float(re.search(r'\(([\d\.]*)\*', line).group(1))
            if printOutput == True: print("Actual electricity power delivered (+P) in 1 Watt resolution:\t\t\t\t%.3f kW" % 
                                      float(re.search(r'\(([\d\.]*)\*', line).group(1)))        
        elif re.search("1-0:2.7.0", line):
            data['ACTUAL_POWER_OUT'] = float(re.search(r'\(([\d\.]*)\*', line).group(1))
            if printOutput == True: print("Actual electricity power received (-P) in 1 Watt resolution:\t\t\t\t%.3f kW" %
                                      float(re.search(r'\(([\d\.]*)\*', line).group(1)))        
        # Gasmeter: 0-1:24.3.0
        elif re.search("0-1:24.2.1", line):
            data['READING_GAS_IN'] = float(re.search(r'\(([\d\.]*)\*', line).group(1))
            if printOutput == True: print("Gas Data - Gas delivered to client in m3:\t\t\t\t\t\t%.3f m3" %
                                     float(re.search(r'\(([\d\.]*)\*', line).group(1)))                
       # else:
               # pass
    buffer = []
    return(data)



def main(host='192.168.2.29', port=8086):  # Replace parameters below with your InfluxDB connection details
        user = 'xxxxxx'
        password = 'xxxxxxxxxxxxx'
        dbname = 'marcel_sensors'
        dbuser = 'xxxxxxxxxxxx'
        dbuser_password = 'xxxxxxxxxx'

        data = getSmartMeterData(ser)
        
        global first_output

        json_body = [
                {
                "measurement": "SmartMeter",
                "time": datetime.datetime.now().isoformat(),
                "fields": {
                        "READING_POWER_IN_LOW_TARIFF" : float(data['READING_POWER_IN_LOW_TARIFF']),
                        "READING_POWER_IN_NORM_TARIFF" : float(data['READING_POWER_IN_NORM_TARIFF']),
                        "ACTUAL_POWER_IN": float(data['ACTUAL_POWER_IN']),
                        "READING_GAS_IN": float(data['READING_GAS_IN']),                    
                }
                } ,               
        ]


        client = InfluxDBClient(host, port, user, password, dbname)
        
        if (first_output == True):
        	print("Write points: {0}".format(json_body))
        	first_output = False

        client.write_points(json_body)


def do_something():
        while True:
                main()
                time.sleep(30)

def run():
	logfile = open('smartmeter_service_daemon.log', 'w')
	with daemon.DaemonContext(stdout = logfile, stderr = logfile, pidfile=lockfile.FileLock('/var/run/smartmeter_service.pid')):
		openPort()
		do_something()

if __name__ == "__main__":
	print("Starting SmartMeter to InfluxDB Service")
	run()

