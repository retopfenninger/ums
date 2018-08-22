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

class keithley_6517B:
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
        self.what_is_measured = ""
        self.debug = False
        self.write_to_dev("++mode 1")
        self.write_to_dev("++addr " + str(address))
        self.write_to_dev("++auto 0")
        self.write_to_dev("++eos 3") # Dont append anything 0=CRLF 1=CR 2=LF 3=None
        self.write_to_dev("++eoi 1") # Indicate End-of-data
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
        return self.read_from_dev()
        
    def get_id(self):
        return "keithley_6517B"
        
    def checkError(self):
        self.write_to_dev("SYST:ERR?")
        self.write_to_dev("++read eoi")
        print self.read_from_dev()
        return self.read_from_dev()
        
    def setup_scan_channels(self,ch,num_measurements):
        self.what_is_measured = "scan"
        self.write_to_dev(":SENS:FUNC 'VOLT', (@101:120)")
        self.write_to_dev(":ROUT:SCAN(@101:120)")
        self.write_to_dev(":SAMP:COUN 20")
        self.write_to_dev(":TRIG:COUN 1")
        self.write_to_dev(":ROUT:SCAN:LSEL INT") # enable scan mode
        self.write_to_dev(":TRAC:FEED:CONT NEXT") # enable trace buffer
        self.write_to_dev("INIT")
        time.sleep(10)
        return self.query("DATA?")
        
    def get_2w_resistance(self,ch):#res
        self.what_is_measured = "res"
        self.write_to_dev("INIT:CONT OFF") # disable continous initiation
        self.write_to_dev("TRAC:CLE:AUTO OFF") # clear internal 55000 reading buffer
        self.write_to_dev("FORM:ELEM READ") # specifies data elements to return reading
        self.write_to_dev("SENS:FUNC 'RES', (@101:110)") # 4W-res-function
        self.write_to_dev("SENS:RES:NPLC 3, (@101:110)") # NPLC 3
        self.write_to_dev("SENS:RES:OCOM ON, (@101:110)") # 1 ohm range
        self.write_to_dev("TRIG:COUN 2")
        self.write_to_dev("SAMP:COUN 10")
        self.write_to_dev("ROUT:SCAN:LSEL INT") # enable internal scan
        self.write_to_dev("ROUT:SCAN (@101,110)") # scan list for channels 1 + 10
        self.write_to_dev("INIT")
        time.sleep(10)
        return self.query("DATA?") # initiate + request

        
    def get_4w_resistance(self,ch):#fres
        self.what_is_measured = "fres"
        self.write_to_dev("INIT:CONT OFF") # disable continous initiation
        self.write_to_dev("TRAC:CLE") # clear buffer
        self.write_to_dev("TRAC:CLE:AUTO OFF") # clear internal 55000 reading buffer
        #self.write_to_dev("TRAC:POIN 20") # clear internal 55000 reading buffer
        self.write_to_dev("FORM:ELEM READ") # specifies data elements to return reading
        self.write_to_dev("SENS:FUNC 'FRES', (@101,110)") # 4W-res-function
        self.write_to_dev("SENS:FRES:NPLC 10, (@101,110)") # NPLC 10
        self.write_to_dev("SENS:FRES:OCOM ON, (@101,110)") # 1 ohm range
        self.write_to_dev("TRIG:COUN 1")
        self.write_to_dev("SAMP:COUN 10")
        self.write_to_dev("ROUT:SCAN:LSEL INT") # enable internal scan
        #self.write_to_dev("ROUT:SCAN (@101,110)") # scan list for channels 1 + 10
        #self.write_to_dev("ROUT:CLOS (@101,110)") # close channel 1 for reading
        self.write_to_dev("INIT")
        time.sleep(5)
        return self.query("TRAC:DATA?") # initiate + request
        
    def setup_current_measurement(self,nplc=1):
        self.what_is_measured = "current"
        #self.write_to_dev("*CLS") # disable continous initiation
        #self.write_to_dev("TRAC:CLE") # clear buffer
        #self.write_to_dev("TRAC:CLE:AUTO OFF") # clear internal 50000 reading buffer
        #self.write_to_dev("TRAC:POIN 200") # clear internal 50000 reading buffer
        self.write_to_dev("SENS:FUNC 'CURR:DC'")
        self.write_to_dev("SENS:CURR:RANG:AUTO ON")
        #self.write_to_dev("SENS:CURR:OCOM ON")
        self.set_nplc(nplc,True)
        self.write_to_dev("SOUR:VOLT:MCON ON")
        #self.write_to_dev("SENS:RES:MAN:VSO:OPER ON")
        
        self.write_to_dev("SOUR:FUNC VOLT")
        #self.write_to_dev("SYST:ZCH ON")
        self.write_to_dev("SYST:ZCH OFF")
        return
        
    def setup_voltage_measurement(self,nplc=1):
        # For this connect the inner line of the triax to your device-under-test (DUT) and also the COMMON-line. This is the
        # best way for precise voltage measurements.
        self.what_is_measured = "voltage"
        self.write_to_dev("SENS:FUNC 'VOLT'")
        self.write_to_dev("SENS:VOLT:RANG:AUTO ON")
        self.set_nplc(nplc,False)
        self.write_to_dev("SENS:VOLT:DC:GUAR ON") # Enable guarding. Voltage measurements should NOT be done with a triax only. You shoud do it guarded
        self.write_to_dev("SOUR:FUNC CURR")
        self.write_to_dev("SYST:ZCH OFF")
        self.write_to_dev("OUTP1:STAT OFF") # This device cannot source current
        return
        
    def set_voltage(self,voltage):
        self.write_to_dev("SOUR:VOLT "+str(voltage))
        return
        
    def set_nplc(self,nplc,current=True):
        if nplc == 0.01:
            self.nplc_delay_time = 0.4
        elif nplc == 0.1:
            self.nplc_delay_time = 0.4
        elif nplc == 1:
            self.nplc_delay_time = 0.9
        elif nplc == 10:
            self.nplc_delay_time = 8
        if nplc in [0.01,0.1,1,10]:
            if current:
                self.write_to_dev("SENS:CURR:DC:NPLC "+str(nplc))
            else: # means voltage
                self.write_to_dev("SENS:VOLT:DC:NPLC "+str(nplc))
        return
        
    def set_voltage_range(self,voltage):
        if voltage <= 100:
            self.write_to_dev("SOUR:VOLT:RANGE 100")
        else:
            self.write_to_dev("SOUR:VOLT:RANGE 1000")
        return
        
    def get_value(self,which=None):
        val = self.parse_output(self.query("READ?"))
        if which is "counter":
            return val[2]
        if which is "value":
            return val[0]
        if which is "time":
            return val[1]
        else:
            return val

    def get_voltage(self): # needed for compatibility with keithley_26xxB
        if self.what_is_measured is "current":
            return None
        return self.get_value("value")
        
    def get_current(self): # needed for compatibility with keithley_26xxB
        if self.what_is_measured is "voltage":
            return None
        return self.get_value("value")
        
    def set_compliance_current(self): # needed for compatibility with keithley_26xxB
        print "WARNING: Keithley 6517B has no capability for setting a compliance current!"
        return
        
    def set_current(self): # needed for compatibility with keithley_26xxB
        print "WARNING: Keithley 6517B is setup in current measurement mode! You cannot source what you want to measure!"
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
        
    def turn_output_on(self):
        self.write_to_dev("OUTP1 ON")
        return
        
    def turn_output_off(self):
        self.write_to_dev("OUTP1 OFF")
        return
        
    def parse_output(self,answer_from_keithley):
        a = answer_from_keithley.split(',')
        res = None
        if self.what_is_measured is "current":
            res = [float(a[0][0:-4]),float(a[1][0:-4]),float(a[2][0:-6])]
        elif self.what_is_measured is "voltage":
            res = [float(a[0][0:-4]),float(a[1][0:-4]),float(a[2][0:-6])]
        #res = [a[0],a[1],a[2]]
        if res[0] == 9.91e37: # overflow
            res[0] = 0.0
        if res[1] == 9.91e37: # overflow
            res[1] = 0.0
        if res[2] == 9.91e37: # overflow
            res[2] = 0.0
        return res
        
    def close(self):
        self.write_to_dev("OUTP1 OFF")
        self.write_to_dev("SENS:RES:MAN:VSO:OPER OFF")
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
   
    ip_address = "192.168.1.29"
    gpib_address = 27
    keithley_6517B = keithley_6517B(ip_address,gpib_address)
    print keithley_6517B.query("*IDN?")
    keithley_6517B.reset()
    keithley_6517B.setup_current_measurement()
    keithley_6517B.set_voltage(0.0042)
    keithley_6517B.turn_output_on()
    keithley_6517B.init()
    time.sleep(2) # wait 2 sec for the device to become ready
    result = []
    for i in range(10):
        a = keithley_6517B.get_value()
        print "Current is: ",a[0]
        result.append(a)
    keithley_6517B.turn_output_off()
    keithley_6517B.close()
    print result

