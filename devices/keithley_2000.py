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

class keithley_2000:
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
        self.debug = False
        self.write_to_dev("++mode 1")
        self.write_to_dev("++addr " + str(address))
        self.write_to_dev("++auto 0")
        self.write_to_dev("++eos 3") # Dont append anything 0=CRLF 1=CR 2=LF 3=None
        self.write_to_dev("++eoi 1") # Indicate End-of-data
        self.write_to_dev("*RST") # reset device
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        time.sleep(1.0)

    def write_to_dev(self, string):
        if self.debug:
            print "Just wrote: ",string
        self.device.write(string + "\n")
        #time.sleep(0.5)
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
        return self.read_from_dev()
        
    def get_id(self):
        return "keithley_2000"
        
    def checkError(self):
        self.write_to_dev("SYST:ERR?")
        self.write_to_dev("++read eoi")
        print self.read_from_dev()
        return self.read_from_dev()
        
    def setup_scan_channels(self,ch,num_measurements):
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        self.write_to_dev(":SENS:FUNC 'VOLT', (@101:120)")
        self.write_to_dev(":ROUT:SCAN(@101:120)")
        self.write_to_dev(":SAMP:COUN 20")
        self.write_to_dev(":TRIG:COUN 1")
        self.write_to_dev(":ROUT:SCAN:LSEL INT") # enable scan mode
        self.write_to_dev(":TRAC:FEED:CONT NEXT") # enable trace buffer
        self.write_to_dev("INIT")
        
        #self.write_to_dev("SYST:PRES")
        #self.write_to_dev("INIT:CONT OFF")
        #self.write_to_dev("ABOR")
        #self.write_to_dev("TRAC:CLE")
        #self.write_to_dev("TRIG:COUN 1")
        #self.write_to_dev("SAMP:COUN " + str(num_measurements))
        ##self.write_to_dev("INIT")
        #self.write_to_dev("MEAS:VOLT 10, 0.01, (@101)")
        time.sleep(10)
        return self.query("DATA?")
        
    def setup_temperature_measurement(self,sensor="K",internal_temperature=23):
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
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
        self.write_to_dev("SENS:FUNC 'TEMP'")
        self.write_to_dev("UNIT:TEMP C") # celsius
        #self.write_to_dev("SENS:TEMP:TRAN TC") # thermocouple
        self.write_to_dev("SENS:TEMP:TC:TYPE "+sens) # Thermocouple type J,K,T
        self.write_to_dev("SENS:TEMP:RJUN:RSEL SIM") # set simulated reference junction
        self.write_to_dev("SENS:TEMP:RJUN:SIM "+str(internal_temperature)) # set reference temperature to 0°C
        self.write_to_dev("INIT:CONT OFF") # disable continous initiation
        return
        
    def setup_voltage_measurement(self,acdc="DC",nplc=1):
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        acdc_scpi = "DC"
        if acdc is "AC":
            acdc_scpi = "AC"
        self.write_to_dev("SENS:FUNC 'VOLT:"+acdc_scpi+"'")
        self.write_to_dev("INIT:CONT OFF") # disable continous initiation
        return
        
    def setup_current_measurement(self,acdc="DC",nplc=1):
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        acdc_scpi = "DC"
        if acdc is "AC":
            acdc_scpi = "AC"
        self.write_to_dev("SENS:FUNC 'CURR:"+acdc_scpi+"'")
        self.write_to_dev("INIT:CONT OFF") # disable continous initiation
        return
        
    def setup_2w_resistance(self,nplc=1):#res
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        self.write_to_dev("INIT:CONT OFF") # disable continous initiation
        #self.write_to_dev("TRAC:CLE:AUTO OFF") # clear internal 55000 reading buffer
        #self.write_to_dev("FORM:ELEM READ") # specifies data elements to return reading
        self.write_to_dev("SENS:FUNC 'RES'") # 4W-res-function
        self.write_to_dev("SENS:RES:NPLC "+str(nplc)) # NPLC 3
        #self.write_to_dev("SENS:RES:OCOM ON, (@101:110)") # 1 ohm range
        #self.write_to_dev("TRIG:COUN 2")
        #self.write_to_dev("SAMP:COUN 10")
        #self.write_to_dev("ROUT:SCAN:LSEL INT") # enable internal scan
        #self.write_to_dev("INIT")
        return
        
    def setup_4w_resistance(self,nplc=1):#fres
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        self.write_to_dev("INIT:CONT OFF") # disable continous initiation
        #self.write_to_dev("TRAC:CLE") # clear buffer
        #self.write_to_dev("TRAC:CLE:AUTO OFF") # clear internal 55000 reading buffer
        #self.write_to_dev("TRAC:POIN 20") # clear internal 55000 reading buffer
        #self.write_to_dev("FORM:ELEM READ") # specifies data elements to return reading
        self.write_to_dev("SENS:FUNC 'FRES'") # 4W-res-function
        self.write_to_dev("SENS:FRES:NPLC "+str(nplc)) # NPLC 10
        #self.write_to_dev("SENS:FRES:OCOM ON, (@101,110)") # 1 ohm range
        #self.write_to_dev("TRIG:COUN 1")
        #self.write_to_dev("SAMP:COUN 10")
        #self.write_to_dev("ROUT:SCAN:LSEL INT") # enable internal scan
        #self.write_to_dev("ROUT:SCAN (@101,110)") # scan list for channels 1 + 10
        #self.write_to_dev("ROUT:CLOS (@101,110)") # close channel 1 for reading
        #self.write_to_dev("INIT")
        return
        
    def setup_frequency_measurement(self,nplc=1):
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        self.write_to_dev("INIT:CONT OFF") # disable continous initiation
        #self.write_to_dev("TRAC:CLE") # clear buffer
        #self.write_to_dev("TRAC:CLE:AUTO OFF") # clear internal 55000 reading buffer
        #self.write_to_dev("TRAC:POIN 20") # clear internal 55000 reading buffer
        #self.write_to_dev("FORM:ELEM READ") # specifies data elements to return reading
        self.write_to_dev("SENS:FUNC 'FREQ'") # 4W-res-function
        self.write_to_dev("SENS:FRES:NPLC "+str(nplc)) # NPLC 10
        #self.write_to_dev("SENS:FRES:OCOM ON, (@101,110)") # 1 ohm range
        #self.write_to_dev("TRIG:COUN 1")
        #self.write_to_dev("SAMP:COUN 10")
        #self.write_to_dev("ROUT:SCAN:LSEL INT") # enable internal scan
        #self.write_to_dev("ROUT:SCAN (@101,110)") # scan list for channels 1 + 10
        #self.write_to_dev("ROUT:CLOS (@101,110)") # close channel 1 for reading
        #self.write_to_dev("INIT")
        return
        
    def reset(self):
        self.write_to_dev("*RST") # reset device
        return
        
    def get_value(self):
        A = [float(self.query("READ?")),time.time()]
        return A # initiate + request READ?
        
    def close(self):
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
    keithley_2000 = keithley_2000(Prologix_port,GPIB_address)
    keithley_2000.reset()
    keithley_2000.debug = True
    keithley_2000.setup_temperature_measurement()
    time.sleep(3)
    result = []
    for i in range(10):
        a = keithley_2000.get_value()
        print "Temperature is: ",a[0]
        result.append(a)
    keithley_2000.close()
    print result

