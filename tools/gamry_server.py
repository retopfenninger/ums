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

# This is the server-side script which will run in background on a windows machine where the Gamry-Software
# plus the AC-API license is installed

import socket
import sys
from gamry_R600_device import gamry_R600_device # the gamry_R600_device.py file needs to be in the same directory as this server-script
from threading import Thread
from multiprocessing.pool import ThreadPool
import time

def receive_command(connection,timeout=2):
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

class background_worker(object):
    def __init__(self): # class which handels all slow and long taking communication with gamry in order to keep the program responsive over network
        self.gamry = None
        self.number_of_points_measured = 0
        self.nyquist_data = []
        self.bode_data = []
        self.pool = ThreadPool(processes=10)
        return
        
    def create_gamry_object(self,mode="Potentiostat",which=0):
        async_result = self.pool.apply_async(gamry_R600_device, args=(mode,which))
        self.gamry = async_result.get()  # takes at least 10 seconds!!! Plan this in when you design client-side program
        
    def make_setup_impedance_measurement(self,cycle_min,cycle_max,speed,zmod,bias):
        async_result = self.pool.apply_async(self.gamry.setup_impedance_measurement, args=(cycle_min,cycle_max,speed,zmod,bias))
        return async_result.wait()
    
    def make_perform_impedance_measurement(self,start_frequency,end_frequency,amplitude,num_points_per_decade):
        async_result = self.pool.apply_async(self.gamry.perform_impedance_measurement, args=(start_frequency,end_frequency,amplitude,num_points_per_decade))
        return async_result.wait()
        
    def make_get_number_of_points_measured(self):
        async_result = self.pool.apply_async(self.gamry.get_number_of_points_measured)
        self.number_of_points_measured = async_result.get()
        return
        
    def make_get_nyquist_data(self):
        async_result = self.pool.apply_async(self.gamry.get_nyquist_data)
        time.sleep(2)
        self.nyquist_data = async_result.get()
        print "Got nyquist_data",self.nyquist_data
        return
        
    def make_get_bode_data(self):
        async_result = self.pool.apply_async(self.gamry.get_bode_data)
        time.sleep(2)
        self.bode_data = async_result.get()
        print "Got bode_data",self.bode_data
        return
        
    def close_gamry_object(self):
        try:
            self.gamry.interrupt = True
        except Exception:
            pass
        try:
            self.flush_gamry_object()
            time.sleep(2)
            self.unflush_gamry_object()
            time.sleep(2)
            self.gamry.close()
            del self.gamry
        except Exception:
            pass
        self.gamry = None
        return
        
    def flush_gamry_object(self):
        try:
            self.gamry.interrupt = True
        except Exception:
            pass
        try:
            self.number_of_points_measured = 0
            self.nyquist_data = []
            self.bode_data = []
            self.gamry.flush()
        except Exception:
            pass
        return
        
    def unflush_gamry_object(self):
        try:
            self.gamry.interrupt = False
        except Exception:
            pass
        try:
            self.gamry.unflush()
        except Exception:
            pass
        return
        
    def __exit__(self):
        try:
            self.close_gamry_object()
        except Exception:
            pass
        return
        
    def __del__(self):
        try:
            self.close_gamry_object()
        except Exception:
            pass
        return

# ---------------------- here the main class starts --------------------------------

