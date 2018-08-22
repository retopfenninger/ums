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
import socket

class keithley_2701:
    def __init__(self, host):
        self.host = host
        self.io_timeout = 2
        self.lock_timeout = 2
        self.what_is_measured = ""
        self.nplc_delay_time = 0.2
        self.slot = None
        self.channel = None
        self.nplc = 1 # number of power line cycles
        self.channel_setup_done = False
        self.debug = False
        self.nplc_delay_time = self.nplc/50.0+self.io_timeout*0.001+self.lock_timeout*0.001+0.01
        # Create a TCP/IP socket
        self.device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set non-blocking
        #self.device.setblocking(0)
        self.device.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.server_address = (self.host, 1394)
        self.device.connect(self.server_address)
        

    def get_value(self): # needed for compatibility
        answer_from_keithley = self.query("READ?")
        a = answer_from_keithley.split(',')
        res = [[0,0,0] for i in range(len(self.channel))]
        j = 0
        if self.what_is_measured is "temperature":
            for i in range(len(self.channel)):
                if self.test_for_overflow(a[j]):
                    g = 0.0
                else:
                    g = a[j][0:-2]
                if i == range(len(self.channel))[-1]:
                    res[i] = [float(g),float(a[j+1][0:-4]),float(a[j+2][0:-6])] # last value has an additional "\n" at the end
                else:
                    res[i] = [float(g),float(a[j+1][0:-4]),float(a[j+2][0:-5])]
                j = j+3
        elif self.what_is_measured is "voltage":
            for i in range(len(self.channel)):
                if self.test_for_overflow(a[j]):
                    g = 0.0
                else:
                    g = a[j][0:-3]
                if i == range(len(self.channel))[-1]:
                    res[i] = [float(g),float(a[j+1][0:-4]),float(a[j+2][0:-6])] # last value has an additional "\n" at the end
                else:
                    res[i] = [float(g),float(a[j+1][0:-4]),float(a[j+2][0:-5])]
                j = j+3
        elif self.what_is_measured is "current":
            for i in range(len(self.channel)):
                if self.test_for_overflow(a[j]):
                    g = 0.0
                else:
                    g = a[j][0:-3]
                if i == range(len(self.channel))[-1]:
                    res[i] = [float(g),float(a[j+1][0:-4]),float(a[j+2][0:-6])] # last value has an additional "\n" at the end
                else:
                    res[i] = [float(g),float(a[j+1][0:-4]),float(a[j+2][0:-5])]
                j = j+3
        elif self.what_is_measured is "2w_resistance":
            for i in range(len(self.channel)):
                if self.test_for_overflow(a[j]):
                    g = 0.0
                else:
                    g = a[j][0:-3]
                if i == range(len(self.channel))[-1]:
                    res[i] = [float(g),float(a[j+1][0:-4]),float(a[j+2][0:-6])] # last value has an additional "\n" at the end
                else:
                    res[i] = [float(g),float(a[j+1][0:-4]),float(a[j+2][0:-5])]
                j = j+3
        elif self.what_is_measured is "4w_resistance":
            for i in range(len(self.channel)):
                if self.test_for_overflow(a[j]):
                    g = 0.0
                else:
                    g = a[j][0:-3]
                if i == range(len(self.channel))[-1]:
                    res[i] = [float(g),float(a[j+1][0:-4]),float(a[j+2][0:-6])] # last value has an additional "\n" at the end
                else:
                    res[i] = [float(g),float(a[j+1][0:-4]),float(a[j+2][0:-5])]
                j = j+3
        elif self.what_is_measured is "frequency":
            for i in range(len(self.channel)):
                if self.test_for_overflow(a[j]):
                    g = 0.0
                else:
                    g = a[j][0:-2]
                if i == range(len(self.channel))[-1]:
                    res[i] = [float(g),float(a[j+1][0:-4]),float(a[j+2][0:-6])] # last value has an additional "\n" at the end
                else:
                    res[i] = [float(g),float(a[j+1][0:-4]),float(a[j+2][0:-5])]
                j = j+3
        if len(res) == 1:
            return [res[0][0],time.time()]
        return [[res[i][0] for i in range(len(res))],time.time()]

    def test_for_overflow(self, x):
        try:
            a = float(x)
            if a >= 9.9e37:
                return True
            return False
        except ValueError:
            return False
            
    def write_to_dev(self, string):
        if self.debug:
            print "Just wrote: ",string
        self.device.sendall(string + "\r\n")
        #time.sleep(2)
        return
        
    def read_from_dev(self):
        a = self.receive_command(self.device)
        if self.debug:
            print a
        return a
        
    def receive_command(self,connection,timeout=2):
        #make socket non blocking
        connection.setblocking(0)
        #total data partwise in an array
        total_data=[];
        data='';
        #beginning time
        begin=time.time()
        while 1:
            #if you got some data, then break after timeout
            if total_data and time.time()-begin > timeout:
                break
            #if you got no data at all, wait a little longer, twice the timeout
            elif time.time()-begin > timeout*2:
                break
            #recv something
            try:
                data = connection.recv(8192)
                if data:
                    total_data.append(data)
                    #change the beginning time for measurement
                    begin=time.time()
                else:
                    #sleep for sometime to indicate a gap
                    time.sleep(0.1)
            except:
                pass
        #join all parts to make final string
        return ''.join(total_data)
        
    def query(self, string):
        self.write_to_dev(string)
        time.sleep(self.nplc_delay_time)
        return self.read_from_dev()
        
    def get_id(self):
        return "keithley_2701"
        
    def checkError(self):
        self.write_to_dev("SYST:ERR?")
        print self.read_from_dev()
        return self.read_from_dev()
        
    def setup_temperature_measurement(self,sensor="K",slot=None,channel=None,nplc=5):
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
        self.write_to_dev("SYST:AZER:STAT ON") # add autozero
        self.write_to_dev("SYST:LSYN:STAT OFF") # disable line synchronization
        #self.write_to_dev("DISP:ENAB OFF") # disable display for speed
        scpi_array = self.parse_scpi_channel_string(slot,channel)
        self.write_to_dev("CONF:TEMP"+scpi_array)
        #self.write_to_dev("SENS:FUNC 'TEMP', "+scpi_array)
        self.write_to_dev("UNIT:TEMP C") # celsius
        self.write_to_dev("SENS:TEMP:NPLC "+str(nplc)) # set nplc. Default is 5 for TEMP
        self.set_nplc(nplc)
        self.write_to_dev("SENS:TEMP:TRAN TC") # thermocouple
        self.write_to_dev("SENS:TEMP:TC:TYPE "+sens) # Thermocouple type J,K,T
        self.write_to_dev("SENS:TEMP:TC:RJUN:RSEL SIM") # set simulated reference junction
        #self.write_to_dev("SENS:TEMP:TC:RJUN:RSEL INT") # set internal reference junction (at screw terminals)
        #self.write_to_dev("SENS:TEMP:RJUN:SIM "+str(internal_temperature)) # set reference temperature to 0°C
        if not self.channel_setup_done:
            self.setup_scan_channels(slot,channel)
            self.channel_setup_done = True
        return
        
    def setup_voltage_measurement(self,acdc="DC",nplc=1,slot=None,channel=None):
        self.what_is_measured = "voltage"
        scpi_array = self.parse_scpi_channel_string(slot,channel)
        acdc_scpi = "DC"
        if acdc is "AC":
            acdc_scpi = "AC"
            self.write_to_dev("VOLT:AC:DET:BAND 300")
            self.write_to_dev("SENS:VOLT:AC:NPLC "+str(nplc))
        else:
            self.write_to_dev("SENS:VOLT:DC:NPLC "+str(nplc))
        self.set_nplc(nplc)
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        self.write_to_dev("SYST:AZER:STAT ON") # add autozero
        self.write_to_dev("SYST:LSYN:STAT OFF") # disable line synchronization
        #self.write_to_dev("DISP:ENAB OFF") # disable display for speed
        self.write_to_dev("SENS:FUNC 'VOLT:"+acdc_scpi+"'")
        self.write_to_dev("CONF:VOLT:"+acdc_scpi+scpi_array)
        if not self.channel_setup_done:
            self.setup_scan_channels(slot,channel)
            self.channel_setup_done = True
        return
        
    def setup_current_measurement(self,acdc="DC",nplc=1,slot=None,channel=None):
        self.what_is_measured = "current"
        scpi_array = self.parse_scpi_channel_string(slot,channel)
        acdc_scpi = "DC"
        if acdc is "AC":
            acdc_scpi = "AC"
            self.write_to_dev("CURR:AC:DET:BAND 300")
            self.write_to_dev("SENS:CURR:AC:NPLC "+str(nplc))
        else:
            self.write_to_dev("SENS:CURR:DC:NPLC "+str(nplc))
        self.set_nplc(nplc)
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        self.write_to_dev("SYST:AZER:STAT ON") # add autozero
        self.write_to_dev("SYST:LSYN:STAT OFF") # disable line synchronization
        #self.write_to_dev("DISP:ENAB OFF") # disable display for speed
        self.write_to_dev("SENS:FUNC 'CURR:"+acdc_scpi+"'")
        self.write_to_dev("CONF:CURR:"+acdc_scpi+scpi_array)
        if not self.channel_setup_done:
            self.setup_scan_channels(slot,channel)
            self.channel_setup_done = True
        return
        
    def setup_2w_resistance_measurement(self,nplc=1,slot=None,channel=None): #res
        self.what_is_measured = "2w_resistance"
        scpi_array = self.parse_scpi_channel_string(slot,channel)
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        self.write_to_dev("SYST:AZER:STAT ON") # add autozero
        self.write_to_dev("SYST:LSYN:STAT OFF") # disable line synchronization
        #self.write_to_dev("DISP:ENAB OFF") # disable display for speed
        self.write_to_dev("SENS:FUNC 'RES'") # 2W-res-function
        self.write_to_dev("SENS:RES:NPLC "+str(nplc)) # NPLC 3
        self.set_nplc(nplc)
        self.write_to_dev("CONF:RES"+scpi_array)
        self.nplc_delay_time = self.nplc_delay_time+0.2 # Ohm measurement takes apparently a bit longer
        #self.write_to_dev("SENS:RES:OCOM ON, "+scpi_array) # 1 ohm range
        if not self.channel_setup_done:
            self.setup_scan_channels(slot,channel)
            self.channel_setup_done = True
        return
        
    def setup_4w_resistance_measurement(self,nplc=5,slot=None,channel=None):#fres
        self.what_is_measured = "4w_resistance"
        scpi_array = self.parse_scpi_channel_string(slot,channel)
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        self.write_to_dev("SYST:AZER:STAT ON") # add autozero
        self.write_to_dev("SYST:LSYN:STAT OFF") # disable line synchronization
        #self.write_to_dev("DISP:ENAB OFF") # disable display for speed
        self.write_to_dev("SENS:FUNC 'FRES'") # 4W-res-function
        self.write_to_dev("SENS:FRES:NPLC "+str(nplc)) # NPLC 5
        self.set_nplc(nplc)
        self.write_to_dev("CONF:FRES"+scpi_array)
        self.nplc_delay_time = self.nplc_delay_time+0.2 # Ohm measurement takes apparently a bit longer
        #self.write_to_dev("SENS:RES:OCOM ON, "+scpi_array) # 1 ohm range
        if not self.channel_setup_done:
            self.setup_scan_channels(slot,channel)
            self.channel_setup_done = True
        return
        
    def setup_frequency_measurement(self,slot=None,channel=None):
        self.what_is_measured = "frequency"
        scpi_array = self.parse_scpi_channel_string(slot,channel)
        self.write_to_dev("SYST:BEEP:STAT OFF") # stop beeper on 110 error
        self.write_to_dev("SYST:AZER:STAT ON") # add autozero
        self.write_to_dev("SYST:LSYN:STAT OFF") # disable line synchronization
        #self.write_to_dev("DISP:ENAB OFF") # disable display for speed
        self.write_to_dev("SENS:FUNC 'FREQ'") # 4W-res-function
        self.write_to_dev("CONF:FREQ"+scpi_array)
        self.nplc_delay_time = self.nplc_delay_time+0.5 # measurement takes apparently a bit longer
        if not self.channel_setup_done:
            self.setup_scan_channels(slot,channel)
            self.channel_setup_done = True
        return
        
    def setup_scan_channels(self,slot,channel,num_measurements=1):
        self.slot = slot
        self.channel = channel
        self.channel_setup_done = True
        if slot is None or channel is None:
            self.channel = [1] # To make get_value() work
            return
        scpi_array = self.parse_scpi_channel_string(slot,channel)
        total_number_of_channels_to_scan = len(slot)*len(channel)
        self.nplc_delay_time = self.nplc_delay_time+0.2*(self.nplc_delay_time*total_number_of_channels_to_scan*num_measurements)
        self.write_to_dev("TRAC:CLE")
        self.write_to_dev("TRAC:CLE:AUTO OFF")
        self.write_to_dev("INIT:CONT OFF")
        self.write_to_dev("TRIG:SOUR IMM")
        self.write_to_dev("TRIG:COUN "+str(num_measurements))
        self.write_to_dev("SAMP:COUN "+str(total_number_of_channels_to_scan))
        self.write_to_dev("ROUT:SCAN"+scpi_array)
        self.write_to_dev("ROUT:SCAN:TSO IMM")
        self.write_to_dev("ROUT:SCAN:LSEL INT") # enable scan mode
        self.write_to_dev("STAT:QUE:DIS, (-110)") # disable silly error messages lining up in buffer
        time.sleep(3+self.nplc_delay_time) # yes, you really need this crazy shit in the next 4 lines in order to make it work! I tested it!
        self.write_to_dev("READ?")
        time.sleep(3+self.nplc_delay_time)
        dummy_reading = self.read_from_dev() # needed to get the device in a fastly responsive state
        return
        
    def open_channel(self,slot,channel,multiple=False):
        scpi_array = self.parse_scpi_channel_string(slot,channel)
        if multiple: # Needed for relay card 7705
            self.write_to_dev("ROUT:MULT:OPEN"+scpi_array)
        else:
            self.write_to_dev("ROUT:OPEN"+scpi_array)
        time.sleep(0.5)
        return
        
    def close_channel(self,slot,channel,multiple=False):
        scpi_array = self.parse_scpi_channel_string(slot,channel)
        if multiple: # Needed for relay card 7705
            self.write_to_dev("ROUT:MULT:CLOS"+scpi_array)
        else:
            self.write_to_dev("ROUT:CLOS"+scpi_array)
        time.sleep(0.5)
        return
        
    def parse_scpi_channel_string(self,slot,channel):
        if slot is None or channel is None:
            return ""
        scpi_array = " (@"
        if type(slot)==int:
           slot = [slot] # make an array
        if type(channel)==int:
           channel = [channel]
        for s in slot:
           for c in channel:
              if len(str(c)) == 1:
                  c="0"+str(c) # one digit channel needs to be addressed as @101 or 102,... and so on
              scpi_array=scpi_array+str(s)+str(c)+","
        scpi_array=scpi_array[0:-1] # remove last comma
        scpi_array=scpi_array+")"
        return scpi_array
        
    def set_nplc(self,nplc,current=True):
        self.nplc = nplc
        if nplc == 0.01:
            self.nplc_delay_time = 0.1
        elif nplc == 0.1:
            self.nplc_delay_time = 0.1
        elif nplc == 1:
            self.nplc_delay_time = 0.2
        elif nplc == 5:
            self.nplc_delay_time = 0.3
        elif nplc == 10:
            self.nplc_delay_time = 1
        return
        
    def install_pseudocard(self,slot=1,card="7700"): # Do not use
        self.write_to_dev("SYST:PCAR"+str(slot)+" C"+str(card))
        return
        
    def reset(self):
        self.write_to_dev("*RST") # reset device
        return
        
    def close(self):
        self.write_to_dev("DISP:ENAB ON")
        self.write_to_dev("ROUT:OPEN ALL") # open all channels
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
   
    ip_address = "172.31.27.122"
    keithley_2701 = keithley_2701(ip_address)
    keithley_2701.reset()
    keithley_2701.setup_temperature_measurement()
    time.sleep(2) # wait 2 sec for the device to become ready
    result = []
    for i in range(10):
        a = keithley_2701.get_value()
        print "Temperature is: ",a[0]
        result.append(a)
    keithley_2701.close()
    print result

