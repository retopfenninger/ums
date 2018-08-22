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
import csv
import os.path

import numpy as np
import os
import sys
import datetime
from prologix_GPIB_ethernet import prologix_ethernet
class keithley_4200gpib:
    def __init__(self,prologic_ip,address):
        try:
            self.device = prologix_ethernet(prologic_ip)
        except:
            return -1
        self.compliance = 0.01
        self.source_range = 0
        self.cur_voltage = 0
        self.source_mode = "DV1"
        self.measure_mode = "TI"
        self.debug = False
        self.read_wait_time = 0.1
        self.path2dir_temp_4200 = os.path.abspath("/home/electrochem/umdata/temp_4200/")

        self.device.settimeout( 10 )

        self.write_to_dev("++mode 1")
        self.write_to_dev("++addr " + str(address))
        self.write_to_dev("++auto 1") # nicht automatisch auf Antwort warten
        self.write_to_dev("++eos 0") # Dont append anything 0=CRLF 1=CR 2=LF 3=None
        self.write_to_dev("++eoi 1") # Indicate End-of-data

        time.sleep(0.1)

    def write_to_dev(self, string):
        if self.debug:
            print "Writing: ",string
        self.device.write(string + "\n")

    def read_from_dev(self, read_wait_time=None):
        #self.write_to_dev("++read")
        if read_wait_time == None:
           read_wait_time = self.read_wait_time
    	time.sleep(read_wait_time)
        if self.debug:
            print "Just read"
        a = self.device.read()
        if not a == None:
            a = a.rstrip()
        if self.debug:
            print a
        return a
        
    def query(self, string, read_wait_time=None):
        self.write_to_dev(string)
        return self.read_from_dev(read_wait_time)
        
    def wait_for_meas_end(self):
      spoll_result = -1

      while True:
        spoll_result = self.query('++spoll')
        if spoll_result == '0' or spoll_result == '1':
          break
        time.sleep(0.1)

    def power_on_gpib_reset(self):
        self.write_to_dev('++rst')
        time.sleep(7)
     
#here starts the keithley specific part
     
    def access_SMU_def(self):
        self.write_to_dev("DE")

    def access_source_setup(self):
        #here in the source setup page the source functions and sweeps will be defined
        self.write_to_dev("SS")

    def access_measure_setup(self):
        self.write_to_dev("SM")

    def access_measure_control(self):
        self.write_to_dev("MD")

    def access_user_mode(self):
        #the user mode commands is just a limited set of commands to perform basic source measure-operations 
        self.write_to_dev("US")

    #this is for the KULT library access - important!
    def access_usrlib_mode(self):
        self.write_to_dev("UL")

#here starts the DE page - channel definition page
#send DE command before

    def channel_def(self, channel, voltage_name, current_name, source_mode, source_function):
        #for every used channel there need to be specified: names for voltage and current, source mode (voltage, current or common) and source function (VAR1, VAR2, constant or VAR')
        #voltage_name and current_name are user-specified up to 6 characters
        #source_mode = 1 - voltage source, source_mode = 2 - current_mode, source_mode = 3 - common
        #source_function = 1 - VAR1 source_function = 2 - VAR2 source_function = 3 - constant source_function = 4 - VAR1' 
        self.write_to_dev("CH" + str(channel) + ", " + str(voltage_name) + ", " + str(current_name) + ", " + str(source_mode) + ", " + str(source_function))

    def channel_def_VS(self, channel, voltage_name, source_function):
        #like channel definition but the SMU will act just as a voltage source
        #voltage_name user-specified up to 6 characters
        #source_function = 1 - VAR1 source_function = 2 - VAR2 source_function = 3 - constant source_function = 4 - VAR1' 
        self.write_to_dev("VS" + str(channel) + ", " + str(voltage_name) + ", " + str(source_function))

    def channel_def_VM(self, channel, voltage_name, source_function):
        #like channel definition but the SMU will act just as a voltmeter
        #voltage_name user-specified up to 6 characters
        #source_function = 1 - VAR1 source_function = 2 - VAR2 source_function = 3 - constant source_function = 4 - VAR1' 
        self.write_to_dev("VM" + str(channel) + ", " + str(voltage_name) + ", " + str(source_function))

    def disable_channel(self, channel):
        self.write_to_dev("CH" + str(channel))

