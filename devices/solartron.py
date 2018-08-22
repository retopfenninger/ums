#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Unified measurement software UMS
# New measurement software for the electrochemical materials group, Prof. Jennifer Rupp
#
# Copyright (c) 2015 Reto Pfenninger, department of materials, D-MATL, ETH Zürich
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
import socket
import numpy as np # You also need to install the numpy-package exe under Windows. This is not included in the python environment
import os
import sys
import datetime
from prologix_GPIB_ethernet import prologix_ethernet

class solartron: # Works with 1287 and 1260
    def __init__(self, device_file="electrochem-m31", mode="Potentiostat"):
        try:
            if "/" not in device_file: # means it is not a path to /dev/xxx
                self.using_GPIB_to_Ethernet = True
                self.device = prologix_ethernet(device_file)
            else:
                self.device = open(device_file, "w+")
                self.using_GPIB_to_Ethernet = False
        except:
            return -1
        self.solartron_1287_address = 6 # address +1 is the minor address to get binary data. *Potentiostat/Galvanostat* 
        self.solartron_1260_address = 4 # address +1 is the minor address to get binary data. *Analyzer*
        self.sleep_time = 0.3 # time between asking and getting the answer
        self.current_address = self.solartron_1260_address
        #self.sleep_time = 2 # time between asking and getting the answer
        self.sleep_time_specific_measurement = 0
        self.bias = 0
        self.ready = False
        self.mode = mode
        self.debug = True
        self.write_to_dev("++mode 1")
        self.talk_to_analyzer() # 1260
        self.write_to_dev("++auto 0")
        self.write_to_dev("++eos 3") # Dont append anything 0=CRLF 1=CR 2=LF 3=None
        self.write_to_dev("++eoi 1") # Indicate End-of-data
        #self.write_to_dev("TT1"self.solartron_1260_address) # initialize device
        #time.sleep(5.0)
        self.write_to_dev("TT2",self.solartron_1260_address) # reset device poland
        time.sleep(5.0)
        ##self.write_to_dev("TT3"self.solartron_1260_address) # reset device
        ##time.sleep(5.0)
        
        # Poland
        #self.write_to_dev("OP1,0") # no RS232 output
        #self.write_to_dev("OP2,1") # GPIB output
        #self.write_to_dev("OP3,0") # no file output
        #self.write_to_dev("RH0") # data output heading, poland
        #self.write_to_dev("BP1") # ?
        #self.write_to_dev("SW0") # sweep?
        #self.write_to_dev("VI0") # ?
        #self.write_to_dev("UW0") # ?
        #self.write_to_dev("CV1") # ?
        #self.write_to_dev("RR0") # ?
        #self.write_to_dev("AU0") # ?
        #self.write_to_dev("SO2,1") # ?
        #self.write_to_dev("FC") # file clear
        
        
        # Solartron self
        self.write_to_dev("OP2,1",self.solartron_1260_address) # GPIB output all
        self.talk_to_generator() # 1287
        self.write_to_dev("IL6",self.solartron_1287_address) # current limit range 2A
        self.write_to_dev("OL2",self.solartron_1287_address) # no current off limit
        self.write_to_dev("PB2",self.solartron_1287_address) # type C potentiostat mode >1MHz bandwith
        self.write_to_dev("RG0",self.solartron_1287_address) # DVM Control input range auto
        self.write_to_dev("DG0",self.solartron_1287_address) # DVM Control 5x9 digits
        self.switch_polVI_mode_on() # 1287
        self.switch_cell_on() # measure RE1,Re2 delta-RE, delta-RE-Bi, POL, delta-POL, CE, I, I-Bi, Half-Standby (1287)
        self.set_filter_off() # 10Hz Filter off (1287)
        self.set_dc_potential_accross_RE1_and_RE2(0.0) # dc potential accross RE1 and RE2 for the potentiostat 0.0V (-14.5 to 14.5) (1287)
        self.set_voltage_bias_rejection_voltage(0.0) # fixed rejection voltage 0.0V (0 to 14.5V) (1287)
        #self.write_to_dev("OT1") # GPIB Output terminator cr lf and EOI TODO could also be for analyser
        self.write_to_dev("OT1",self.solartron_1260_address) # no file output TODO
        self.write_to_dev("OP3,0",self.solartron_1260_address) # no file output
        self.write_to_dev("OP2,0",self.solartron_1260_address) # GPIB output off ??? WFT
        self.write_to_dev("VI0",self.solartron_1260_address) # display frequency
        self.write_to_dev("SW0",self.solartron_1260_address) # disable sweeping
        self.write_to_dev("CV0",self.solartron_1260_address) # display options
        self.write_to_dev("UW0",self.solartron_1260_address) # normal phase
        self.set_potentiostatic_mode() # 1260
        self.write_to_dev("IA0",self.solartron_1260_address) # generator I amplitude 0A (you need to tell this to the analyser, stupid but true)
        self.write_to_dev("IB0",self.solartron_1260_address)# generator I bias 0A (you need to tell this to the analyser, stupid but true)
        self.write_to_dev("ME0",self.solartron_1260_address) # monitor off
        #self.write_to_dev("RA3,5",self.solartron_1260_address) # input I range 60mA
        self.write_to_dev("RA3,0",self.solartron_1260_address) # input I auto-range TODO doesn't this make more sense?
        self.set_input_current_coupling("dc") #1260
        self.write_to_dev("FV0",self.solartron_1260_address) # display options
        self.write_to_dev("CI0",self.solartron_1260_address) # display options
        self.write_to_dev("CZ0",self.solartron_1260_address) # display options
        self.write_to_dev("CY0",self.solartron_1260_address) # display options
        self.write_to_dev("VA0",self.solartron_1260_address) # generator voltage amplitude 0A (you need to tell this to the analyser, stupid but true)
        self.set_potential_bias(0.0) # generator voltage bias 0A (you need to tell this to the analyser, stupid but true) (1260)
        self.write_to_dev("AU0",self.solartron_1260_address) # auto integration off
        self.set_integration_time(0.2) # integration time 0.2s (1260)
        self.set_integration_delay(0.0) # delay 0s (1260)
        self.write_to_dev("RA1,0",self.solartron_1260_address) # input V1 autorange
        self.write_to_dev("RA2,0",self.solartron_1260_address) # input V2 autorange
        self.set_input_voltage_coupling(1,"dc") # 1260
        self.set_input_voltage_coupling(2,"dc") # 1260
        self.set_input_mode(1,"single") # 1260
        self.set_input_mode(2,"single") # 1260
        self.set_outer_bnc(1,"floating") # 1260
        self.set_outer_bnc(2,"floating") # 1260
        self.set_outer_bnc(1,"floating") # Why do I need to repeat? (1260)
        self.write_to_dev("SO1,2",self.solartron_1260_address) # source V1 / V2 could be 2,1
        #self.write_to_dev("SO2,0",self.solartron_1260_address) # current on V2 TODO
        #self.write_to_dev("SO0,2",self.solartron_1260_address) # current on V2 TODO
        #self.write_to_dev("SO3,0",self.solartron_1260_address) # current on V2 TODO
        #self.write_to_dev("SO3,2",self.solartron_1260_address) # current on V2 TODO
        #self.write_to_dev("SO2,3",self.solartron_1260_address) # current on V2 TODO
        self.write_to_dev("BP0",self.solartron_1260_address) # error beep off
        self.write_to_dev("CE",self.solartron_1260_address) # clear errors TODO 1287
        self.write_to_dev("OP2,1",self.solartron_1260_address) #  GPIB output all
        self.write_to_dev("VA0",self.solartron_1260_address) # generator voltage amplitude 0A (you need to tell this to the analyser, stupid but true)
        self.set_potential_bias(0.0) # generator voltage bias 0A (you need to tell this to the analyser, stupid but true)
        self.write_to_dev("PI1",self.solartron_1287_address) # Add external signal to the polarization (from PVF pr PC F at gain of x0.01
        self.switch_polarization_on() # 1287
        self.write_to_dev("TR1",self.solartron_1287_address) # measurement trigger set to continuous measurements
        self.write_to_dev("RU1",self.solartron_1287_address) # digital voltmeter RUN
        self.write_to_dev("BR1",self.solartron_1287_address) # bias reject ON
        self.write_to_dev("VX1",self.solartron_1287_address) # 10x voltage amplification to rear output
        self.write_to_dev("IX1",self.solartron_1287_address) # 10x current amplification to rear output
        #self.write_to_dev('RR8',self.solartron_1287_address) # 1 MOhm resistor selected TODO trial
        
    def change_address(self,address):
        if address != self.current_address:
            self.write_to_dev("++addr " + str(address))
            self.current_address = address
        return
        
    def talk_to_analyzer(self):
        self.change_address(self.solartron_1260_address)
        return
        
    def talk_to_generator(self):
        self.change_address(self.solartron_1287_address)
        return
        
    def write_to_dev(self, string, which=None):
        if self.debug:
            if which is not None and which is not self.current_address:
                print "Now talking to:",which
        if which is not None:
            self.change_address(which)
        self.device.write(string + "\n")
        if self.debug:
            print "Just wrote: ",string
        time.sleep(self.sleep_time)
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
        
    def is_ready(self):
        return self.ready
        
    def get_id(self):
        return "Solartron"
        
    def query(self, string):
        self.write_to_dev(string)
        time.sleep(self.sleep_time_specific_measurement)
        return self.read_from_dev()

    def setup_impedance_measurement(self, num_repetitions=7, amplitude=0.05, bias=0):
        if self.ready:
            return # No need to setup again. Already running
        try:
            if self.mode is "Potentiostat":
                self.set_potentiostatic_mode()
                self.set_potential_bias(bias)
            elif self.mode is "Galvanostat":
                self.set_galvanostatic_mode()
                self.set_current_bias(bias)
            self.bias = bias
            self.set_ac_amplitude(amplitude,self.mode)
            self.ready = True
        except Exception:
            print "I could not connect to the Solartron! Therefore I cannot measure with this device!"
        return
        
    def perform_single_measurement(self,frequency,amplitude_in_millivolts):
        if self.ready:
            # Start a measurement. For each point alone
            print "measuring...",frequency,"Hz ",amplitude_in_millivolts,"mV "
            self.set_frequency(frequency) # to analyser
            self.set_integration_delay(0) # to analyser
            #self.set_generator_voltage_potential(1.0) # to analyser
            self.set_ac_amplitude(amplitude_in_millivolts/1000.0,self.mode)
            self.set_potential_bias(0.0) # generator voltage bias 0A (you need to tell this to the analyser, stupid but true)
            self.sleep_time_specific_measurement = (1/frequency)*5+3
            self.set_integration_time((1/frequency)*5+0.01)
            a = self.get_impedance_data(frequency)
            return a
        else:
            return None
        
    def eformat(self,f, prec, exp_digits): # needed since to set the frequency you have to pass a number with only one digit after the exponent e+3 AND NOT e+03 as is default in python
        s = "%.*e"%(prec, f)
        mantissa, exp = s.split('e')
        # add 1 to digits as 1 is taken by sign +/-
        return "%sE%+0*d"%(mantissa, exp_digits+1, int(exp))
        
    def reset(self):
        self.talk_to_generator()
        self.write_to_dev("BK3") # reset
        self.switch_cell_off()
        return
        
    def switch_cell_on(self):
        self.talk_to_generator()
        self.write_to_dev('BY1') # measure RE1,Re2 delta-RE, delta-RE-Bi, POL, delta-POL, CE, I, I-Bi
        return
        
    def switch_cell_off(self):
        self.talk_to_generator()
        self.write_to_dev('BY0') # measure POL, delta-POL, CE only
        time.sleep(1.0)
        return
        
    def switch_polarization_on(self):
        self.talk_to_generator()
        self.write_to_dev('PW1') #???
        return
        
    def switch_polarization_off(self):
        self.talk_to_generator()
        self.write_to_dev('PW0') #???
        return
        
    def switch_polVI_mode_on(self):
        self.talk_to_generator()
        self.write_to_dev('ON0') # apply PV and PC to the cell
        return
        
    def switch_restVI_mode_on(self):
        self.talk_to_generator()
        self.write_to_dev('ON1') # cell held at its rest potential
        return
        
    def voltage_bias_reject_auto(self):
        self.talk_to_generator()
        self.write_to_dev('VT0') # auto, default
        return
        
    def voltage_bias_reject_fixed(self):
        self.talk_to_generator()
        self.write_to_dev('VT1')
        return
        
    def set_voltage_bias_rejection_voltage(self,p):
        p_new = self.test_if_in_range(p,0,14.5)
        self.talk_to_generator()
        self.write_to_dev('VR'+str(self.eformat(p_new,4,1)))
        return
        
    def current_bias_reject_auto(self):
        self.talk_to_generator()
        self.write_to_dev('IT0') # auto, default
        return
        
    def current_bias_reject_fixed(self):
        self.talk_to_generator()
        self.write_to_dev('IT1')
        return
        
    def set_current_bias_rejection_current(self,p):
        p_new = self.test_if_in_range(p,0,2)
        self.talk_to_generator()
        self.write_to_dev('IR'+str(self.eformat(p_new,4,1)))
        return
        
    def set_filter_on(self):
        self.talk_to_generator()
        self.write_to_dev('FI1') # 10Hz filter
        return
        
    def set_filter_off(self):
        self.talk_to_generator()
        self.write_to_dev('FI0') # 10Hz filter
        return
        
    def set_IR_compensation_on(self):
        self.talk_to_generator()
        self.write_to_dev('CC1')
        return
        
    def set_IR_compensation_off(self):
        self.talk_to_generator()
        self.write_to_dev('CC0')
        return
        
    def set_voltmeter_on(self):
        self.talk_to_generator()
        self.write_to_dev('RU1') # run voltmeter
        return
        
    def set_voltmeter_off(self):
        self.talk_to_generator()
        self.write_to_dev('RU0') # halt voltmeter
        return
        
    def set_averaging_on(self):
        self.talk_to_generator()
        self.write_to_dev('AV1')
        return
        
    def set_averaging_off(self):
        self.talk_to_generator()
        self.write_to_dev('AV0')
        return
        
    def set_sweep_segment_potential(self,p): 
        p_new = self.test_if_in_range(p,-14.5,14.5)
        self.talk_to_generator()
        self.write_to_dev('VA'+str(self.eformat(p_new,4,1))) # in volts. In ramp sweep segment definition
        return
        
    def set_generator_voltage_potential(self,p): 
        #p_new = self.test_if_in_range(p,0,3)
        #self.talk_to_analyzer()
        #self.write_to_dev('VA'+str(self.eformat(p_new,4,1))) # in volts. range: 0 to 3 below 10MHz, 0 to 1 otherwise
        p_new = self.test_if_in_range(p,-14.5,14.5)
        self.talk_to_generator()
        self.write_to_dev('PV'+str(self.eformat(p_new,4,1))) # in volts
        #self.write_to_dev('VC'+str(self.eformat(p_new,4,1))) # in volts. range: 0 to 3 below 10MHz, 0 to 1 otherwise
        return
        
    def set_generator_current_potential(self,c): 
        c_new = self.test_if_in_range(c,-2.0,2.0)
        #c_new = self.test_if_in_range(c,0,60e-3)
        #self.talk_to_analyzer()
        #self.write_to_dev('IA'+str(self.eformat(c_new,4,1))) # in amps. range: 0 to 60e-3 below 10MHz, 0 to 20 otherwise
        self.talk_to_generator()
        self.write_to_dev('PC'+str(self.eformat(c_new,4,1))) # in amps. range: 0 to 60e-3 below 10MHz, 0 to 20 otherwise
        return
        
    def set_dc_potential_accross_RE1_and_RE2(self,p): 
        p_new = self.test_if_in_range(p,-14.5,14.5)
        self.talk_to_generator()
        self.write_to_dev('PV'+str(self.eformat(p_new,4,1))) # -14.5V to 14.5V
        return
        
    def set_sweep_segment_current(self,c): 
        c_new = self.test_if_in_range(c,-2,2)
        self.talk_to_generator()
        self.write_to_dev('JA'+str(self.eformat(c_new,4,1))) # in amps
        return
        
    def set_integration_delay(self,p): # in seconds
        p_new = self.test_if_in_range(p,0,1e5)
        self.talk_to_analyzer()
        self.write_to_dev('MS'+str(self.eformat(p_new,4,1)))
        return
        
    def set_potential_bias(self,p): # in volts
        p_new = self.test_if_in_range(p,-40.95,40.95)
        self.talk_to_analyzer()
        self.write_to_dev('VB'+str(self.eformat(p_new,4,1)))
        return
        
    def set_current_bias(self,c): # in amps.
        c_new = self.test_if_in_range(c,-100e-3,100e-3)
        self.talk_to_analyzer()
        self.write_to_dev('IB'+str(self.eformat(c_new,4,1)))
        return
        
    def set_compliance_voltage(self,p): # in volts. range: 0 to 3 below 10MHz, 0 to 1 otherwise
        p_new = self.test_if_in_range(p,0,3)
        self.talk_to_analyzer()
        self.write_to_dev('VC'+str(self.eformat(p_new,4,1)))
        return
        
    def set_compliance_current(self,c):  # in amps. range: 0 to 60e-3 below 10MHz, 0 to 20 otherwise
        c_new = self.test_if_in_range(c,0,60e-3)
        self.talk_to_analyzer()
        self.write_to_dev('IC'+str(self.eformat(c_new,4,1)))
        return
        
    def set_frequency(self,f): # in Hz
        f_new = self.test_if_in_range(f,10.0e-6,32.0e6)
        self.talk_to_analyzer()
        self.write_to_dev('FR'+str(self.eformat(f_new,7,1)))
        return
        
    def set_ac_amplitude(self,a,mode):
        if mode is "Potentiostat":
            self.set_generator_voltage_potential(a)
        elif mode is "Galvanostat":
            self.set_generator_current_potential(a)
        return
        
    def set_num_ac_periods(self,n): # for compatibility with Zahner IM6
        return
        
    def set_integration_time(self,t):
        t_new = self.test_if_in_range(t,0.01,1e5) # seconds
        self.talk_to_analyzer()
        self.write_to_dev("IS"+str(self.eformat(t,4,1)))
        return
        
    def set_input_voltage_range(self,channel,max_voltage):
        self.talk_to_analyzer()
        if channel == 1:
            if max_voltage < 30e-3:
                self.write_to_dev("RA1,1") # 30mV
            elif max_voltage < 300e-3:
                self.write_to_dev("RA1,2") # 300mV
            elif max_voltage < 3.0:
                self.write_to_dev("RA1,3") # 300mV
            else:
                self.write_to_dev("RA1,0") # auto
        if channel == 2:
            if max_voltage < 30e-3:
                self.write_to_dev("RA2,1") # 30mV
            elif max_voltage < 300e-3:
                self.write_to_dev("RA2,2") # 300mV
            elif max_voltage < 3.0:
                self.write_to_dev("RA2,3") # 300mV
            else:
                self.write_to_dev("RA2,0") # auto
        return
        
    def set_input_current_range(self,max_current):
        self.talk_to_analyzer()
        if max_current < 6e-6:
            self.write_to_dev("RA3,1") # 6uA
        elif max_current < 60e-6:
            self.write_to_dev("RA3,2") # 60uA
        elif max_current < 600e-6:
            self.write_to_dev("RA3,3") # 600uA
        elif max_current < 6e-3:
            self.write_to_dev("RA3,4") # 6mA
        elif max_current < 60e-3:
            self.write_to_dev("RA3,5") # 60mA
        else:
            self.write_to_dev("RA3,0") # auto
        return
        
    def set_input_voltage_coupling(self,channel,ac_dc="dc"):
        self.talk_to_analyzer()
        if channel == 1:
            if ac_dc is "ac":
                self.write_to_dev("DC1,1")
            else:
                self.write_to_dev("DC1,0") # recommended
        if channel == 2:
            if ac_dc is "ac":
                self.write_to_dev("DC2,1")
            else:
                self.write_to_dev("DC2,0") # recommended
        return
        
    def set_input_current_coupling(self,ac_dc="dc"):
        self.talk_to_analyzer()
        if ac_dc is "ac":
            self.write_to_dev("DC3,1")
        else:
            self.write_to_dev("DC3,0") # recommended
        return

    def set_input_mode(self,channel,input_mode="single"):
        self.talk_to_analyzer()
        if channel == 1:
            if input_mode is "differential":
                self.write_to_dev("IP1,1")
            else:
                self.write_to_dev("IP1,0") # single
        if channel == 2:
            if input_mode is "differential":
                self.write_to_dev("IP2,1")
            else:
                self.write_to_dev("IP2,0") # single
        return
        
    def set_outer_bnc(self,channel,outer_bnc="grounded"):
        self.talk_to_analyzer()
        if channel == 1:
            if outer_bnc is "floating":
                self.write_to_dev("OU1,1")
            else:
                self.write_to_dev("OU1,0") # grounded
        if channel == 2:
            if outer_bnc is "floating":
                self.write_to_dev("OU2,1")
            else:
                self.write_to_dev("OU2,0") # grounded
        return
        
    def set_potentiostatic_mode(self):
        self.mode = "Potentiostat"
        self.talk_to_analyzer()
        self.write_to_dev('GT0')
        #self.write_to_dev('PO0')
        return
        
    def set_galvanostatic_mode(self):
        self.mode = "Galvanostat"
        #self.talk_to_analyzer() # 1260
        self.write_to_dev('GT1',self.solartron_1260_address) # galvanostatic mode
        #self.write_to_dev('PO1')
        # Solartron software
        self.write_to_dev('RU1',self.solartron_1287_address) # +2.07035E-03,+1.51106E-08,00,00 Voltmeter RUN
        self.write_to_dev('RU1',self.solartron_1287_address) # +2.07112E-03,+1.34231E-08,00,00 Voltmeter RUN
        self.write_to_dev('RU1',self.solartron_1287_address) # +2.07035E-03,+1.45737E-08,00,00 Voltmeter RUN
        self.write_to_dev('GT1',self.solartron_1260_address) # galvanostatic mode
        self.write_to_dev('GP0',self.solartron_1287_address) # turn GPIB off ?
        self.write_to_dev('CE',self.solartron_1287_address)  #  clear errors TODO maybe 1260
        self.write_to_dev('PO1',self.solartron_1287_address) # set 1287 to operate as galvanostat, PO0 would be potentiostat
        self.set_dc_potential_accross_RE1_and_RE2(0) # PV0 generator (1287)
        self.write_to_dev('PC0',self.solartron_1287_address) # define the current through the cell =0 (-2 to 2)
        self.write_to_dev('RR1',self.solartron_1287_address) # 0.1 Ohm resistor selected
        self.write_to_dev('RG0',self.solartron_1287_address) # DVM Control input range auto
        self.write_to_dev('DG0',self.solartron_1287_address) # DVM Control 5x9 digits
        self.set_IR_compensation_off() # 1287
        self.switch_polVI_mode_on() # 1287
        self.switch_cell_on() # 1287
        self.write_to_dev('PI1',self.solartron_1287_address) # Add external signal to the polarization (from PVF pr PC F at gain of x0.01 (1287)
        self.set_filter_off() # 1287
        self.write_to_dev('IL6',self.solartron_1287_address) # current limit range 2A
        self.write_to_dev('OL2',self.solartron_1287_address) # no current off limit
        self.write_to_dev('GB2',self.solartron_1287_address) # Type C galvanostat with >7.5kHz bandwith
        self.set_generator_current_potential(0.0) # define the current through the cell =0.0000 (-2 to 2) (1287)
        self.set_current_bias_rejection_current(0.0) # 1287
        self.write_to_dev('VX0',self.solartron_1287_address) # 10x voltage amplification to rear output OFF
        self.write_to_dev('IX0',self.solartron_1287_address) # 10x current amplification to rear output OFF
        self.write_to_dev('BR0',self.solartron_1287_address) # bias reject OFF
        self.set_filter_off() # 1287
        self.write_to_dev('RR5',self.solartron_1287_address) # 1 kOhm standard resistor FIXME this is the last unique command in galvanomode
        self.write_to_dev('OT1',self.solartron_1287_address) # GPIB Output terminator cr lf and EOI TODO could also be for 1260
        self.write_to_dev('OP3,0',self.solartron_1260_address) # no file output
        self.write_to_dev('OP2,0',self.solartron_1260_address) # GPIB output off ??? WFT
        self.write_to_dev('VI0',self.solartron_1260_address) # display frequency
        self.write_to_dev('SW0',self.solartron_1260_address) # disable sweeping
        self.write_to_dev('CV0',self.solartron_1260_address) # display options
        self.write_to_dev('UW0',self.solartron_1260_address) # normal phase
        self.set_potentiostatic_mode() # TODO WTF??? 1260
        self.write_to_dev('IA0',self.solartron_1260_address) # generator I amplitude 0A
        self.write_to_dev('IB0',self.solartron_1260_address)# generator I bias 0A
        self.write_to_dev('ME0',self.solartron_1260_address) # monitor off
        self.write_to_dev('RA3,0',self.solartron_1260_address) # input I range auto TODO Doesn't this make more sense?
        #self.write_to_dev('RA3,5',self.solartron_1260_address) # input I range 60mA
        self.set_input_current_coupling("dc") # 1260
        self.write_to_dev('FV0',self.solartron_1260_address) # display options
        self.write_to_dev('CI0',self.solartron_1260_address) # display options
        self.write_to_dev('CZ0',self.solartron_1260_address) # display options
        self.write_to_dev('CY0',self.solartron_1260_address) # display options
        self.write_to_dev('VA0',self.solartron_1260_address) # generator voltage amplitude 0A
        self.set_potential_bias(0.0) # 1260
        self.write_to_dev('AU0',self.solartron_1260_address) # auto integration off
        self.set_integration_time(0.2) # 1260
        self.set_integration_delay(0.0) # 1260
        self.write_to_dev('RA1,0',self.solartron_1260_address) # input V1 autorange
        self.write_to_dev('RA2,0',self.solartron_1260_address) # input V2 autorange
        self.set_input_voltage_coupling(1,"dc") # 1260
        self.set_input_voltage_coupling(2,"dc") # 1260
        self.set_input_mode(1,"single") # 1260
        self.set_input_mode(2,"single") # 1260
        self.set_outer_bnc(1,"floating") # 1260
        self.set_outer_bnc(2,"floating") # 1260
        self.write_to_dev('SO1,2',self.solartron_1260_address) # source V1 / V2 could be 2,1
        self.write_to_dev('BP0',self.solartron_1260_address) # error beep off
        self.write_to_dev('CE',self.solartron_1260_address) # clear errors TODO 1287
        self.write_to_dev('OP2,1',self.solartron_1260_address) # GPIB output all
        self.write_to_dev('VA0',self.solartron_1260_address) # generator voltage amplitude 0A
        self.set_potential_bias(0.0) # 1260
        self.write_to_dev('PI0',self.solartron_1287_address) # add polarization from FRA at gain of x1 FIXME this is the only parameter different from init in galvanomode
        self.switch_polarization_on() # 1287
        self.write_to_dev('TR1',self.solartron_1287_address) # measurement trigger set to continuous measurements
        self.write_to_dev('RU1',self.solartron_1287_address) # digital voltmeter RUN
        self.write_to_dev('BR1',self.solartron_1287_address) # bias reject ON
        self.write_to_dev("VX1",self.solartron_1287_address) # 10x voltage amplification to rear output
        self.write_to_dev("IX1",self.solartron_1287_address) # 10x current amplification to rear output
        #self.write_to_dev('VA?') # +0.0000E+00
        return
        
    def set_pseudo_galvanostatic_mode(self): # for compatibility with Zahner IM6
        return
        
    def get_value(self,frequency=None):
        self.talk_to_analyzer()
        A = self.query('SI') # one-shot measurement. ("RE" for cyclic measurement-mode)
        try:
            A = A.split(",")
            result = [float(A[1]),float(A[2]),0,float(A[0])]
            if np.absolute(float(frequency)-float(A[0]))>0.1 and frequency is not None: # Means we asked too fast for the reply from the device.
                print "get_value freq=",float(frequency)," is not ",float(A[0])
                result = None
        except Exception:
            result = None
        return result
        
    def get_impedance_data(self,frequency): # Cell must be on before you can send this command
        if self.mode is "Potentiostat":
            b = 0 # self.get_current_data(frequency) # You should send this command always first in order to let the instrument turn to the right range
        elif self.mode is "Galvanostat":
            b = 0 # self.get_potential_data(frequency) # You should send this command always first in order to let the instrument turn to the right range
        else:
            b = 0
        f = self.get_value(frequency)
        f.append(b)
        return f
        
    def get_potential_data(self): # Cell must be on before you can send this command
        self.talk_to_generator() # 1287
        self.write_to_dev('EB1') # error bell off
        self.switch_cell_on() # (1287)
        self.write_to_dev("DG3") # DVM Control 3x9 digits
        self.write_to_dev("TR0") # measurement trigger single measurement
        self.write_to_dev("GP2") # turn GPIB on
        ok,res = self.query('RU1') # digital voltmeter RUN
        self.write_to_dev("GP0") # turn GPIB off ?
        self.write_to_dev("CE") #  clear errors
        self.switch_cell_off()
        A = res.split(",")
        return float(A[0]) # volts
        
    def get_current_data(self): # Cell must be on before you can send this command
        self.talk_to_generator() # 1287
        self.write_to_dev('EB1') # error bell off
        self.switch_cell_on() # (1287)
        self.write_to_dev("DG3") # DVM Control 3x9 digits
        self.write_to_dev("TR0") # measurement trigger single measurement
        self.write_to_dev("GP2") # turn GPIB on
        ok,res = self.query('RU1') # digital voltmeter RUN
        self.write_to_dev("GP0") #  # turn GPIB off ?
        self.write_to_dev("CE") #  clear errors
        self.switch_cell_off()
        A = res.split(",")
        return float(A[1]) # amps
        
    def get_ocp_data(self):
        return self.get_potential_data()
        
    def get_dc_data(self):
        self.talk_to_generator() # 1287
        self.write_to_dev('EB1') # error bell off
        self.switch_cell_on() # (1287)
        self.write_to_dev("DG3") # DVM Control 3x9 digits
        self.write_to_dev("TR0") # measurement trigger single measurement
        self.write_to_dev("GP2") # turn GPIB on
        ok,res = self.query('RU1') # digital voltmeter RUN
        self.write_to_dev("GP0") #  # turn GPIB off ?
        self.write_to_dev("CE") #  clear errors
        self.switch_cell_off()
        A = res.split(",")
        result = [float(A[0]),float(A[1])] # volts, amps
        return result
        
    def test_if_in_range(self,n,min_,max_):
        if n >= min_ and n <= max_:
            return n
        else:
            print "The value: "+str(n)+" is out of the allowed range: ("+str(min_)+","+str(max_)+")"
            if n<min_:
                return min_
            return max_
        
    def flush(self): # command between two measurements in arrhenius program
        return
        
    def unflush(self): # compatibility with Gamry R600
        return
        
    def close(self):
        if self.ready:
            # Send termination command
            #self.write_to_dev("FC") # file clear
            self.switch_cell_off()
            self.ready = False
            return self.device.close()
        else:
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
        
# Little demo to show how the class can be used to acquire a simple impedance measurement
if __name__ == "__main__":
   
    ip_address = "electrochem-m31"
    #ip_address = "192.168.1.3"
    solartron = solartron(ip_address)
    solartron.setup_impedance_measurement()
    solartron.switch_cell_on()
    amplitude_in_millivolts = 20
    frequency_values = [1e6,2e5,2.5e4,3e3,4e3,5e3,6e3,7e3,8e3,9e3,1e4]
    #frequency_values = [1e3,2e3,2.5e3,3e3,4e3,5e3,6e3,7e3,8e3,9e3,1e4]
    result = []
    for frequency in frequency_values:
        a = solartron.perform_single_measurement(frequency,amplitude_in_millivolts)
        result.append(a)
    solartron.close()
    print result

