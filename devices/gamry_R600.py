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

import socket
import sys
import numpy as np
import time

class gamry_R600:
    def __init__(self, host='172.31.46.15', mode="Potentiostat", which=0): # electrochem-m15 '172.31.46.15'
        self.host = host
        self.mode = mode
        self.which = which
        self.host_listening_port = 10000
        self.frequency_values = []
        self.debug = False
        self.tested_successfully = False
        # Make a little communication test and report on error
        # Create a TCP/IP socket
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.host_listening_port) # electrochem-m15 '172.31.46.15'
        try:
            test_sock.connect(server_address)
        except Exception:
            print "No communication with Gamry-Server possible. Is gamry_server.py-Program running in the console of the Windows machine? Remote-License activated? Or it might be used by someone else. Don't forget to establish connection before Gamry will be used!"
        # Set up the experiment
        test_string = "TES"
        if self.query(test_sock,test_string):
            print "Communication with Gamry-Server is working. Device is currently free..."
            self.tested_successfully = True
        else:
            print "No communication with Gamry-Server possible. Is gamry_server.py-Program running in the console of the Windows machine? Remote-License activated? Or it might be used by someone else. Don't forget to establish connection before Gamry will be used!"
        test_sock.close()
        
    def test_if_connected(self):
        # Make connection to gamry-server running on windows with gamry_server.py daemon in background
        # Create a TCP/IP socket
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.host_listening_port) # electrochem-m15 '172.31.46.15'
        test_sock.connect(server_address)
        # Set up the experiment
        test_string = "TES"
        if self.query(test_sock,test_string):
            print "Communication with Gamry-Server is working. Device is currently free..."
            self.tested_successfully = True
        else:
            print "Currently no communication with Gamry-Server possible. Is the gamry_server.py-Program running in the console of the Windows machine? Or it might be used by someone else. Don't forget to establish connection before Gamry will be used!"
        test_sock.close()
        return
        
    def get_id(self):
        return "Gamry_R600"
        
    def is_ready(self):
        return self.tested_successfully
        
    def create_impedance_object(self):
        # Make connection to gamry-server running on windows with gamry_server.py daemon in background
        # Create a TCP/IP socket
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.host_listening_port) # electrochem-m15 '172.31.46.15'
        test_sock.connect(server_address)
        # Set up the experiment
        command_string = "CIO,"+str(self.which)+","+str(self.mode)
        if not self.query(test_sock,command_string):
            print "Could not send command to create impedance object!"
        test_sock.close()
        return
        

    def setup_impedance_measurement(self, cycle_min=5, cycle_max=10, speed=1, zmod=1000000, bias=0):
        # Create a TCP/IP socket
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.host_listening_port) # electrochem-m15 '172.31.46.15'
        test_sock.connect(server_address)
        # Set up the experiment
        command_string = "SIM,"+str(cycle_min)+","+str(cycle_max)+","+str(speed)+","+str(zmod)+","+str(bias)
        if not self.query(test_sock,command_string):
            print "Could not send command to setup impedance measurement!"
        test_sock.close()
        return
        
    def perform_impedance_measurement(self, start_frequency, end_frequency, amplitude, num_points_per_decade=10):
        if start_frequency >= 1:
            start_frequency = int(start_frequency)
        if end_frequency >= 1:
            end_frequency = int(end_frequency)
        # Create a TCP/IP socket
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.host_listening_port) # electrochem-m15 '172.31.46.15'
        test_sock.connect(server_address)
        command_string = "PIM,"+str(start_frequency)+","+str(end_frequency)+","+str(int(amplitude*1000))+","+str(int(num_points_per_decade))
        if not self.query(test_sock,command_string):
            print "Could not send command to perform impedance measurement!"
            return
        # Get the specific frequencies which will be scanned
        # IMPORTANT: If you change this, you also have to do so on the server-script
        # Filter out line frequency 50Hz 100Hz and 200Hz afterwards
        frequency_values_generated = np.logspace(np.log10(start_frequency),np.log10(end_frequency),int(num_points_per_decade)*np.log10(end_frequency/start_frequency)) 
        frequency_values_without_50Hz = [float(i+4.5) if np.absolute(i-50)<1.0 else i for i in frequency_values_generated]
        frequency_values_without_100Hz = [float(i+2.5) if np.absolute(i-100)<1.0 else i for i in frequency_values_without_50Hz]
        frequency_values_without_200Hz = [float(i+1.5) if np.absolute(i-200)<0.8 else i for i in frequency_values_without_100Hz]
        self.frequency_values = frequency_values_without_200Hz
        test_sock.close()
        return
        
    def get_number_of_points_measured(self):
        # Create a TCP/IP socket
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.host_listening_port) # electrochem-m15 '172.31.46.15'
        try:
            test_sock.connect(server_address)
            result = self.query(test_sock,"GNP")
        except Exception:
            result = ''
            pass
        if not result:
            result = 0 # if no answer and device busy
        test_sock.close()
        return int(result)

    def get_nyquist_data(self):
        # Create a TCP/IP socket
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.host_listening_port) # electrochem-m15 '172.31.46.15'
        test_sock.connect(server_address)
        result = self.query(test_sock,"GND",10)
        try:
            data_with_duplicates = [[float(y) for y in x.split(',')] for x in result.split('|')]
        except Exception:
            return [[],[]]
        # Get rid of doublettes. This funny device sometimes adds values twice
        row1 = self.remove_duplicates(data_with_duplicates[0])
        row2 = self.remove_duplicates(data_with_duplicates[1])
        test_sock.close()
        return [row1,row2]
        
    def get_bode_data(self):
        # Create a TCP/IP socket
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.host_listening_port) # electrochem-m15 '172.31.46.15'
        test_sock.connect(server_address)
        result = self.query(test_sock,"GBD",10)
        try:
            data_with_duplicates = [[float(y) for y in x.split(',')] for x in result.split('|')]
        except Exception:
            return [[],[]]
        # Get rid of doublettes. This funny device sometimes adds values twice
        row1 = self.remove_duplicates(data_with_duplicates[0])
        row2 = self.remove_duplicates(data_with_duplicates[1])
        test_sock.close()
        return [row1,row2]
        
    def remove_duplicates(self,seqence): 
        # order preserving
        checked = []
        for e in seqence:
            if e not in checked:
                checked.append(e)
        return checked
        
    def query(self,sock,message,timeout=2):
        if self.debug:
            print "Just sent: ", message
        sock.sendall(message)
        a = self.receive_command(sock,timeout)
        if self.debug:
            print "Just received: ", a
        is_boolean_answer = False
        if len(a) is 2:
            is_boolean_answer = True
        if a[0:2] == "OK" and is_boolean_answer:
            return True
        if a[0:2] == "ER" and is_boolean_answer: # means error occured
            return False
        return a[2:]
        
    def receive_command(self,sock,timeout=2):
        #make socket non blocking
        sock.setblocking(0)
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
                data = sock.recv(8192)
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
        
    def flush(self): # command between two measurements in arrhenius program
        # Create a TCP/IP socket
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.host_listening_port) # electrochem-m15 '172.31.46.15'
        test_sock.connect(server_address)
        self.query(test_sock,"FLU")
        test_sock.close()
        return
        
    def unflush(self): # command between two measurements in arrhenius program
        # Create a TCP/IP socket
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.host_listening_port) # electrochem-m15 '172.31.46.15'
        test_sock.connect(server_address)
        self.query(test_sock,"UFL")
        test_sock.close()
        return
        
    def close(self):
        # Create a TCP/IP socket
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.host_listening_port) # electrochem-m15 '172.31.46.15'
        test_sock.connect(server_address)
        self.query(test_sock,"DEL")
        test_sock.close()
        return

    def __exit__(self):
        try:
            self.close()
        except Exception:
            pass
        return
        
    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
        return
        
# Little demo to show how the class can be used to acquire a simple impedance measurement
if __name__ == "__main__":
    gamry = gamry_R600()
    gamry.debug = True
    gamry.create_impedance_object()
    time.sleep(15) # This is very important. Gamry needs at least 10 sec to startup. Do NOT continue before this is done
    gamry.setup_impedance_measurement()
    time.sleep(5)
    gamry.perform_impedance_measurement(1, 10, 0.05, 1)
    print gamry.get_nyquist_data()
    print gamry.get_bode_data()
    gamry.close()