#here starts the SS page - source setup
#send SS command before

    def config_VAR1(self, source_mode, sweep_mode, start_value, stop_value, step_value, compliance_value):
        #source_mode = VR - voltage source, source_mode = IR - current source
        #sweep_mode = 1 - linear sweep, sweep_mode = 2 - log10 sweep, sweep_mode = 3 - log25 sweep, sweep_mode = 4 - log50 sweep
        #start_value (-210 to +210 V) or (-0.1 to 0.1 A)
        #stop_value (-210 to +210 V) or (-0.1 to 0.1 A)
        #step_value  (-210 to +210 V) or (-0.1 to 0.1 A)
        #compliance_value  (-210 to +210 V) or (-0.1 to 0.1 A)
        self.write_to_dev(str(source_mode) + str(sweep_mode) + ", " + str(start_value) + ", " + str(stop_value) + ", " + str(step_value) + ", " + str(compliance_value))

    def config_VAR2(self, source_mode, start_value, step_value, number_of_steps, compliance_value):
        #source_mode = VP - voltage source, source_mode = IP - current source
        #start_value (-210 to +210 V) or (-0.1 to 0.1 A)
        #step_value  (-210 to +210 V) or (-0.1 to 0.1 A)
        #number_of_steps (1 to 32)
        #compliance_value  (-210 to +210 V) or (-0.1 to 0.1 A)
        self.write_to_dev(str(source_mode) + ", " + str(start_value) + ", " + str(step_value) + ", " + str(number_of_steps) + ", " + str(compliance_value))

    def config_VAR1prime(self, RT, RT_channel, FS, FS_channel):
        #RT - ratio (-10 to 10)
        #FS- offset (-210 to -210)
        self.write_to_dev("RT " + str(RT) + ", " + str(RT_channel)) 
        self.write_to_dev("FS " + str(FS) + ", " + str(FS_channel)) 

    def config_VS(self, SMU_channel, output_voltage, compliance):
        self.write_to_dev("VC" + str(SMU_channel) + ", " + str(output_voltage) +", "+ str(compliance)) 
    
    def config_VM(self, SMU_channel, output_current, compliance):
        self.write_to_dev("IC" + str(SMU_channel) + ", "+ str(output_current) +", "+ str(compliance))

    def set_hold_time(self,time):
        #delay the start of an sweep
        self.write_to_dev("HT " + str(time))
 

        #this is one of the parameters that will determine the sweep speed
        #the time duration spent on each step of the sweep is determined by user set delay time and the time it takes to perform the measurement
        self.write_to_dev("DT " + str(time))

    def enable_test_sequence(self, name):
        self.write_to_dev("LI " + str(name))

    def autostandby(self, SMU_channel, output):
        #output = 0 - disable autostandby, output = 1 - enable autostandby
        self.write_to_dev("ST " + str(SMU_channel) + ", " + str(output))

