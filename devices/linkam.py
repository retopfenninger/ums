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

import serial
import time
import sys

class linkam:
    """Instrument class for Linkam T-95 process controller and LNP-95 cryo controller.
    IMPORTANT: It only works with a modified RS232-cable where you connect the pins exactly like written here.
    
              9 way 'D' type on the computer                                        25 way 'D' type on the computer
              Linkam                Computer                                      Linkam                Computer
              TX     pin 3 ------ RX   pin 2                                     TX     pin 3 ------  RX   pin 3
              RX     pin 2 ------ TX   pin 3                                     RX     pin 2 ------  TX   pin 2
              RTS    pin 7 ------ CTS  pin 8                                     RTS    pin 7 ------  CTS  pin 5
              CTS    pin 8 ------ RTS  pin 7                                     CTS    pin 8 ------  RTS  pin 4
              GND    pin 5 -----  GND  pin 5                                     GND    pin 5 ------  GND  pin 7
              GND    pin 5 ------ DSR  pin 6                                     GND    pin 5 ------- DSR  pin 6
                           ------ DTR  pin 4  
     The serial computer port follows a DTE  pinout and uses a RTS/CTS handshake. If your computer does
     not drive CTS then connect pin 5 to the computers DTR line and DSR line
    """
    def __init__(self, portname):
        self.oven_name = str(portname)+" Linkam"
        self.oven_constant = 0.000078 # default value
        if "/" not in portname: # means instead of a serial port name, a pseudoname has been used
            if portname.lower() == "THMSG600": # goes from -196°C to 600°C
                portname = "/dev/ttyS0"
                self.oven_constant = 0.000079 # calculated from exponential air-cooling curve
                self.oven_name = "THMSG600"
            else:
                self.oven_constant = 0
                self.oven_name = "linkam heating stage"
                sys.exit("No heating stage with the name: \""+str(portname)+"\" has been found. This means we never tested such a stage. But it should work fine anyway. Either use a correct pseudoname or address the serial port directly (See manual)")
        self.room_temperature = 23
        self.debug = False
        self.termination_chars = '\r' #'\x0d'+'\x00' #"D" # '\x0d==CR + '\x00'
        self.current_ramp_rate = 0
        self.started = False
        self.sleep_time = 0.2
        self.status = ""
        self.error = ""
        self.pump_status = 0
        self.pump_in_manual_mode = False
        self.status_byte = ["Stopped", "Heating", "Cooling", "Holding at the limit reached end of ramp","Holding the limit time", "Holding the current temperature"]
        self.error_info = ["Cooling rate too fast", "Open circuit", "Power surge", "No Exit at temperature >300°C", "Link error", "Not error"]
        self.pump_status_byte = ["LNP Stopped","Minimum speed (Band 1 LED on the front panel of the LNP","Maximum speed (Band 5 LED on the front panel of the LNP"]
        self.serial = serial.Serial(port=portname, baudrate=19200, parity=serial.PARITY_NONE, bytesize=8, stopbits=1, rtscts=False, timeout=0.5)
        print "###########################################################################"
        print "       "+self.oven_name+" (with id: "+str(self.get_id())+")"
        print "###########################################################################"

    def write_to_dev(self, string):
        if self.debug:
            print "Just wrote: ",string
        self.serial.write(string + self.termination_chars)
        time.sleep(self.sleep_time)
        return

    def read_from_dev(self):
        a = self.serial.read(14)
        if a == '\r':
            a = "CR (means OK)"
        if self.debug:
            print "Just received: ",a," Status: ",self.get_status()," Error: ",self.get_error()," Pump_status: ",self.get_pump_status()
        return a
        
    def query(self, string):
        self.write_to_dev(string)
        return self.read_from_dev()
        
    def get_id(self):
        return "linkam"

    ## Process value
    def get_pv(self):
        try:
            a = self.query("T") # write_read_socket("T", 6) read 14 bit cut at 7
            self.status = ord(a[0])
            self.error = ord(a[1])
            self.pump_status = ord(a[2])
            temperature = int(a[6:10],16)/10.0
            if temperature > 32768:
                temperature = temperature - 65536
        except IOError:
            return None # Error during communication, Return a integer value nevertheless to make the program not crash.
        return temperature
    
    def get_op(self):
        return
        
    def get_id(self):
        """Return the customer defined identification number"""
        return self.get_oven_name()
        
    def get_oven_constant(self):
        """Return the exponential coefficient of the air-cooling curve"""
        return float(self.oven_constant)
        
    def get_oven_name(self):
        return self.oven_name

    def get_heater_current(self):
        return
        
    def get_program_status(self):
        return self.get_status()
        
    def get_current_program_running(self):
        return self.get_status()
        
    def select_setpoint(self,setpoint): # for compatibility with Eurotherm controllers
        return
        
    def get_status(self):
        """Return the status"""
        returnval = self.status
        if returnval == 1:
            return self.status_byte[0]
        elif returnval == 16:
            return self.status_byte[1]
        elif returnval == 32:
            return self.status_byte[2]
        elif returnval == 48:
            return self.status_byte[3]
        elif returnval == 64:
            return self.status_byte[4]
        elif returnval == 80:
            return self.status_byte[5]
        return
        
    def get_pump_status(self):
        returnval = self.pump_status
        if returnval == 128:
            return self.pump_status_byte[0]
        elif returnval == 129:
            return self.pump_status_byte[1]
        elif returnval == 158:
            return self.pump_status_byte[2]
        elif returnval == 0:
            return "NA"
        return "Pump running at: ",self.get_pump_speed(),"%"
        
    def get_pump_speed(self): # 0 off to 30 (max). Therefore normalize it to return %. manual says you need to send the speed as val+0x30 which is 48 in decimal.
        returnval = self.pump_status
        if returnval > 30:
            return 0
        return 100.0*returnval/30

    def start(self):
        a = self.query("S")
        return a
        
    def stop(self): # wait at current T until heat or cool received
        self.query("E")
        self.started = False
        return
        
    def hold(self): # probably on old linkam stages this needs to be sent at end of ramping up, otherwise the internal timer starts running and moves on with its own program
        self.query("O")
        self.started = False
        return
        
    def heat(self):
        a = self.query("H")
        return a
       
    def cool(self):
        self.query("C")
        return
       
    def set_manual_mode(self):
        if not self.pump_in_manual_mode:
            self.query("Pm0")
        self.pump_in_manual_mode = True
        return
        
    def set_pump_speed(self,val): # 0 to 30. manual says you need to send the speed as val+0x30 which is 48 in decimal. But PN is maximum speed? WTF?
        if self.pump_in_manual_mode:
            self.query("P"+str(val))
        return
       
    def set_auto_mode(self): # for compatibility with Eurotherm controllers
        return
        
    def set_pump_auto_mode(self): # Set automatic mode, where the pump speed is controlled by the T95 unit
        self.query("Pa0")
        self.pump_in_manual_mode = False
        return
        
    def get_error(self):
        """Return the error status"""
        returnval = self.error
        if returnval == 0:
            return self.error_info[5]
        elif returnval == 1:
            return self.error_info[0]
        elif returnval == 2:
            return self.error_info[1]
        elif returnval == 4:
            return self.error_info[2]
        elif returnval == 8:
            return self.error_info[3]
        elif returnval == 32:
            return self.error_info[4]
        return
        
    def get_target_setpoint_current_segment(self):
        return
        
    def get_ramp_rate(self):
        return self.current_ramp_rate
        
    def set_ramp_rate(self,value):
        self.set_setpoint_rate(value)
        return
    
    def is_manual_mode(self):
        return
    
    def set_sp1(self, value):
        # Args: value (uint16): Setpoint (most often in degrees)
        self.query("L1"+str(int(value*10.0)))
        print "Just set set-point to ",value," at ",time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        if not self.started:
            self.start()
            self.started = True
        return
        
    def set_op(self, value):
        return
    
    def get_setpoint_rate(self):
        return self.current_ramp_rate
    
    def set_setpoint_rate(self, value):
        # R1. Speed from 0 (off) to 30 (maximum)
        # Args: value (uint16): Setpoint change rate (most often in degrees/minute). 0==Off (means no rate limit)
        self.query("R1"+str(int(value*100.0)))
        self.current_ramp_rate = int(value)
        return
    
    def is_setpoint_rate_limited(self):
        return

    def disable_setpoint_rate(self): # for compatibility with Eurotherm controllers
        return
        
    def disable_programmer_mode(self): # for compatibility with Eurotherm controllers
        return
        
    def set_instrument_mode(self,mode): # for compatibility with Eurotherm controllers
        return
        
    def __del__(self):
        try:
            self.stop()
            self.set_sp1(self.room_temperature)
        except Exception:
            pass
        return

    def __exit__(self):
        try:
            self.stop()
            self.set_sp1(self.room_temperature)
        except Exception:
            pass
        return
        
# Little demo to show how the class can be used to acquire a simple ramping
if __name__ == "__main__":
   
    COM_port = "/dev/ttyS2"
    Temperature = 50 # °C
    Rate = 5 # °C/min
    linkam = linkam(COM_port)
    linkam.set_instrument_mode(0)
    linkam.select_setpoint(0) # means setpoint 1
    linkam.disable_setpoint_rate()
    linkam.set_sp1(Temperature)
    linkam.set_setpoint_rate(Rate)
    for i in range(100):
        T = linkam.get_pv()
        print "Current temperature is: ",T
        
