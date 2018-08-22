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

import minimalmodbus
import time
import sys

class eurotherm_2416( minimalmodbus.Instrument ):
    """Instrument class for Eurotherm 2416 process controller. 
    
    Communicates via Modbus RTU protocol (via RS232 or RS485), using the *MinimalModbus* Python module.    

    Args:
        * portname (str): port name
        * slaveaddress (int): slave address in the range 1 to 247

    Implemented with these function codes (in decimal):
        
    ==================  ====================
    Description         Modbus function code
    ==================  ====================
    Read registers      3
    Write registers     16
    ==================  ====================
        
    The wiring diagram of the controller to an RS-232 cable is as following:
    
    RS-232 pin 2 == HF
    RS-232 pin 3 == HE
    RS-232 pin 5 == HD
    
    All other pins are left empty

    """
    
    def __init__(self, portname, slaveaddress=1):
        self.oven_name = str(portname)
        self.oven_constant = 0.000078 # default value
        if "/" not in portname: # means instead of a serial port name, a pseudoname has been used
            if portname.lower() == "concordia":
                portname = "/dev/ttyS0"
                self.oven_constant = 0.0000798095032075008 # calculated from exponential air-cooling curve
                self.oven_name = "concordia"
            elif portname.lower() == "invincible":
                portname = "/dev/ttyS0"
                self.oven_constant = 0.0000798095032075008 # calculated from exponential air-cooling curve
                self.oven_name = "invincible"
            else:
                self.oven_constant = 0
                self.oven_name = ""
                sys.exit("No furnace with the name: \""+str(portname)+"\" has been found. Is the controller really Eurotherm 2416? Don't you think it's a Eurotherm 3216? Either use a correct pseudoname or address the serial port directly (See manual)")
        minimalmodbus.Instrument.__init__(self, portname, slaveaddress=1)
        self.room_temperature = 23
        print "###########################################################################"
        print "       "+self.oven_name+" (with id: "+str(self.get_id())+")"
        print "###########################################################################"
    ## Process value
    
    def get_pv(self):
        """Return the process value (PV) for loop1."""
        try:
            a = self.read_register(1, 0)
        except IOError:
            return None # Error during communication, Return a integer value nevertheless to make the program not crash.
        return a
    
    def get_op(self):
        """Return the % output level. (For 2404 this can also be used to set the % output)"""
        return self.read_register(3, 0)
        
    def get_id(self):
        """Return the customer defined identification number"""
        return int(self.read_register(629, 0))
        
    def get_oven_constant(self):
        """Return the exponential coefficient of the air-cooling curve"""
        return float(self.oven_constant)
        
    def get_oven_name(self):
        """Return the name"""
        return self.oven_name

    def get_heater_current(self):
        """Return the heater current."""
        return self.read_register(80, 1)
        
    def get_program_status(self):
        """Return the StAt. PC"""
        a = int(self.read_register(23, 0))
        string = ""
        if a is 1:
           string="Reset"
        elif a is 2:
           string="Run"
        elif a is 4:
           string="Hold"
        elif a is 8:
           string="Holdback"
        elif a is 16:
           string="Complete"
        return string
        
    def get_current_program_running(self):
        """Return the PrG. PN as a number"""
        return self.read_register(22, 0) 
        
    def get_programmer_setpoint(self):
        """Return the PS."""
        return self.read_register(163, 0)

    def get_program_cycles_remaining(self):
        """Return the CL."""
        return self.read_register(59, 0)
        
    def turn_logic_outputs_off(self):
        """Return the z1."""
        Off = 0
        On = 1
        self.write_register(273, Off, 0)
        
    def turn_logic_outputs_on(self):
        """Return the z1."""
        Off = 0
        On = 1
        self.write_register(273, On, 0)
        
    def enable_autotune(self):
        """Return the AT."""
        Off = 0
        On = 1
        self.write_register(270, On, 0)
        
    def disable_autotune(self):
        """Return the AT."""
        Off = 0
        On = 1
        self.write_register(270, Off, 0)
        
    def enable_adaptive_tune(self):
        """Return the AT."""
        Off = 0
        On = 1
        self.write_register(271, On, 0)
        
    def disable_adaptive_tune(self):
        """Return the AT."""
        Off = 0
        On = 1
        self.write_register(271, Off, 0)
        
    def get_current_segment_number(self):
        """Return the SN."""
        return self.read_register(56, 0)
        
    def set_sensor_break_output_power(self):
        """Shuts everything down on sensor break"""
        Full = 2
        Off = 1
        self.write_register(40, Off, 0)
        
    def select_setpoint(self,setpoint):
        """Which setpoint int 0 to 15"""
        self.write_register(15, setpoint, 0)
        
    def get_current_segment_type(self):
        """Return the CS."""
        a = int(self.read_register(29, 0))
        string = ""
        if a is 0:
           string="End"
        elif a is 1:
           string="Ramp (Rate)"
        elif a is 2:
           string="Ramp (time to target)"
        elif a is 3:
           string="Dwell"
        elif a is 4:
           string="Step"
        elif a is 5:
           string="Call"
        return string
        
    def get_segment_time_remaining(self):
        """Return the PM in minutes."""
        return self.read_register(63, 1)
        
    def get_target_setpoint_current_segment(self):
        """Return the CT."""
        return self.read_register(160, 0)
        
    def get_ramp_rate(self):
        """Return the CR."""
        return self.read_register(161, 1)
        
    def set_ramp_rate(self,value):
        """Set the CR."""
        return self.write_register(161, value, 1)
        
    def get_program_time_remaining(self):
        """Return the TP."""
        return self.read_register(58, 1)
        
    ## Auto/manual mode
    
    def is_manual_mode(self):
        """Return True if is in manual mode."""
        return self.read_register(273, 1) > 0
    
    ## Setpoint
    
    def get_target_setpoint(self):
        """Return the Target setpoint (if in manual mode). SL"""
        return self.read_register(2, 0)
    
    def get_working_setpoint(self): # Readonly
        """readonly. Return the (working) setpoint (SP)."""
        return self.read_register(5, 0)
    
    def set_sp1(self, value):
        """Set the SP1.
        Note that this is not necessarily the working setpoint.
        Args:
            value (float): Setpoint (most often in degrees)
        """
        print "Just set set-point to ",value," at ",time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        self.write_register(24, value, 0)
        
        
    def set_sp2(self, value):
        """Set the SP2.
        Note that this is not necessarily the working setpoint.
        Args:
            value (float): Setpoint (most often in degrees)
        """
        self.write_register(25, value, 0)
        
    def set_sp3(self, value):
        """Set the SP3.
        Note that this is not necessarily the working setpoint.
        Args:
            value (float): Setpoint (most often in degrees)
        """
        self.write_register(164, value, 0)
        
    def set_op_pre3(self, value):
        """Set the % control output. Only for 2400 pre S/W 3.00
        Args:
            value (int): xxx%
        """
        self.write_register(85, value, 0)
    
    #def set_op(self, value):
        #"""Set the % control output.
        #Args:
            #value (int): xxx%
        #"""
        #self.write_register(3, value, 0)
        
    
    ## Setpoint rate
    
    def get_setpoint_rate(self):
        """Return the setpoint (SP) change rate. RR. degree/min. 0==Off (means no rate limit)"""
        return self.read_register(35, 0)   
    
    def set_setpoint_rate(self, value):
        """Set the setpoint (SP) change rate. RR.
        Args:
            value (int): Setpoint change rate (most often in degrees/minute). 0==Off (means no rate limit)
        """
        self.write_register(35, value, 0)  
    
    def is_setpoint_rate_limited(self):
        """Return True if setpoint (SP) rate is disabled. RD"""
        return self.read_register(78, 1) > 0

    def disable_setpoint_rate(self):
        """Disable the setpoint (SP) change rate. RD"""
        VALUE = 0
        self.write_register(78, VALUE, 0) 
        
    def set_manual_mode(self):
        """Auto-man select. mA"""
        Auto = 0
        Manual = 1
        self.write_register(273, Manual, 0)
        
    def set_auto_mode(self):
        """Auto-man select. mA"""
        Auto = 0
        Manual = 1
        self.write_register(273, Auto, 0)
        
    def enable_setpoint_rate(self):
        """Set disable=false for the setpoint (SP) change rate. RD
        Note that also the SP rate value must be properly set for the SP rate to work.
        """
        VALUE = 1
        self.write_register(78, VALUE, 0)
        
    def disable_programmer_mode(self):
        """needed that the instrument does use a ramp rate. Added for compatibility with 3216"""
        No = 0
        Programmer = 10
        return
        #self.write_register(320, No, 0)
        
    def set_instrument_mode(self, value):
        """needed that the instrument does use a ramp rate. Added for compatibility with 3216"""
        return
        
    def __del__(self):
        try:
            self.set_sp1(self.room_temperature)
        except Exception:
            pass
        return

    def __exit__(self):
        try:
            self.set_sp1(self.room_temperature)
        except Exception:
            pass
        return
        
    def goto_temperature_and_wait(self,final_temperature,ramp_rate,hold_time=60):
        temperature_now = self.get_pv()
        temperature_difference = final_temperature-temperature_now
        if temperature_difference <= 0 or ramp_rate == 0:
            time.sleep(hold_time*60)
            return
        time_needed = temperature_difference/ramp_rate
        self.set_setpoint_rate(ramp_rate)
        self.set_sp1(final_temperature)
        self.disable_setpoint_rate()
        time.sleep(60*time_needed+hold_time*60)
        return
        
    def goto_temperature(self,final_temperature,ramp_rate):
        self.set_setpoint_rate(ramp_rate)
        self.set_sp1(final_temperature)
        self.disable_setpoint_rate()
        return