#here starts the SM page - measurement set-up
#send SM command before

    def set_wait_time(self, time):
        #delay the start of the test sequence
        self.write_to_dev("WT " + str(time))
   
    def set_inerval(self, time):
        #set the time interval between measurements
        self.write_to_dev("IN " + str(time))
   
    def set_number_of_readings(self, num):
        #set the number of readings
        #NR (1 to 4096)
        self.write_to_dev("NR " + str(num))
   
    def set_display_mode(self, mode):
        #set the display mode
        #DM (1 or 2)
        self.write_to_dev("DM" + str(mode))
 
    #here starts the MD page - measurement control
    #send MD command before

    def trigger_measurement(self, trigger):
        #command strings to control the measurement
        #in ME1 and ME2 the buffer is cleared before readings are stored
        #in ME3 does not lear the buffer before storing - the buffer can hold up to 4096 readings
        #trigger = 1 - single trigger test - store reading in buffer trigger = 2 - repeat trigger test trigger = 3 - append trigger test, trigger = 4 - abbort test
        self.write_to_dev("ME" + str(trigger))

    #here starts the US page - this is used for the cycling program
    #def are written so that they are compatible with the cycling program in ums and with othe keithleys
    #here the us command gives no current range option and the ums cycling program is too slow and unstable
    #probably best to use the system mode commands and the VAR1 sweep for cycling

    def set_us_command(self, output_source):
        #source range for voltage source: 0 = auto, 1 = 20V, 2 = 200V, 3 = 200V
        self.write_to_dev("US " + self.source_mode +  ", " + str(self.source_range) + ", " + str(output_source) + ", " + str(self.compliance))

    def us_trigger(self):
        str_out = self.query(self.measure_mode)
        return float(str_out[3:])

    def us_stop_output(self):
        self.write_to_dev(self.source_mode)

    def set_compliance_current(self, compl):
        if self.source_mode[:-1] != "DV":
            print "Source mode not set correctly. Changing the source mode to voltage source."
            self.setup_current_measurement()
        self.compliance = compl

    def set_voltage_range(self, range):
        if range < 20:
            self.source_range = 1
        elif range < 200:
            self.source_range = 2
        else:
            self.source_range = 0

    def setup_current_measurement(self, channel = 1):
        self.source_mode = "DV" + str(channel)
        self.measure_mode = "TI" + str(channel)

    def setup_voltage_measurement(self, channel = 1):
        self.source_mode = "DI" + str(channel)
        self.measure_mode = "TV" + str(channel)

    def turn_output_on(self):   #need for ums compatibility
        self.clear_buffer()

    def turn_output_off(self):
        self.clear_buffer()
        self.us_stop_output()

    def set_voltage(self, voltage):
        if self.source_mode[:-1] != "DV":
            print "Source mode not set correctly. Changing the source mode to voltage source."
            self.setup_current_measurement()
        self.set_us_command(voltage)
        self.curr_voltage = voltage

    def get_value(self):
        if self.source_mode[:-1] == "DV":
            A = [self.us_trigger(),time.time()]
        elif self.source_mode[:-1] == "DI":
            A = [self.us_trigger(),time.time()]
        return A

    def get_voltage(self):
        return self.curr_voltage

    def reset(self):    #just for compatibility
        return

    def init(self): # needed for compatibility with keithley_6517B
        return


    #here the command can be used in any page

    def get_output_data(self, channel_name):
        #command strings to get the measurement data
        #the channel_name should be defined in the DE channel definition page
        data_str = self.query("DO " + str(channel_name))
        data_fl = [float(x[1:]) for x in data_str.split(',')]
        return data_fl

    def get_time_data(self, channel_name):
        #to output time measurements use 'ChnT' name where n is the channel number
        data_str = self.query("DO 'CH" + str(channel_name) + "T'")
        data_fl = [float(x) for x in data_str.split(',')]
        return data_fl

    def set_immediate_current_range(self, channel, curr_range, compliance):
        self.write_to_dev("RI " + str(channel) + ", " + str(curr_range) + ", " + str(compliance))

    def save_data(self, file_type, file_name, comment):
        #command strings to save the measurement data
        #file_type = P - program file, file_type = D - Data/Program file
        #file_name - up to 6 characters
        self.query("SV " + str(file_type) + str(file_name) + str(comment))

    def get_file(self, file_type, file_name):
        #file_type = P - program file, file_type = D - Data/Program file
        #file_name - up to 6 characters
        self.query("GT " + str(file_type) + str(file_name) + str(comment))

    def set_source_range(self, range_type):
        self.write_to_dev("SR " + str(range_type))

    def set_integration_time(self, int_type):
        self.write_to_dev("IT" + str(int_type))

    def set_global_resolution(self, resolution):
        self.write_to_dev("RS " + str(resolution))

    def set_lowest_current(self, smu_number, lowest_auto_range):
        self.write_to_dev("RG " + str(smu_number) + ", " +str(lowest_auto_range))

    def enable_data_ready(self, enable):
        #1 for enable
        #0 for disable
        self.write_to_dev("DR " + str(enable))

    def clear_buffer(self):
        self.write_to_dev("BC")


