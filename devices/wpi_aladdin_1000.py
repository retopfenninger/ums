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

class wpi_aladdin_1000():
    """Instrument class for WPI Al-1000 syringe controller. 
    
    Communicates via RS232 over RJ-11 with a WPI Al-1000 syringe pump

    Args:
        * portname (str): port name
        * slaveaddress (int): slave address. default 0



    Wiring diagram::
    
    This is the RJ-11 plug at the pump:
          ____ 
    ______|   |____
    |              |
    |              |
    |__|__|__|__|__|
       A  B  C  D
       
    If you have a RS-232 cable, wire it the following way:
    
    A = empty
    B = pin 3
    C = pin 5
    D = pin 2
    
    BASIC command syntax to pump: <command data> <CR>
    BASIC response: <STX> <response data> <ETX>
    
       
    """    
    def __init__(self, portname, slaveaddress=0):
        self.debug = True
        self.slaveaddress = slaveaddress
        self.pump_name = str(portname)
        self.CR = '\x0D'
        self.STX = '\x02'
        self.ETX = '\x03'
        if "/" not in portname: # means instead of a serial port name, a pseudoname has been used
            if portname.lower() == "spraychamber": # spray computer on first serial port (over USB)
                portname = "/dev/ttyUSB0"
                self.pump_name = "spraychamber"
            else:
                self.pump_name = "unknown pump"
                sys.exit("No pump with the name: \""+str(portname)+"\" has been found. Is the controller connected and turned on? Either use a correct pseudoname or address the serial port directly (See manual)")
        self.interface = serial.Serial(port=portname,baudrate=9600,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS,xonxoff=False) # TODO enable local echo (half-duplex)
        self.interface.isOpen()
        self.pump_rate = 0.0 #self.get_rate()
        print "###########################################################################"
        print "       "+self.pump_name+" (with id: )"
        print "###########################################################################"
    
    ## Process value
    def write(self,message):
        self.interface.write(str(self.slaveaddress)+" "+message+self.CR)
        if self.debug:
            print "Just wrote:",str(self.slaveaddress)+" "+message
        return
     
    def read(self):
        buf = []
        trials = 10
            #if ser.inWaiting(): # Is there data waiting in the input buffer?
        while True and trials:
            val = self.interface.read(1)
            if self.ETX in val: # EOL detected
                break
            buf.append(val)
            trials -= 1
        if self.debug:
            print "Just got:",str(buf)
        return buf
     
    def query(self,m):
        self.write(m)
        time.sleep(1)
        return self.read()
     
    def float_number_formatter(self,value): # According to manual of pump
        value = float(value)
        if value >= 999.95:
            return float(str(float("{:.4g}".format(value)))[:4])
        elif value < 1.0:
            return float("{:.3f}".format(value))
        return float("{:.4g}".format(value)) # loating point number. maximum of 4 digits plus 1 decimal point. maximum of 3 digits to the right of the decimal point.
     
    #def get_pv(self):
        #"""Return the process value (PV) for loop1."""
        #try:
            #a = self.read_register(1, 1, signed=True)
        #except IOError:
            #return None # Error during communication, Return a integer value nevertheless to make the program not crash.
        #return a
    
    def set_infusing_mode(self):
        """pump mode"""
        return self.query("I")
     
    def set_withdrawing_mode(self):
        """pump mode"""
        return self.query("W")
     
    def stop(self):
        """pump mode"""
        return self.query("S")
     
    def pause(self):
        """pump mode"""
        return self.query("P")
     
    def pause_phase(self):
        """pump mode"""
        return self.query("T")
     
    def set_trigger_mode(self):
        """pump mode"""
        return self.query("U")
     
    def set_pump_address(self,a):
        """pump mode"""
        new_address = int(a)
        if new_address < 100 and new_address >= 0:
            return self.query("ADR "+str(new_address))
        else:
            print "New set address of pump out of range [0-100]! You gave this number:",str(a)
            return
         
    def get_pump_address(self):
        """pump address"""
        return self.query("* ADR")
     
    def set_syringe_diameter(self,s): # TODO
        """syringe inside diameter. Also sets the unit for 'volume to be dispersed' and 'Volume dispersed' """
        val = self.float_number_formatter(s)
        if float(s) < 100 and float(s) >= 0:
            return self.query("DIA "+str(val))
        else:
            print "New syringe inner diameter set is out of range [0-100]! You gave this number:",str(s)
            return
         
    def get_syringe_diameter(self):
        """syringe inside diameter"""
        return self.query("DIA")
     
    def set_phase_number(self,s): # TODO
        """Program phase """
        val = s
        if val < 100 and val >= 0:
            return self.query("PHN "+str(val))
        else:
            print "Program phase set is out of range [0-100]! You gave this number:",str(s)
            return
         
    def get_phase_number(self):
        """Program phase """
        return self.query("PHN")
         
    def get_phase_function(self): # internal use only
        """Program phase """
        return self.query("FUN")
     
    def set_rate(self,s):
        """Pump rate """
        self.stop() # needed for programming
        self.query("FUN RAT") # switch to RAT mode
        val = self.float_number_formatter(s)
        if float(s) < xxx and float(s) >= xxx:
            return self.query("RAT "+str(val))
        else:
            print "Program set_rate is out of range [xxx]! You gave this number:",str(s)
            return
         
    def get_rate(self):
        """Program phase """
        self.stop() # needed for programming
        self.query("FUN RAT") # switch to RAT mode
        return self.query("RAT") 
    
    def set_unit_volume(self,volume):
        """set volume"""
        self.stop() # needed for programming
        self.query("FUN RAT") # switch to RAT mode
        if volume is "uL":
            self.write("UL")
        elif volume is "mL":
            self.write("mL")
        else:
            print "Wrong input for set_unit_volume! You can only use either 'uL' or 'mL' as input to this function!"
        return 
     
    def close(self):
        """shutdown procedure"""
        self.stop() # stop the pumping
        self.interface.close() # SErial port down
        return 
        

        
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
        

# Little demo to show how the class can be used to set a few values
if __name__ == "__main__":
   
    serial_port_name = "/dev/ttyUSB0"
    address = 11 # default address
    syringe_pump = wpi_aladdin_1000(serial_port_name,address)
    #syringe_pump.set_unit_volume("mL")
    #syringe_pump.set_unit_time("hr")
    #syringe_pump.set_syringe_diameter(7.3) # mm
    #syringe_pump.set_flow(42.42) # ml/minute
    syringe_pump.set_infusing_mode() # pump and not suck
    syringe_pump.start()
    print "The pump is now pumping..."
    time.sleep(10) # wait 2 sec for the device to become ready
    syringe_pump.stop()
    print "The pump just stopped pumping"
    syringe_pump.close()
