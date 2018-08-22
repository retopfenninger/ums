#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Unified measurement software UMS
# New measurement software for the electrochemical materials group, Prof. Jennifer Rupp
#
# Copyright (c) 2013 Reto Pfenninger, department of materials, D-MATL, ETH Zürich
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import string
import struct

import numpy as np
import os
import sys
import datetime
from prologix_GPIB_ethernet import prologix_ethernet

class keithley_2182A:
    def __init__(self,device_file,address):
        try:
            if "/" not in device_file: # means it is not a path to /dev/xxx
                self.using_GPIB_to_Ethernet = True
                self.device = prologix_ethernet(device_file)
            else:
                self.device = open(device_file, "w+")
                self.using_GPIB_to_Ethernet = False
        except:
            return -1
        self.debug = True
        self.write_to_dev("++mode 1")
        self.write_to_dev("++addr " + str(address))
        self.write_to_dev("++auto 0")
        self.write_to_dev("++eos 3") # Dont append anything 0=CRLF 1=CR 2=LF 3=None
        self.write_to_dev("++eoi 1") # Indicate End-of-data
        #self.write_to_dev("CAL:UNPR:ACAL:INIT") # prepare for calibration
        #time.sleep(2.0)
        #self.write_to_dev("CAL:UNPR:ACAL:STEP2") # prepare for 10mV range calibration
        #time.sleep(5.0)
        #self.write_to_dev("CAL:UNPR:ACAL:DONE") # prepare for 10mV range calibration
        self.nplc_delay_time = 0.1
        time.sleep(1.0)

    def write_to_dev(self, string):
        if self.debug:
            print "Just wrote: ",string
        self.device.write(string + "\n")
        #time.sleep(2)
        return

    def read_from_dev(self):
        self.write_to_dev("++read eoi\n")
        if self.using_GPIB_to_Ethernet:
            a = self.device.read()
        else:
            a = self.device.readline()
        if self.debug:
            print a
        return a
        
    def query(self, string):
        self.write_to_dev(string)
        time.sleep(self.nplc_delay_time)
        print "NPLC is",self.nplc_delay_time
        return self.read_from_dev()
        
    def get_id(self):
        return "keithley_2182A"
        
    def checkError(self):
        self.write_to_dev("SYST:ERR?")
        self.write_to_dev("++read eoi")
        print self.read_from_dev()
        return self.read_from_dev()
        
    def set_nplc(self,nplc,current=False):
        if nplc == 0.01:
            self.nplc_delay_time = 0.4
        elif nplc == 0.1:
            self.nplc_delay_time = 1.6
        elif nplc == 1:
            self.nplc_delay_time = 2
        elif nplc == 5:
            self.nplc_delay_time = 1
        elif nplc == 10:
            self.nplc_delay_time = 8
        if nplc in [0.01,0.1,1,5,10]:
            if current:
                print "This device does not support current measurements!"
            self.write_to_dev("SENS:VOLT:NPLC "+str(nplc))
            self.write_to_dev("SENS:TEMP:NPLC "+str(nplc))
        return
        
    def get_value(self,channel=1): # needed for compatibility with keithley_6517B
        self.write_to_dev("SENS:CHAN "+str(channel))
        answer_from_keithley = self.query("READ?")
        a = answer_from_keithley.split(',')
        res = [0]
        if self.what_is_measured is "temperature":
            res = [float(a[0])]
        elif self.what_is_measured is "voltage":
            res = [float(a[0])]
        elif self.what_is_measured is "voltage_ratio":
            res = [float(a[0])]
        if res[0] == 9.9e37: # overflow
            res[0] = 0.0
        return [res[0],time.time()]

    def setup_temperature_measurement(self,sensor="K"):
        self.what_is_measured = "temperature"
        sens = "K"
        if sensor is "J":
            sens = "J"
        elif sensor is "T":
            sens = "T"
        elif sensor is "S":
            sens = "S"
        elif sensor is "E":
            sens = "E"
        elif sensor is "R":
            sens = "R"
        elif sensor is "B":
            sens = "B"
        elif sensor is "N":
            sens = "N"
        elif sensor is "K":
            sens = "K"
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        #self.write_to_dev("DISP:ENAB OFF") # display off for speed
        self.write_to_dev("SYST:FAZ OFF") # add front autozero (delta speed is half with it ON)
        self.write_to_dev("SYST:AZER OFF") # add autozero
        self.write_to_dev("SYST:LSYN OFF") # enable line synchronization
        self.set_nplc(0.1)
        self.write_to_dev("SENS:FUNC 'TEMP'")
        self.write_to_dev("UNIT:TEMP C") # celsius
        internal_temperature = float(self.query("SENS:TEMP:RTEM?")) # Get current room temperature
        self.write_to_dev("SENS:TEMP:TRAN TC") # thermocouple
        self.write_to_dev("SENS:TEMP:TC:TYPE "+sens) # Thermocouple type J,K,T
        self.write_to_dev("SENS:TEMP:RJUN:RSEL SIM") # set simulated reference junction
        #self.write_to_dev("SENS:TEMP:TC:RJUN:RSEL INT") # set internal reference junction (at screw terminals)
        self.write_to_dev("SENS:TEMP:RJUN:SIM "+str(internal_temperature)) # set reference temperature to 0°C
        #self.write_to_dev("ROUT:CLOS (@101)")
        return
        
    def setup_voltage_measurement(self,acdc="DC",nplc=0.1):
        self.what_is_measured = "voltage"
        acdc_scpi = "DC"
        if acdc is "AC":
            print "This device only supports DC-voltage measurements! No AC"
        self.set_nplc(nplc)
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        self.write_to_dev("SYST:FAZ ON") # add autozero
        self.write_to_dev("SYST:AZER ON") # add autozero
        self.write_to_dev("SYST:LSYN ON") # enable line synchronization
        self.write_to_dev("SENS:FUNC 'VOLT'")
        return
        
    def setup_voltage_ratio_measurement(self,acdc="DC",nplc=1):
        self.what_is_measured = "voltage_ratio"
        acdc_scpi = "DC"
        if acdc is "AC":
            print "This device only supports DC-voltage measurements! No AC"
        self.set_nplc(nplc)
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        self.write_to_dev("SYST:FAZ ON") # add autozero
        self.write_to_dev("SYST:AZER ON") # add autozero
        self.write_to_dev("SYST:LSYN ON") # enable line synchronization
        self.write_to_dev("SENS:FUNC 'VOLT'")
        self.write_to_dev("SENS:FUNC:VOLT:RAT ON")
        return
            
    def trigger(self):
        self.write_to_dev("*TRG")
        return
        
    def init(self):
        self.write_to_dev("INIT")
        return
        
    def reset(self):
        self.write_to_dev("*CLS") # reset device
        self.write_to_dev("*RST") # reset device
        return
        
    def close(self):
        self.write_to_dev("OUTP OFF")
        return self.device.close()
        
    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
        return

    def __exit__(self):
        try:
            self.close()
        except Exception:
            pass
        return
        
# Little demo to show how the class can be used to acquire a simple measurement
if __name__ == "__main__":
    Prologix_port = "/dev/ttyUSB0"
    GPIB_address = 13
    keithley_2182A = keithley_2182A(Prologix_port,GPIB_address)
    keithley_2182A.reset()
    keithley_2182A.debug = True
    keithley_2182A.setup_temperature_measurement()
    time.sleep(3)
    result = []
    for i in range(10):
        a = keithley_2182A.get_value()
        print "Temperature is: ",a[0]
        result.append(a)
    keithley_2182A.close()
    print result


