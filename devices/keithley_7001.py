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

class keithley_7001:
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
        #self.write_to_dev("++mode 1")
        #self.write_to_dev("++addr " + str(address))
        #self.write_to_dev("++auto 1")
        self.debug = False
        self.operations_per_second = 3
        self.write_to_dev("++mode 1")
        self.write_to_dev("++addr " + str(address))
        self.write_to_dev("++auto 0")
        self.write_to_dev("++eos 3") # Dont append anything 0=CRLF 1=CR 2=LF 3=None
        self.write_to_dev("++eoi 1") # Indicate End-of-data
        self.write_to_dev("*RST;OPEN ALL") # reset device
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
        return self.read_from_dev()
        
    def get_id(self):
        return "keithley_7001"
        
    def checkError(self):
        self.write_to_dev("SYST:ERR?")
        self.write_to_dev("++read eoi")
        print self.read_from_dev()
        return self.read_from_dev()
        
    def open_channel(self,slot,channel):
        scpi_array = "(@"
        if type(slot)==int:
           slot = [slot] # make an array
        if channel is "all":
           self.write_to_dev(":ROUT:OPEN ALL")
           return
        if type(channel)==int:
           channel = [channel]
        for s in slot:
           for c in channel:
              scpi_array=scpi_array+str(s)+"!"+str(c)+","
        scpi_array=scpi_array[0:-1] # remove last comma
        scpi_array=scpi_array+")"
        self.write_to_dev(":ROUT:OPEN "+scpi_array)
        time.sleep(0.5)
        return
        
    def close_channel(self,slot,channel):
        scpi_array = "(@"
        if type(slot)==int:
           slot = [slot] # make an array
        if type(channel)==int:
           channel = [channel]
        for s in slot:
           for c in channel:
              scpi_array=scpi_array+str(s)+"!"+str(c)+","
        scpi_array=scpi_array[0:-1] # remove last comma
        scpi_array=scpi_array+")"
        self.write_to_dev(":ROUT:CLOS "+scpi_array)
        time.sleep(0.5)
        return
        
    def get_slot_timing(self,slot=1):
        slot_scpi= "SLOT1"
        if slot is 1:
            slot_scpi = "SLOT1"
        else:
            slot_scpi = "SLOT2"
        return self.query(":ROUT:CONF:"+slot_scpi+":STIM?") # initiate + request READ?
        
    def get_close_status(self):
        return self.query(":ROUT:CLOS:STAT?") # initiate + request READ?
        
    def reset(self):
        self.write_to_dev("*RST") # reset device
        return
        
    def close(self):
        self.open_channel(1,"all")
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

# Little demo to show how the class can be used to open channels
if __name__ == "__main__":
   
    ip_address = "192.168.1.24"
    gpib_address = 14
    keithley_7001 = keithley_7001(ip_address,gpib_address)
    keithley_7001.reset()
    keithley_7001.close_channel(1,12) # slot 1, channel 12
    print "Slot 1 Channel 12 has been closed"
    time.sleep(5)
    keithley_7001.open_channel(1,12) # slot 1, channel 12
    print "Slot 1 Channel 12 has been opened"
    keithley_7001.close()