#here start the pulse generator commands - we will however use more the KULT library functions

    def set_output_impedance(self, pulse_channel, load):
        #load (1.0 to 10e6, default = 50)
        self.write_to_dev("PD " + str(self.pulse_channel) + ", " + str(load))
  
    def set_trigger_mode(self, pulse_channel, trigger_mode, count):
        #trigger_mode = 0 - burst, trigger_mode = 1 - continuous, trigger_mode = 2 - trig burst, default = 1
        #count (1 to 232)
        self.write_to_dev("PG " + str(pulse_channel) + ", " + str(trigger_mode) + ", " + str(count))

    def stop_pulse_output(self, pulse_channel):
        self.write_to_dev("PH " + str(pulse_channel))

    def set_pulse_output(self, pulse_channel, output_state, output_mode):
        #output_state = 0 - OFF, output_state = 1 - ON
        #output_mode = 0 - normal, output_mode = 1 - complement
        self.write_to_dev("PO " + str(pulse_channel) + ", " + str(output_state) + ", " + str(output_mode))

    def reset_pulse_card(self, pulse_channel):
        self.write_to_dev("PS " + str(pulse_channel))

    def set_pulse_timing(self, pulse_channel, pulse_period, pulse_width, rise_time, fall_time):
        #the pulse period affects all channels and will be set the same for all channels
        #the rest is channel independent
        self.write_to_dev("PT " + str(pulse_channel) + ", " + str(pulse_period) + ", " + str(pulse_width) + ", " + str(rise_time) + ", " + str(fall_time))

    def set_pulse_voltage(self, pulse_channel, pulse_high, pulse_low, pulse_range, current_limit):
        #each of the commands can be independently set for for each channel of the pulse card
        self.write_to_dev("PV " + str(pulse_channel) + ", " + str(pulse_high) + ", " + str(pulse_low) + ", " + str(pulse_range) + ", " + str(current_limit))

    def set_pulse_trigger_output(self, pulse_channel, pulse_delay, pulse_polarity):
        #the polarity settings affects both channels of a pulse card
        #each channel can have its unique delay
        self.query("TO " + str(pulse_channel) + ", " + str(pulse_delay) + ", " + str(pulse_polarity))

    def set_pulse_trigger_source(self, pulse_channel, trigger_source):
        #the trigger_source = 0 is the software trigger mode. all other triggers are for the Trigger In connector
        self.write_to_dev("TS " + str(pulse_channel) + ", " + str(trigger_source))

    #Here starts the KULT Communication page

    def execute_usrlib(self, library, module):
        self.write_to_dev("EX " + str(library) + ' ' + str(module)) #when calling the module in ums don't use quotation marks, for the output parameters just leave an empty space

    def get_param_by_name(self, param_name, num_value, read_wait_time=None):
        data_str = self.query('GN ' + str(param_name) + ' ' + str(num_values), read_wait_time)
        #data manipulation to get a list of floats as output
        data_fl = [float(x) for x in data_str.split(';')]
        return data_fl

    def get_param_by_number(self, param_name, num_values, read_wait_time=None):
        data_str = self.query('GP ' + str(param_name) + ' ' + str(num_values), read_wait_time)
        #data manipulation to get a list of floats as output
        data_fl = [float(x) for x in data_str.split(';')]
        return data_fl
    ##########################################

    def get_csv(self,filename):
        with open(filename,'rb') as f:
            reader = csv.reader(f,delimiter=',')
            results = []

            for row in reader:
                try:
                    entry = [float(x) for x in row]
                    results.append(entry)
                except ValueError:
                    print(
                        "Could not convert '{}' to "
                        "a float...skipping.".format(entry)
                    )
        print "Successfully read from file"
        os.remove(filename)
        print "Succesfully deleted file after reading"
        return results


    def close(self):
        self.device.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def __exit__(self):
        try:
            self.close()
        except Exception:
            pass
 
# Little demo to show how the class can be used to send a gpib command
if __name__ == "__main__":
    keithley_4200gpib = keithley_4200gpib("electrochem-m33",17)
    keithley_4200gpib.debug = True
    keithley_4200gpib.query("ID")


