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

class keithley_740:
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
        self.write_to_dev("++eos 0")# Dont append anything 0=CRLF 1=CR 2=LF 3=None
        self.write_to_dev("++eoi 1") # Indicate End-of-data
        time.sleep(1)

    def write_to_dev(self, string):
        if self.debug:
            print "Just wrote: ",string
        self.device.write(string + "\n")
        time.sleep(0.5)
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
        return "keithley_740"
        
    def get_temperature(self):
        val = self.query("B0G2X")
        #time.sleep(0.5)
        self.query("M08X")
        #val = self.query("BOG2X")
        #formatted_val = val.split(".")[0][4:]
        result = float(val)
        return  result # initiate + request READ?
        
    def get_value(self):
        val = self.query("B0G2X")
        #time.sleep(0.5)
        self.query("M08X")
        #val = self.query("BOG2X")
        #formatted_val = val.split(".")[0][4:]
        result = float(val)
        A = [result,time.time()]
        return A # initiate + request READ?
        
    def setup_temperature_measurement(self,sensor="K",internal_temperature=23):
        return
        
    def reset(self):
        return
        
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
   
    ip_address = "192.168.1.13"
    gpib_address = 27
    keithley_740 = keithley_740(ip_address,gpib_address)
    print keithley_740.query("*IDN?")
    keithley_740.reset()
    keithley_740.setup_temperature_measurement()
    keithley_740.turn_output_on()
    keithley_740.init()
    time.sleep(2) # wait 2 sec for the device to become ready
    result = []
    for i in range(10):
        a = keithley_740.get_value()
        print "Temperature is: ",a[0]
        result.append(a)
    keithley_740.turn_output_off()
    keithley_740.close()
    print result

#print d.query("*OPT?")
#print d.read_channel(2,1)
#print d.get_4w_resistance("111")
#print d.query("*IDN?")
#d.setv("RANG:AUTO ON")

