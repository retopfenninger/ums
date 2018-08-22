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
import socket
import numpy as np # You also need to install the numpy-package exe under Windows. This is not included in the python environment
import os
import sys
import datetime

class zahner_IM6: # Workes with Thales 4.10 and the remote.vi script under Windows XP with Firewall disabled
    def __init__(self, host="electrochem-m12.mit.edu", mode="Potentiostat"):
        self.host = host
        self.port = 260
        self.io_timeout = 2
        self.lock_timeout = 2
        self.channel_setup_done = False
        self.debug = False
        self.sleep_time = 0 #0.1 # time between asking and getting the answer
        self.wait_time_after_each_measurement = 2
        self.ready = False
        self.mode = mode
        
    def is_ready(self):
        return self.ready
        
    def get_id(self):
        return "Zahner_IM6"
        
    def write_to_dev(self, string):
        if self.debug:
            print "Just wrote: ",string
        self.device.sendall(string)
        #time.sleep(2)
        return

    def read_from_dev(self):
        a = self.recv_end(self.device)
        if self.debug:
            print a
        return a
        
    def query(self, string, string_size1=4,string_size2=0):
        a = []
        self.write_to_dev(string)
        #time.sleep(self.sleep_time)
        a.append(self.read_from_dev())
        if string_size2 > 0:
            a.append(self.read_from_dev())
        return a

    def setup_impedance_measurement(self, num_repetitions=7, amplitude=0.05, bias=0):
        if self.ready:
            return # No need to setup again. Already running
        if amplitude < 0.01:
            if self.mode is "Potentiostat":
                print "The ac-amplitude you choose: ",amplitude,"A might be to low to get reliable results! You should work with 0.01A at least!"
            else:
                print "The ac-amplitude you choose: ",amplitude,"V might be to low to get reliable results! You should work with 0.01V at least!"
        # Set up the experiment. Potentiostatic-mode
        message1 = '\0'+'\x0c'+'\x01'+'\xf8'+'\x01'+'\0'+'\xff'+'\xff'+'ScriptRemote'
        message2 = '\x5e'+'\0'+'\0'+'1:Pot=0:Gal=0:GAL=0:Pset=0.000000:Cset=0.0000000000:Frq=1000.000000:Ampl=0.000000:NW='+str(int(num_repetitions))+':DEV%=0:'
        # Create a TCP/IP socket
        try:
            self.device = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            l_onoff = 1
            l_linger = 0
            self.device.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,struct.pack('ii', l_onoff, l_linger)) # device does not want to terminate well with FIN-packet but needs a RST,ACK
            self.server_address = (self.host, self.port)
            self.device.connect(self.server_address)
            self.write_to_dev(message1)
            self.query(message2,4) # after this receive 4 bytes
            self.get_potential_data()
            #self.set_current(current)
            self.set_ac_amplitude(amplitude*1000)
            if self.mode is "Potentiostat":
                self.set_potential(bias)
            elif self.mode is "Galvanostat":
                self.set_galvanostatic_mode()
                self.set_current(bias)
            self.ready = True
        except Exception:
            print "I could not connect to the Zahner_IM6! Therefore I cannot measure with this device!"
        return
        
    def perform_single_measurement(self,frequency,amplitude_in_millivolts,potential):
        if self.ready:
            # Start a measurement. For each point alone
            #print "measuring...",frequency,"Hz ",amplitude_in_millivolts,"mV "
            self.set_potential(potential)
            self.set_frequency(frequency)
            self.set_ac_amplitude(amplitude_in_millivolts)
            a = self.get_impedance_data()
            time.sleep(self.wait_time_after_each_measurement)
            return a
        else:
            return None
        
    def reset(self):
        self.switch_cell_off()
        return
        
    def switch_cell_on(self):
        self.query('\x09'+'\0'+'\0'+"1:Pot=-1:",4) # after this receive 4 bytes with "..." in it.
        return
        
    def switch_cell_off(self):
        self.query('\x08'+'\0'+'\0'+"1:Pot=0:",4) # after this receive 4 bytes with "..." in it.
        return
        
    def set_potential(self,p): # in volts. range: -4 to 4
        p_new = self.test_if_in_range(p,-4,4)
        if p >=0: # format to x.xxxxxx
            self.query('\x10'+'\0'+'\0'+"1:Pset="+str("{:.6f}".format(p_new))+":",4) # after this receive 4 bytes with "..." in it.
        else:
            self.query('\x11'+'\0'+'\0'+"1:Pset="+str("{:.6f}".format(p_new))+":",4)
        return
        
    def set_current(self,c): # in amps. range: -3 to 3
        c_new = self.test_if_in_range(c,-3,3)
        if c_new >= 0: # format to x.xxxxe-x
            self.query('\x11'+'\0'+'\0'+"1:Cset="+str(self.eformat(c_new,4,1))+":",6) # after this receive 6 bytes with "..ok" in it.
        else: # format to -x.xxxxe-x
            self.query('\x12'+'\0'+'\0'+"1:Cset="+str(self.eformat(c_new,4,1))+":",6) # after this receive 6 bytes with "..ok" in it.
        return
        
    def set_frequency(self,f): # in Hz. range: 1.0e-5 to 8*10e6
        f_new = self.test_if_in_range(f,1.0e-5,8.0e6)
        self.query('\x12'+'\0'+'\0'+"1:Frq="+str(self.eformat(f_new,6,1))+":",4)
        return
        
    def eformat(self,f, prec, exp_digits): # needed since to set the frequency you have to pass a number with only one digit after the exponent e+3 AND NOT e+03 as is default in python
        s = "%.*e"%(prec, f)
        mantissa, exp = s.split('e')
        # add 1 to digits as 1 is taken by sign +/-
        return "%se%+0*d"%(mantissa, exp_digits+1, int(exp))
        
    def set_ac_amplitude(self,a): # in mV. range: 0 to 1000
        a_new = int(self.test_if_in_range(a,0,1000))
        if a_new <= 9:
            self.query('\x10'+'\0'+'\0'+"1:Ampl="+str("{:.6f}".format(a_new))+":",6)
        elif np.log10(a_new) >= 1.0 and np.log10(a_new) < 2.0: # two digit number (10 to 99)
            self.query('\x11'+'\0'+'\0'+"1:Ampl="+str("{:.6f}".format(a_new))+":",6)
        elif np.log10(a_new) >= 2.0 and np.log10(a_new) < 3.0: # three digit number (100 to 999)
            self.query('\x12'+'\0'+'\0'+"1:Ampl="+str("{:.6f}".format(a_new))+":",6)
        else: # # four digit number (1000)
            self.query('\x13'+'\0'+'\0'+"1:Ampl="+str("{:.6f}".format(a_new))+":",6)
        return
        
    def set_num_ac_periods(self,n): # range: 1 to 99 (or 10?)
        n_new = int(self.test_if_in_range(n,1,10))
        if n_new < 10:
            self.query('\x07'+'\0'+'\0'+"1:NW="+str(n)+":",6) # after this receive 6 bytes with "..ok" in it.
        else:
            self.query('\x08'+'\0'+'\0'+"1:NW=10:",6) # after this receive 6 bytes with "..ok" in it.
        return
        
    def set_potentiostatic_mode(self):
        self.mode = "Potentiostat"
        self.query('\x0e'+'\0'+'\0'+"1:Gal=0:GAL=0:",4) # after this receive 4 bytes with "..." in it.
        return
        
    def set_galvanostatic_mode(self):
        self.mode = "Galvanostat"
        self.query('\x0f'+'\0'+'\0'+"1:Gal=-1:GAL=1:",4) # after this receive 4 bytes with "..." in it.
        return
        
    def set_pseudo_galvanostatic_mode(self):
        self.mode = "Pseudo"
        self.query('\x0f'+'\0'+'\0'+"1:Gal=0:GAL=-1:",4) # TODO: Dont know the register here... \x0d?
        return
        
    def get_value(self):
        return
        
    def get_impedance_data(self): # Cell must be on before you can send this command
        if self.mode is "Potentiostat":
            b = self.get_current_data() # You should send this command always first in order to let the instrument turn to the right range
        elif self.mode is "Galvanostat":
            b = self.get_potential_data() # You should send this command always first in order to let the instrument turn to the right range
        else:
            self.get_dc_data() # You should send this command always first in order to let the instrument turn to the right range
            b = 0
        ok,res = self.query('\x0c'+'\0'+'\0'+"1:IMPEDANCE:",6,4) # after this receive 6 bytes with "..ok" in it.
        # Grab error message: '"Potentiostatic loop interrupted!:'
        if "=" not in res:
           print "The Zahner IM6 did interrupt the potentiostatic loop! ac-amplitude too low and noisy."
           return None
        else:
            A = res.split("=")
            A = A[1].split(",")
            result = [float(A[0]),float(A[1][:-1]),b]
            return result
        
    def get_potential_data(self): # Cell must be on before you can send this command
        ok,res = self.query('\x0c'+'\0'+'\0'+"1:POTENTIAL:",6,23) # after this receive 6 bytes with "...ok" in it. After this 23 bytes with the potential data in it.
        if "=" not in res:
           print "The Zahner IM6 did interrupt the potentiostat!"
           return None
        else:
            A = res.split("=")
            result = float(A[1][:-1])
            return result
        
    def get_current_data(self): # Cell must be on before you can send this command
        ok,res = self.query('\x0a'+'\0'+'\0'+"1:CURRENT:",6,23) # after this receive 6 bytes with "...ok" in it. After this 23 bytes with the current data in it.
        if "=" not in res:
           print "The Zahner IM6 did interrupt the potentiostat!"
           return None
        else:
            A = res.split("=")
            result = float(A[1][:-1])
            return result
        
    def get_ocp_data(self):
        self.switch_cell_off()
        A = self.get_potential_data()
        self.switch_cell_on()
        return A
        
    def get_dc_data(self):
        ok,res = self.query('\x14'+'\0'+'\0'+'1:CURRENT:POTENTIAL:',6,43) # after this receive 6 bytes with "...ok" in it. After this 43 bytes with the potential data in it.
        if "=" not in res:
           print "The Zahner IM6 did interrupt the potentiostat!"
           return None
        else:
            A = res.split("=")
            current = float(A[1][:-10])
            potential = float(A[2][:-1])
            result = [current,potential]
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
        if self.ready:
            self.switch_cell_off()
        return
        
    def unflush(self): # compatibility with Gamry R600
        return
        
    def close(self):
        if self.ready:
            # Send termination command
            self.switch_cell_off()
            self.ready = False
            return self.device.close()
        else:
            return

    def recv_end(self,the_socket):
        End='\r' # This is the delimiter the Zahner sends with each package
        total_data=[];data=''
        while True:
                data=the_socket.recv(4)
                if End in data:
                    total_data.append(data[:data.find(End)])
                    break
                total_data.append(data)
                if len(total_data)>1:
                    #check if end_of_data was split
                    last_pair=total_data[-2]+total_data[-1]
                    if End in last_pair:
                        total_data[-2]=last_pair[:last_pair.find(End)]
                        total_data.pop()
                        break
        return ''.join(total_data)
        
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
   
    ip_address = "192.168.1.49"
    zahner_IM6 = zahner_IM6(ip_address)
    zahner_IM6.setup_impedance_measurement()
    zahner_IM6.switch_cell_on()
    time.sleep(3)
    amplitude_in_millivolts = 100
    frequency_values = [1e3,2e3,2.5e3,3e3,4e3,5e3,6e3,7e3,8e3,9e3,1e4]
    result = []
    for frequency in frequency_values:
        a = zahner_IM6.perform_single_measurement(frequency,amplitude_in_millivolts)
        result.append(a)
    zahner_IM6.close()
    print result