class daemon_gamry_server(object):
    def __init__(self):
        # Some crazy Windows shit with threads in the next lines
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to the port
        self.server_address = ('172.31.46.15', 10000) # electrochem-m15
        print >>sys.stderr, 'starting up on %s port %s' % self.server_address
        self.sock.bind(self.server_address)
        # Listen for incoming connections
        self.sock.listen(1)
        self.background_worker = background_worker()
        self.stop_daemon = False
        self.last_received_command = "NEW"
        
    def run_it(self):
        while not self.stop_daemon: # This is a daemon, will run forever
            # Wait for a connection
            connection, client_address = self.sock.accept()
            request_processed = False
            try:
                print >>sys.stderr, 'connection from', client_address
                print "Gamry object is of type: ",type(self.background_worker.gamry)
                # Receive the data
                while not request_processed:
                    data = receive_command(connection)
                    print >>sys.stderr, 'received "%s"' % data
                    if data[0:3] == "TES": # Means communication test was triggered
                        print >>sys.stderr, 'got TES (communication test)'
                        if self.last_received_command is "DEL" or self.last_received_command is "NEW": # You can only use it if nobody else uses it
                            self.last_received_command = "TES"
                            connection.sendall("OK")
                        else:
                            connection.sendall("ER")
                    elif data[0:3] == "CIO": # Means create_impedance_object
                        print >>sys.stderr, 'got CIO (create_impedance_object)'
                        if self.last_received_command is "DEL" or self.last_received_command is "TES": # You can only do this if you don't have a gamry up
                            self.last_received_command = "CIO"
                            connection.sendall("OK")
                            command_string = data.split(",")
                            which = int(command_string[1])
                            mode = str(command_string[2])
                            Thread(target=self.background_worker.create_gamry_object(mode,which)).start()
                        else:
                            connection.sendall("ER")
                    elif data[0:3] == "SIM": # Means setup_impedance_measurement
                        print >>sys.stderr, 'got SIM (setup_impedance_measurement)'
                        if self.last_received_command is "CIO": # You can only do this if you have a gamry up
                            self.last_received_command = "SIM"
                            connection.sendall("OK")
                            command_string = data.split(",")
                            cycle_min = int(command_string[1])
                            cycle_max = int(command_string[2])
                            speed = int(command_string[3])
                            zmod = int(command_string[4])
                            bias = float(command_string[5])
                            self.background_worker.make_setup_impedance_measurement(cycle_min,cycle_max,speed,zmod,bias)
                        else:
                            connection.sendall("ER")
                    elif data[0:3] == "PIM": # Means perform_impedance_measurement
                        print >>sys.stderr, 'got PIM (perform_impedance_measurement)'
                        if self.last_received_command is "SIM": # You can only do this if you setup the gamry first
                            self.last_received_command = "PIM"
                            connection.sendall("OK")
                            command_string = data.split(",")
                            start_frequency = float(command_string[1])
                            end_frequency = float(command_string[2])
                            amplitude = int(command_string[3])
                            num_points_per_decade = int(command_string[4])
                            self.background_worker.make_perform_impedance_measurement(start_frequency,end_frequency,amplitude,num_points_per_decade)
                        else:
                            connection.sendall("ER")
                    elif data[0:3] == "GNP": # Means get_number_of_points_measured
                        print >>sys.stderr, 'got GNP (get_number_of_points_measured)'
                        self.last_received_command = "GNP"
                        Thread(target=self.background_worker.make_get_number_of_points_measured).start() # New thread
                        connection.sendall("OK"+str(self.background_worker.number_of_points_measured))
                        print >>sys.stderr, 'sent back GNP number_of_points_measured='+str(self.background_worker.number_of_points_measured)
                    elif data[0:3] == "GND": # Means get_nyquist_data
                        print >>sys.stderr, 'got GND (get_nyquist_data)'
                        self.last_received_command = "GND"
                        Thread(target=self.background_worker.make_get_nyquist_data).start() # New thread
                        time.sleep(5)
                        n = "|".join(",".join(map(str,l)) for l in self.background_worker.nyquist_data)
                        print "sending...","OK"+str(n)
                        connection.sendall("OK"+str(n))
                    elif data[0:3] == "GBD": # Means get_bode_data
                        print >>sys.stderr, 'got GBD (get_bode_data)'
                        self.last_received_command = "GBD"
                        Thread(target=self.background_worker.make_get_bode_data).start() # New thread
                        time.sleep(5)
                        n = "|".join(",".join(map(str,l)) for l in self.background_worker.bode_data)
                        connection.sendall("OK"+str(n))
                    elif data[0:3] == "DEL": # Means delete current measurement and reset
                        print >>sys.stderr, 'got DEL (will delete current measurement and reset)'
                        self.last_received_command = "DEL"
                        connection.sendall("OK")
                        Thread(target=self.background_worker.close_gamry_object).start() # New thread
                    elif data[0:3] == "FLU": # Means flush and reset
                        print >>sys.stderr, 'got FLU (flush and reset)'
                        self.last_received_command = "CIO"
                        connection.sendall("OK")
                        Thread(target=self.background_worker.flush_gamry_object).start() # New thread
                    elif data[0:3] == "UFL": # Means unflush
                        print >>sys.stderr, 'got UFL (unflush)'
                        self.last_received_command = "CIO"
                        connection.sendall("OK")
                        Thread(target=self.background_worker.unflush_gamry_object).start() # New thread
                    request_processed = True
            finally:
                # Clean up the connection
                connection.close()

    def close(self):
        self.stop_daemon = True
        try:
            self.background_worker.close_gamry_object()
            del self.background_worker
        except Exception:
            pass
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

# ---------------------- here the main program starts --------------------------------
#pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
#pythoncom.CoInitialize()

main_prog = daemon_gamry_server()
main_prog.run_it()

        
        