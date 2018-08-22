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
import warnings

class voegtlin_gsc( minimalmodbus.Instrument ):
   
    """Instrument class for Vögtlin red-y GSC mass flow controller
    f32 == 4byte
    s8 == 8byte
    s50 == 50byte
    u8 == 8bit, 1byte
    u16 == 16bit, 2byte
    u32 == 32bit, 4byte
    
    4ms break after each command @9600 baudrate
    
    Communicates via Modbus RTU protocol (via RS232 or RS485), using the *MinimalModbus* Python module.    

    write_register(self, registeraddress, value, numberOfDecimals=0, functioncode=16, signed=False)
    read_register(self, registeraddress, numberOfDecimals=0, functioncode=3, signed=False) uint 16 and int16
    read_float(self, registeraddress, functioncode=3, numberOfRegisters=2)
    write_float(self, registeraddress, value, numberOfRegisters=2)
    read_string(self, registeraddress, numberOfRegisters=16, functioncode=3)
    write_string(self, registeraddress, textstring, numberOfRegisters=16)
    
    !! Long integers (32 bits = 4 bytes) are stored in two consecutive 16-bit registers in the slave
    read_long(self, registeraddress, functioncode=3, signed=False)
    write_long(self, registeraddress, value, signed=False)
    
    Args:
        * portname (str): port name
        * slaveaddress (int): slave address in the range 1 to 247

    Implemented with these function codes (in decimal):
        
    ==================  ====================
    Description         Modbus function code
    ==================  ====================
    Read registers      3
    Write one register  6
    Write registers     16
    ==================  ====================

    """
    
    def __init__(self, portname, slaveaddresses, voegtlin_debug=False, stop_bits=2):
        if type(slaveaddresses)==float or type(slaveaddresses)==int:
            slaveaddresses = [int(slaveaddresses)] # make an array
        minimalmodbus.Instrument.__init__(self, portname, slaveaddresses[0], stop_bits=2) # connect to the first one
        # sort out all addresses where no device is present
        self.mfc_addresses = []
        self.voegtlin_debug = voegtlin_debug
        for test_address in slaveaddresses:
            if self.set_flowmeter_address(test_address):
                self.mfc_addresses.append(test_address)
        return
    
    def get_flowmeter_address(self):
        return self.address
        
    def get_all_flowmeter_addresses(self):
        result_array = []
        active_mfc = self.address
        for flowmeter_address in self.mfc_addresses:
            max_flow = ""
            v = self.get_calibrated_end_value(flowmeter_address)[0]
            if v != 0.0:
                max_flow = " "+str(int(v))
            result_array.append([flowmeter_address,self.get_medium_info(flowmeter_address)+max_flow])
        self.set_flowmeter_address(active_mfc) # set back to the address of the mfc-in-charge before calling this function
        return result_array
        
    def set_flowmeter_address(self,value):
        if value in self.mfc_addresses:
            self.address = value
            return True
        else:
            # Now check if we can find a flowmeter at the new modbus address
            old_address = self.address
            self.address = value
            if self.check_if_device_available():
                return True
            self.address = old_address
            return False
        
    def check_if_device_available(self):
        available = True
        try:
            self.get_id()
            if self.voegtlin_debug:
                print "Device found at modbus address:",self.get_flowmeter_address()
                self.get_condensed_system_variables()
        except IOError:
            if self.voegtlin_debug:
                print "No device found at modbus address:",self.get_flowmeter_address()
            available = False
            pass
        return available
    
    def get_pv(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        try:
            a = self.read_float(0) # f32 r 2reg
        except IOError:
            return None # Error during communication, Return a integer value nevertheless to make the program not crash.
        unit_factor = self.get_unit_conversion_factor()
        return a*unit_factor
        
    def get_id(self,which=None): # returns the serial number
        if which is not None:
            self.set_flowmeter_address(which)
        return int(self.read_long(30)) # u32 r 2reg

    def get_flow(self,which=None): # same as get_pv
        return self.get_pv(which)
        
    def get_gas_temperature(self,which=None): # in deg C
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(2) # f32 r 2reg
        
    def get_sp(self,which=None): # value is in milli-unit
        if which is not None:
            self.set_flowmeter_address(which)
        a = self.read_float(6) # f32 rw 2reg
        unit_factor = self.get_unit_conversion_factor()
        return a*unit_factor
        
    def set_sp(self,value,which=None): # value is in unit [mln/min]
        if which is not None:
            self.set_flowmeter_address(which)
        # Now make sure that the flow is not going to be set bigger than the maximum opening which is possible. Maximum opening is only visible on newer instruments
        unit_factor = self.get_unit_conversion_factor()
        max_val = self.get_calibrated_end_value()[0]*unit_factor
        if max_val != 0.0 and value > max_val:
            print "ERROR: The setpoint of the Mass-flow-controller with serial number:",self.get_id(),"cannot be set to:",value," which is higher than its maximum of:",max_val
            self.write_float(6, max_val/unit_factor) # f32 rw 2reg
            print "The value has been set to the maximum instead"
        else:
            self.write_float(6, value/unit_factor) # f32 rw 2reg
        return
        
    def get_analog_input_value(self,which=None): # mA or V depending on setting
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(8) # f32 r 2reg
        
    def get_valve_position(self,which=None): # in %
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(10) # f32 rw 2reg
        
    def set_valve_position(self,value,which=None): # between 0-100 %
        if which is not None:
            self.set_flowmeter_address(which)
        if value < 0.0 or value > 100.0:
            print "ERROR: The valve position setvalue is out of allowed range (1-100%). You wanted:",value
        else:
            self.write_float(10, value) # f32 rw 2reg, mode10 needs to be active
        return
        
    def get_alarm_status(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        a = int(self.read_register(12, 0)) # 1reg
        result = "no_alarm"
        if a is 0:
            result = "negative_flow_measured"
        elif a is 1:
            result = "negative_flow_measured_higher_than_threshold"
        elif a is 15:
            result = "hardware_error"
        return result
        
    def get_hardware_status(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        a = int(self.read_register(13, 0)) # u16 bit 15...0 1reg
        result = "no_alarm"
        if a is 0:
            result = "power_up_alarm"
        elif a is 1:
            result = "analog_sp_out_of_range"
        elif a is 2:
            result = "leakage_detected"
        elif a is 3:
            result = "fully_open_but_no_gasflow"
        elif a is 4:
            result = "valve_doesnt_react"
        elif a is 5:
            result = "sensor_communication_error"
        elif a is 7:
            result = "EEPROM_error"
        elif a is 10:
            result = "analog_input_current_too_high"
        elif a is 11:
            result = "serialnumber_wrong_all_set_to_zero"
        return result
        
    def get_mode(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        value = self.read_register(14, 0) # u16 rw 1reg
        if value is 1:
            return "digital"
        elif value is 0:
            return "automatic"
        elif value is 2:
            return "analog" # default
        elif value is 10: # the valve postion is controlled manually
            return "mode10"
        elif value is 20:
            return "sp0"
        elif value is 21:
            return "sp100"
        elif value is 22:
            return "valve_closed"
        elif value is 23:
            return "valve_open"
        return None
        
    def set_mode(self,value="digital",which=None): # u16 rw 1reg
        if which is not None:
            self.set_flowmeter_address(which)
        if value is "digital":
            self.write_register(14, 1, 0)
        elif value is "automatic":
            self.write_register(14, 0, 0)
        elif value is "analog":
            self.write_register(14, 2, 0) # default
        elif value is "mode10": # the valve postion is controlled manually
            self.write_register(14, 10, 0)
        elif value is "sp0":
            self.write_register(14, 20, 0)
        elif value is "sp100":
            self.write_register(14, 21, 0)
        elif value is "valve_closed":
            self.write_register(14, 22, 0)
        elif value is "valve_open":
            self.write_register(14, 23, 0)
        else:
            print "ERROR: Wrong argument supplied to function set_mode(). You entered:",value
        return
        
    def get_ramp_mode(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 150000:
            return None
        else: # u16 rw 1reg 0==deactivated. otherwise use a value of 200-10000 [ms]
            return self.read_register(15, 0) # in ms till sp should be reached
            
    def set_ramp_mode(self,value,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 150000:
            return None
        elif (value < 200.0 or value > 10000.0) and value != 0:
            print "ERROR: The set_ramp_mode() setvalue is out of allowed range (200-10000 [ms] or 0). You wanted:",value
        else:
            self.write_register(15, value, 0) # in ms till sp should be reached
        return 
        
    def get_modbus_address(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_register(19, 0) # u16 (but 2 u8) rw 1reg
        
    def set_modbus_address(self,value,which=None): # 1-247
        if which is not None:
            self.set_flowmeter_address(which)
        if value < 1 or value > 247:
            print "ERROR: The argument supplied to set_modbus_address() is out of allowed range (1-247). You wanted:",value
        else:
            self.write_register(19, value, 0) # u16 (but 2 u8) rw 1reg
        return 
        
    def get_medium_info(self,which=None): # s8 r 4reg TODO shorter?
        if which is not None:
            self.set_flowmeter_address(which)
        a = self.read_string(26, numberOfRegisters=2)
        b = self.read_string(24642, numberOfRegisters=2)
        if a == b or all(x=='\x00' for x in b): # both say the same or all elements from b are empty
            return a.replace('\x00', '')
        return a.replace('\x00', '') + " / " + b.replace('\x00', '')
        
    def get_medium_info_long(self,which=None): # TODO: shorter? long on newer models? FileVer? FileVersionbasic_stringt from 160000?
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000 and self.get_serial_number() > 130000:
            print "ERROR: The function get_medium_info_long() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_string(24610, numberOfRegisters=4) # s50 r 25reg
        
    def get_serial_number(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        return self.get_id()
        
    def get_hardware_version(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_register(32, 0) # u16 r 1reg
        
    def get_software_version(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_register(33, 0) # u16 r 1reg
        
    def get_software_in_eeprom(self,which=None): # 0. >0 means will be safed in eeprom
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_register(34, 0) # u16 rw 1reg
        
    def set_software_in_eeprom(self,value=0,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_register(34, value, 0)
        return
        
    def get_typecode_1(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_string(35, numberOfRegisters=4) # s8 r 4reg
        
    def set_analog_output(self,value,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_float(40, value) # f32 rw 2reg
        return
        
    def get_analog_output(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        self.read_float(40) # f32 rw 2reg
        return
        
    def softreset(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        value = 1 # any value works
        self.write_register(52, value, 0) # u16 w 1reg
        return
        
    def set_pid_select(self,value="medium_fast_response",which=None): # u16 rw 1reg
        if which is not None:
            self.set_flowmeter_address(which)
        if value is "user1":
            self.write_register(53, 0, 0) # default
        elif value is "user2":
            self.write_register(53, 1, 0)
        elif value is "fast_response":
            self.write_register(53, 2, 0) 
        elif value is "medium_fast_response":
            self.write_register(53, 3, 0)
        elif value is "slow_response":
            self.write_register(53, 4, 0)
        else:
            print "ERROR: Wrong argument supplied to function set_pid_select(). You entered:",value
        return
        
    def get_pid_select(self,which=None): # u16 rw 1reg
        if which is not None:
            self.set_flowmeter_address(which)
        a = None
        value = self.read_register(53, 0)
        if value is 0:
            a = "user1"
        elif value is 1:
            a = "user2"
        elif value is 2:
            a = "fast_response"
        elif value is 3:
            a = "medium_fast_response"
        elif value is 4:
            a = "slow_response"
        return a
        
    def set_change_from_flow_to_pressure_control(self,value="digital",which=None): # u16 rw 1reg TODO needs newer model? doesnt work on 124663
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 130000:
            print "ERROR: The function set_change_from_flow_to_pressure_control() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        if value is "automatic":
            self.write_register(56, 0, 0) # not recommended
        elif value is "digital":
            self.write_register(56, 1, 0)
        elif value is "analog":
            self.write_register(56, 3, 0) 
        elif value is "pressure_control": # always digital
            self.write_register(56, 5, 0)
        elif value is "after_pressure_control": # always digital
            self.write_register(56, 6, 0)
        else:
            print "ERROR: Wrong argument supplied to function set_change_from_flow_to_pressure_control(). You entered:",value
        return
        
    def get_change_from_flow_to_pressure_control(self,which=None): # u16 rw 1reg # TODO needs newer model? doesnt work on 124663
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 130000:
            print "ERROR: The function get_change_from_flow_to_pressure_control() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        a = None
        value = self.read_register(56, 0)
        if value is 0:
            a = "automatic"  # not recommended
        elif value is 1:
            a = "digital"
        elif value is 3:
            a = "analog"
        elif value is 5: # always digital
            a = "pressure_control"
        elif value is 6: # always digital
            a = "after_pressure_control"
        return a
        
    def get_typecode_2(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_string(4100, numberOfRegisters=4) # s8 r 4reg
        
    def set_power_up_alarm(self,value,which=None): # 0==Off, 1== On
        if which is not None:
            self.set_flowmeter_address(which)
        if value != 1 and value != 0:
            print "ERROR: The argument supplied to set_power_up_alarm() is out of allowed range (1 or 0). You wanted:",value
        else:
            self.write_register(16448, value, 0) # u16 rw 1reg
        return
        
    def get_power_up_alarm(self,which=None): # 0==Off, 1== On
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_register(16448, 0) # u16 rw 1reg
        
    def set_power_up_flow(self,value,which=None): # between 0 and endval [milli-unit]
        if which is not None:
            self.set_flowmeter_address(which)
        unit_factor = self.get_unit_conversion_factor()
        endval = self.get_calibrated_end_value()[0]*unit_factor
        if value < 0 or (value > endval and endval != 0.0):
            print "ERROR: The argument supplied to set_power_up_flow() is out of allowed range (0 to endval). You wanted:",value
        else:
            self.write_float(16449, value) # f32 rw 2reg
        return
        
    def get_power_up_flow(self,which=None): # between 0 and endval [milli-unit]
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(16449) # f32 rw 2reg
        
    def set_zeropoint_suppression(self,value,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_float(16460, value) # or | 24867 und 24868 mit f32 default 0 rw
        return
        
    def get_zeropoint_suppression(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(16460)
        
    def reset_hardware_error(self,value,which=None): # 1 to 15 specifying which error to delete
        if which is not None:
            self.set_flowmeter_address(which)
        if value < 1 or value > 15:
            print "ERROR: The argument supplied to reset_hardware_error() is out of allowed range (1 to 15). You wanted:",value
        else:
            self.write_register(16463, value, 0) # u16 rw 1reg
        return
        
    def set_sp_memory_location(self,value=0,which=None): # 0== no automatic saving 1== EEPROM save
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_register(16464, value, 0) # u16 rw 1reg
        return
        
    def get_sp_memory_location(self,which=None): # 0== no automatic saving 1== EEPROM save
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_register(16464, 0) # u16 rw 1reg
        
    def set_backflow_detection_threshold(self,value,which=None): # not recommended
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_float(16466, value) # f32 rw 2reg
        return
        
    def get_backflow_detection_threshold(self,which=None): # not recommended
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(16466) # f32 rw 2reg
        
    def set_analog_output_signal(self,value,which=None): # 0== 0-20 mA or 0-5V | 1==2== 4-20mA or 1-5V | 3==0-20mA or 0-10V | 4== 4-20mA or 2-10V
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_register(16516, value, 0) # u16 rw 1reg
        return
        
    def get_analog_output_signal(self,which=None): # 0== 0-20 mA or 0-5V | 1==2== 4-20mA or 1-5V | 3==0-20mA or 0-10V | 4== 4-20mA or 2-10V
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_register(16516, 0) # u16 rw 1reg
        
    def set_analog_input_signal(self,value,which=None): # 0== 0-20 mA or 0-5V | 1==2== 4-20mA or 1-5V | 3==0-20mA or 0-10V | 4== 4-20mA or 2-10V
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_register(16517, value, 0) # u16 rw 1reg
        return
        
    def get_analog_input_signal(self,which=None): # 0== 0-20 mA or 0-5V | 1==2== 4-20mA or 1-5V | 3==0-20mA or 0-10V | 4== 4-20mA or 2-10V
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_register(16517, 0) # u16 rw 1reg
        
    def set_hardware_selftest_delay(self,value,which=None): # default 10s, can be 0 to 600s
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_register(16519, value, 0) # u16 rw 1reg
        return
        
    def get_hardware_selftest_delay(self,which=None): # default 10s, can be 0 to 600s
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_register(16519, 0) # u16 rw 1reg
        
    def set_lut(self,value,which=None): # type of gas used. default 2, can store 11 settings
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function set_lut() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        self.write_register(16697, value, 0) # u8 rw 1reg
        return
        
    def get_lut(self,which=None): # TODO SN 103684 unknown # type of gas used. default 2, can store 11 settings
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function get_lut() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_register(16697, 0) # u8 rw 1reg
        
    def get_identifier(self,which=None): # TODO gives strange characters on > 150000
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 130000:
            print "ERROR: The function get_identifier() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_string(20480, numberOfRegisters=25) # s50 rw 1reg?
        
    def set_identifier(self, textstring,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 130000:
            print "ERROR: The function get_identifier() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.write_string(20480, textstring, numberOfRegisters=25) # s50 rw 1reg?
        
    def get_baudrate(self,which=None): # TODO SN 103684 unknown
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function get_baudrate() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        a = int(self.read_register(20992, 0)) # u16 rw 1reg
        result = None
        if a is 0:
            result = 300
        elif a is 1:
            result = 600
        elif a is 2:
            result = 1200
        elif a is 3:
            result = 2400
        elif a is 4:
            result = 4800
        elif a is 5:
            result = 9600
        elif a is 6:
            result = 19200
        elif a is 7:
            result = 38400
        elif a is 8:
            result = 57600
        return result
        
    def set_baudrate(self, value,which=None): # u16 rw 1reg
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function set_baudrate() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        if value is 300:
            self.write_register(20992, 0, 0)
        elif value is 600:
            self.write_register(20992, 1, 0)
        elif value is 1200:
            self.write_register(20992, 2, 0)
        elif value is 2400:
            self.write_register(20992, 3, 0)
        elif value is 4800:
            self.write_register(20992, 4, 0)
        elif value is 9600:
            self.write_register(20992, 5, 0)
        elif value is 19200:
            self.write_register(20992, 6, 0)
        elif value is 38400:
            self.write_register(20992, 7, 0)
        elif value is 57600:
            self.write_register(20992, 8, 0)
        else:
            return False
        return True
        
    def set_alarm_led(self,value,which=None): # TODO needs newer model? doesnt work on 124663, 153210
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 160000:
            print "ERROR: The function set_alarm_led() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        self.write_register(20996, value, 0) # u16 rw 1reg
        return
        
    def get_alarm_led(self,which=None): # TODO needs newer model? doesnt work on 124663, 153210
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 160000:
            print "ERROR: The function get_alarm_led() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_register(20996, 0) # u16 rw 1reg
        
    def set_analog_output_mode(self,value,which=None): # 0== current output active 1== voltage output active
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function set_analog_output_mode() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        self.write_register(21760, value, 0) # u16 rw 1reg
        return
        
    def get_analog_output_mode(self,which=None): # TODO SN 103684 unknown # 0== current output active 1== voltage output active
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function get_analog_output_mode() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_register(21760, 0) # u16 rw 1reg
        
    def set_analog_input_mode(self,value,which=None): # 0== current input active 1== voltage input active
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function set_analog_input_mode() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        self.write_register(21764, value, 0) # u16 rw 1reg
        return
        
    def get_analog_input_mode(self,which=None): # TODO SN 103684 unknown # 0== current input active 1== voltage input active
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function get_analog_input_mode() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_register(21764, 0) # u16 rw 1reg
        
    def set_analog_input_current_lower_threshold(self,value,which=None): # mA
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_float(21765, value) # f32 rw 1reg
        return
        
    def get_analog_input_current_lower_threshold(self,which=None): # mA
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(21765) # f32 rw 1reg
        
    def set_analog_input_current_upper_threshold(self,value,which=None): # mA. < 20 mA
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_float(21767, value) # f32 rw 1reg
        return
        
    def get_analog_input_current_upper_threshold(self,which=None): # mA. < 20 mA
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(21767) # f32 rw 1reg
        
    def set_analog_input_lower_threshold(self,value,which=None): # V
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_float(21769, value) # f32 rw 1reg
        return
        
    def get_analog_input_lower_threshold(self,which=None): # V
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(21769) # f32 rw 1reg
        
    def set_analog_input_upper_threshold(self,value,which=None): # V. < 10 V
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_float(21771, value) # f32 rw 1reg
        return
        
    def get_analog_input_upper_threshold(self,which=None): # V. < 10 V
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(21771) # f32 rw 1reg
        
    def set_analog_output_current_lower_threshold(self,value,which=None): # mA
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_float(21773, value) # f32 rw 1reg
        return
        
    def get_analog_output_current_lower_threshold(self,which=None): # mA
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(21773) # f32 rw 1reg
        
    def set_analog_output_current_upper_threshold(self,value,which=None): # mA. < 20 mA
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_float(21775, value) # f32 rw 1reg
        return
        
    def get_analog_output_current_upper_threshold(self,which=None): # mA. < 20 mA
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(21775) # f32 rw 1reg
        
    def set_analog_output_lower_threshold(self,value,which=None): # V
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_float(21777, value) # f32 rw 1reg
        return
        
    def get_analog_output_lower_threshold(self,which=None): # V
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(21777) # f32 rw 1reg
        
    def set_analog_output_upper_threshold(self,value,which=None): # V. < 10 V
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_float(21779, value) # f32 rw 1reg
        return
        
    def get_analog_output_upper_threshold(self,which=None): # V. < 10 V
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(21779) # f32 rw 1reg
        
    def get_pid_access(self,which=None): # TODO SN 103684 unknown # 0 to 4
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function get_pid_access() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_register(24567, 0) # u16 rw 1reg
        
    def set_pid_access(self, value,which=None): # 0 to 4
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function set_pid_access() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        self.write_register(24567, value, 0) # u16 rw 1reg
        return
        
    def get_lut_access(self,which=None): # TODO SN 103684 unknown # 2 to 11
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function get_lut_access() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_register(24575, 0) #u8 rw 1reg
        
    def set_lut_access(self, value,which=None): # 2 to 11
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function set_lut_access() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        self.write_register(24575, value, 0) #u8 rw 1reg
        return
        
    def get_lut_id(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_long(24576) # u32 r 2reg
        
    def get_calibrated_end_value(self,which=None): # always return the value in milli-unit
        if which is not None:
            self.set_flowmeter_address(which)
        flow = self.read_float(24608) # f32 r 2reg
        # What unit is used?
        unit = self.get_measurement_unit(which)
        return [flow,unit]

        
    def get_unit_conversion_factor(self,which=None): # always return the value for milli-unit: sccm
        unit = self.get_measurement_unit(which)
        # The following units are available: lb/min, lb/h, sscm, mln/min, ln/min, ln/h, mls/min, ls/min, ls/h, m3n/h,
        # m3s/h, kg/min, kg/h, g/min, g/h, mln/h, mls/h, NLPM, SLPM, NLPH, SLPH, SCFM, SCFH 
        if "sccm" not in unit  and "mln/min" not in unit and "ln/min" not in unit and unit is not "" and not all(i == '\x00' for i in unit):
            warnings.warn("Please select 'sccm' or 'mln/min' / 'ln/min' as the unit of the attached flowmeters in the redy-smart configuration tool. Everything else can result in unprecise results.")
        if "mln/min" in unit or "sccm" in unit or "mls/min" in unit or unit is "" or all(i == '\x00' for i in unit): # if its milli but not cubicmeter, The last one applies to super old MFCs with no unit settable
            return 1.0
        elif "m3s/h" in unit or "m3n/h" in unit:
            return 0.000060
        elif "lb/min" in unit:
            return 0.0022
        elif "lb/h" in unit:
            return 0.0022*60
        elif "ln/min" in unit or "ls/min" in unit or "NLPM" in unit or "SLPM" in unit:
            return 1000.0
        elif "mln/h" in unit or "mls/h" in unit:
            return 60.0
        elif "ln/h" in unit or "ls/h" in unit or "NLPH" in unit or "SLPH" in unit:
            return 1000.0*60
        elif "kg/min" in unit or "kg/h" in unit or "g/min" in unit or "g/h" in unit:
            raise ValueError("Please select 'sccm' or 'mln/min' / 'ln/min' as the unit of the attached flowmeters in the redy-smart configuration tool. Everything else can result in unprecise results.")
        elif "SCFM" in unit:
            return 0.0000353146662127
        elif "SCFH" in unit:
            return 0.0000353146662127*60
        raise ValueError("Unknown unit ",unit," is set as flow unit in the redy-smart configuration tool. Driver does not know how to convert to sccm")
        
    def get_measurement_unit(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_string(24646, numberOfRegisters=4) # s8 r 4reg
        
    def get_sensor_amplification(self,which=None): # TODO SN 103684 unknown
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function get_sensor_amplification() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_register(24864, 0) # u16 r 1reg
        
    def get_heater_output(self,which=None): # TODO SN 103684 unknown
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function get_heater_output() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_register(24865, 0) # u16 r 1reg
        
    def get_dynamic_range(self,which=None): # TODO SN 103684 unknown
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function get_dynamic_range() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_register(24866, 0) # u16 r 1reg
        
    def get_Kd(self,which=None): # 0 to 10000
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(25090) # f32 rw 2reg
        
    def set_Kd(self, value,which=None): # 0 to 10000
        if which is not None:
            self.set_flowmeter_address(which)
        return self.write_float(25090, value) # f32 rw 2reg
        
    def get_Kp(self,which=None): # 0 to 10000
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(25092) # f32 rw 2reg
        
    def set_Kp(self, value,which=None): # 0 to 10000
        if which is not None:
            self.set_flowmeter_address(which)
        return self.write_float(25092, value) # f32 rw 2reg
        
    def get_Ki(self,which=None): # 0 to 10000
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(25094) # f32 rw 2reg
        
    def set_Ki(self, value,which=None): # 0 to 10000
        if which is not None:
            self.set_flowmeter_address(which)
        return self.write_float(25094, value) # f32 rw 2reg
        
    def get_nonlinearity_factor_N(self,which=None): # TODO SN 103684 unknown # 0 to 8000
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function get_nonlinearity_factor_N() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_register(25096, 0) # u16 rw 1reg
        
    def set_nonlinearity_factor_N(self, value,which=None): # 0 to 8000
        if which is not None:
            self.set_flowmeter_address(which)
        self.write_register(25096, value, 0) # u16 rw 1reg
        return
        
    def get_totalizer_1(self,which=None): # sum of all flow ever measured. resetable. in 1/min
        if which is not None:
            self.set_flowmeter_address(which)
        eeprom_saved_every_10min = self.read_float(4)# f32 r 2reg
        value_summed_since_then = self.read_float(25472)# f32 r 2reg
        return eeprom_saved_every_10min+value_summed_since_then
        
    def get_totalizer_2(self,which=None): # sum of all flow ever measured. in 1/min
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(25474) # f32 r 2reg
        
    def get_scale_totalizer_2(self,which=None): # default 1
        if which is not None:
            self.set_flowmeter_address(which)
        return self.read_float(25476)# f32 r 2reg
        
    #def get_unit_totalizer_2(self,which=None): # TODO broken. gives stranges characters back. doesnt work on SN 124663
        #if which is not None:
            #self.set_flowmeter_address(which)
        #return self.read_string(25478, numberOfRegisters=4) # s8 r 4reg
        
    def set_analog_input_filter(self,value,which=None): # 0 < value < 25. default 0==off.
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function set_analog_input_filter() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        self.write_register(21781, value, 0) # uint8 r? 1reg
        return
        
    def get_analog_input_filter(self,which=None): # TODO SN 103684 unknown # 0 < value < 25. default 0==off.
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function get_analog_input_filter() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_register(21781, 0) # uint8 r? 1reg
        
    def set_last_value_profibus(self,value,which=None): # default 0==set to 0%. can be 1 or 0. 1==last applied setpoint
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function set_last_value_profibus() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        self.write_register(22851, value, 0) # uint8 r 1reg
        return
        
    def get_last_value_profibus(self,which=None): # TODO SN 103684 unknown # default 0==set to 0%. can be 1 or 0. 1==last applied setpoint
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function get_last_value_profibus() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_register(22851, 0) # uint8 r 1reg
        
    def set_default_value_profibus(self,value,which=None): # default 0%. between 0 and 100
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function set_default_value_profibus() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        self.write_register(22852, value, 0) # uint8 r 2reg
        return
        
    def get_default_value_profibus(self,which=None): # TODO SN 103684 unknown # default 0%. between 0 and 100
        if which is not None:
            self.set_flowmeter_address(which)
        if self.get_serial_number() < 110000:
            print "ERROR: The function get_default_value_profibus() is not supported on the model with serialnumber: ",self.get_serial_number()
            return None
        return self.read_register(22852, 0) # uint8 r 2reg
        
    def get_all_system_variables(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        print "get_alarm_led: ",self.get_alarm_led()
        print "get_alarm_status: ",self.get_alarm_status()
        print "get_analog_input_current_lower_threshold: ",self.get_analog_input_current_lower_threshold()
        print "get_analog_input_current_upper_threshold: ",self.get_analog_input_current_upper_threshold()
        print "get_analog_input_filter: ",self.get_analog_input_filter()
        print "get_analog_input_lower_threshold: ",self.get_analog_input_lower_threshold()
        print "get_analog_input_mode: ",self.get_analog_input_mode()
        print "get_analog_input_signal: ",self.get_analog_input_signal()
        print "get_analog_input_upper_threshold: ",self.get_analog_input_upper_threshold()
        print "get_analog_input_value: ",self.get_analog_input_value()
        print "get_analog_output: ",self.get_analog_output()
        print "get_analog_output_current_lower_threshold: ",self.get_analog_output_current_lower_threshold()
        print "get_analog_output_current_upper_threshold: ",self.get_analog_output_current_upper_threshold()
        print "get_analog_output_lower_threshold: ",self.get_analog_output_lower_threshold()
        print "get_analog_output_mode: ",self.get_analog_output_mode()
        print "get_analog_output_signal: ",self.get_analog_output_signal()
        print "get_analog_output_upper_threshold: ",self.get_analog_output_upper_threshold()
        print "get_backflow_detection_threshold: ",self.get_backflow_detection_threshold()
        print "get_baudrate: ",self.get_baudrate()
        print "get_calibrated_end_value: ",self.get_calibrated_end_value()
        print "get_change_from_flow_to_pressure_control: ",self.get_change_from_flow_to_pressure_control()
        print "get_default_value_profibus: ",self.get_default_value_profibus()
        print "get_dynamic_range: ",self.get_dynamic_range()
        print "get_flow: ",self.get_flow()
        print "get_flowmeter_address: ",self.get_flowmeter_address()
        print "get_gas_temperature: ",self.get_gas_temperature()
        print "get_hardware_selftest_delay: ",self.get_hardware_selftest_delay()
        print "get_hardware_status: ",self.get_hardware_status()
        print "get_hardware_version: ",self.get_hardware_version()
        print "get_heater_output: ",self.get_heater_output()
        print "get_id: ",self.get_id()
        print "get_identifier: ",self.get_identifier()
        print "get_Kd: ",self.get_Kd()
        print "get_Ki: ",self.get_Ki()
        print "get_Kp: ",self.get_Kp()
        print "get_last_value_profibus: ",self.get_last_value_profibus()
        print "get_lut: ",self.get_lut()
        print "get_lut_access: ",self.get_lut_access()
        print "get_lut_id: ",self.get_lut_id()
        print "get_measurement_unit: ",self.get_measurement_unit()
        print "get_medium_info: ",self.get_medium_info()
        print "get_medium_info_long: ",self.get_medium_info_long()
        print "get_modbus_address: ",self.get_modbus_address()
        print "get_mode: ",self.get_mode()
        print "get_nonlinearity_factor_N: ",self.get_nonlinearity_factor_N()
        print "get_pid_access: ",self.get_pid_access()
        print "get_pid_select: ",self.get_pid_select()
        print "get_power_up_alarm: ",self.get_power_up_alarm()
        print "get_power_up_flow: ",self.get_power_up_flow()
        print "get_pv: ",self.get_pv()
        print "get_ramp_mode: ",self.get_ramp_mode()
        print "get_scale_totalizer_2: ",self.get_scale_totalizer_2()
        print "get_sensor_amplification: ",self.get_sensor_amplification()
        print "get_serial_number: ",self.get_serial_number()
        print "get_software_in_eeprom: ",self.get_software_in_eeprom()
        print "get_software_version: ",self.get_software_version()
        print "get_sp: ",self.get_sp()
        print "get_sp_memory_location: ",self.get_sp_memory_location()
        print "get_totalizer_1: ",self.get_totalizer_1()
        print "get_totalizer_2: ",self.get_totalizer_2()
        print "get_typecode_1: ",self.get_typecode_1()
        print "get_typecode_2: ",self.get_typecode_2()
        print "get_valve_position: ",self.get_valve_position()
        print "get_zeropoint_suppression: ",self.get_zeropoint_suppression()
        return
        
    def get_condensed_system_variables(self,which=None):
        if which is not None:
            self.set_flowmeter_address(which)
        print "-------------------------------"    
        print "Found the following device:"
        print "Serial number:",self.get_serial_number()," Type:",self.get_typecode_1(),"-",self.get_typecode_2()
        print "Flowmeter address:",self.get_modbus_address()
        print "Baudrate:",self.get_baudrate()
        print "Gas:",self.get_medium_info(),"(maximum flow:",self.get_calibrated_end_value()[0],self.get_calibrated_end_value()[1],")"
        print "Flow right now:",self.get_flow()," (Gas temperature:",self.get_gas_temperature(),")"
        print "Programmed setpoint:",self.get_sp()
        print "Valve position right now:",self.get_valve_position(),"%"
        print "Hardware status:",self.get_hardware_status()," HW-Version:",self.get_hardware_version(), "Software version:",self.get_software_version()
        print "Operation mode:",self.get_mode()
        print "Total flow in lifetime:",self.get_totalizer_1()+self.get_totalizer_2()
        print "Medium info long:",self.get_medium_info_long()
        print "-------------------------------"  
        return
        
    def close(self):
        try:
            for flowmeter_address in self.mfc_addresses:
                self.set_sp(0,flowmeter_address)
        except Exception:
            pass
        return
        
    def __del__(self):
        self.close()
        return

    def __exit__(self):
        self.close()
        return
        
# Little demo to show how the class can be used to acquire mass flow measurements
if __name__ == "__main__":
    
    usb_port = "/dev/ttyUSB0" # you can make an udev-rule to get a name like /dev/voegtlin on your lab-computer
    modbus_addresses = range(1,20) #range(1,248) #247 # default address from manufacturer. Use 0 if you want to talk to all instruments at the same moment. Please change in red-y software. Never have two devices with the same address.
    voegtlin_gsc = voegtlin_gsc(usb_port,modbus_addresses,voegtlin_debug=True)
    print "There are flowmeters with the following addresses found:",voegtlin_gsc.get_all_flowmeter_addresses()
    voegtlin_gsc.set_sp(42,voegtlin_gsc.get_all_flowmeter_addresses()[0][0]) # sscm. Pick the first one
    print "The flow of the first one has been set to 42 sscm"
    voegtlin_gsc.get_condensed_system_variables()
    for i in range(10):
        print "The current readout for flow is: ",voegtlin_gsc.get_flow()
    voegtlin_gsc.set_sp(0,voegtlin_gsc.get_all_flowmeter_addresses()[0][0]) # sscm
    print "The flow has been set back to 0"
    voegtlin_gsc.close()
    
