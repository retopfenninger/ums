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

class keithley_6220:
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
        self.actual_current = 0
        self.debug = False
        self.write_to_dev("++mode 1")
        self.write_to_dev("++addr " + str(address))
        self.write_to_dev("++auto 0")
        self.write_to_dev("++eos 3") # Dont append anything 0=CRLF 1=CR 2=LF 3=None
        self.write_to_dev("++eoi 1") # Indicate End-of-data
        self.nplc_delay_time = 1.0
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
        return "keithley_6220"
        
    def setup_current_measurement(self,nplc=1): # needed for compatibility with keithley_26xxB
        print "WARNING: Keithley 6220 has no capability for measuring current!"
        return
        
    def setup_voltage_measurement(self,nplc=1):
        print "WARNING: Keithley 6220 has no capability for measuring voltage! (Very stupid since it's intrinsically possible, sothe AD-converter would be there)"
        return
        
    def set_voltage(self,voltage): # needed for compatibility with keithley_26xxB
        print "WARNING: Keithley 6220 has no capability for setting voltage! Only compliance-voltage can be set!"
        return   

    def get_voltage(self): # This device cannot return any readings
        return None 
        
    def get_current(self): # No actual measurement possible. Just return the programmed value
        return self.actual_current
        
    def set_compliance_current(self): # needed for compatibility with keithley_26xxB
        print "WARNING: Keithley 6220 has no capability for setting a compliance current!"
        return
        
    def set_compliance_voltage(self,value):
        self.write_to_dev("SOUR:CURR:COMP "+str(value))
        return
        
    def set_triax_inner_shield_to_low(self):
        self.turn_output_off()
        self.write_to_dev("OUTP:ISH OLOW")
        return
        
    def set_triax_inner_shield_to_guard(self):
        self.turn_output_off()
        self.write_to_dev("OUTP:ISH GUAR")
        return
        
    def set_triax_output_low_to_earth(self):
        self.turn_output_off()
        self.write_to_dev("OUTP:LTE ON")
        return
        
    def set_triax_output_low_to_floating(self):
        self.turn_output_off()
        self.write_to_dev("OUTP:LTE OFF")
        return
        
    def set_current(self,value):
        self.write_to_dev("SOUR:CURR:AMPL "+str(value))
        self.actual_current = value
        return
            
    def trigger(self):
        self.write_to_dev("*TRG")
        return
        
    def init(self):
        self.write_to_dev("INIT")
        return
        
    def reset(self):
        self.write_to_dev("CLE") # reset device
        self.write_to_dev("*CLS") # reset device
        self.write_to_dev("*RST") # reset device
        return
        
    def turn_output_on(self):
        self.write_to_dev("OUTP ON")
        return
        
    def turn_output_off(self):
        self.write_to_dev("OUTP OFF")
        self.actual_current = 0
        return
        
    def close(self):
        self.write_to_dev("OUTP OFF")
        self.write_to_dev("SOUR:IMM") # set current to zero and then turn off
        self.actual_current = 0
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
        
# Little demo to show how the class can be used to set currents
if __name__ == "__main__":
   
    ip_address = "192.168.1.48"
    gpib_address = 12
    keithley_6220 = keithley_6220("electrochem-m27",gpib_address)
    print keithley_6220.query("*IDN?")
    keithley_6220.reset()
    keithley_6220.set_current(1e-9) # A
    keithley_6220.set_compliance_voltage(1.0) # V
    keithley_6220.turn_output_on()
    print "Output has been turned on"
    time.sleep(5) # wait 2 sec for the device to become ready
    keithley_6220.turn_output_off()
    print "Output has been turned off"
    keithley_6220.close()

