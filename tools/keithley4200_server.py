#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Unified measurement software UMS
# New measurement software for the electrochemical materials group, Prof. Jennifer Rupp
#
# Copyright (c) 2016 Reto Pfenninger, department of materials, D-MATL, ETH Zürich
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

# This is the server-side script which will run in background on the windows machine of the Keithley 4200-SCS
# It needs to be started in a separate command line

import socket
import sys
from keithley4200_device import keithley4200_device # the Keithley4200_device.py file needs to be in the same directory as this server-script
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
    def __init__(self): # class which handels all slow and long taking communication with keihtley in order to keep the program responsive over network
        self.keithley4200 = None
        self.number_of_points_measured = 0
        self.data = []
        self.pool = ThreadPool(processes=10)
        return
        
    def create_keithley4200_object(self):
        async_result = self.pool.apply_async(keithley4200_device)
        self.keithley4200 = async_result.get()
    
    def make_send_string(self,data_string):
        async_result = self.pool.apply_async(self.keithley4200.send_string,args=(data_string))
        return async_result.get()
        
    def make_get_number_of_points_measured(self):
        async_result = self.pool.apply_async(self.keithley4200.get_number_of_points_measured)
        self.number_of_points_measured = async_result.get()
        return
        
    def make_get_data(self):
        async_result = self.pool.apply_async(self.keithley4200.get_data)
        time.sleep(2)
        self.data = async_result.get()
        print "Got data",self.data
        return
        
    def close_keithley4200_object(self):
        try:
            self.keithley4200.interrupt = True
        except Exception:
            pass
        try:
            self.number_of_points_measured = 0
            self.data = []
            self.keithley4200.close()
            del self.keithley4200
        except Exception:
            pass
        self.keithley4200 = None
        return
        
    def __exit__(self):
        try:
            self.close_keithley4200_object()
        except Exception:
            pass
        return
        
    def __del__(self):
        try:
            self.close_keithley4200_object()
        except Exception:
            pass
        return

# ---------------------- here the main class starts --------------------------------

class daemon_keithley_server(object):
    def __init__(self):
        # Some crazy Windows shit with threads in the next lines
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to the port
        self.server_address = ('172.31.27.122', 10000) # the address of the Keithley over the network interface
        print >>sys.stderr, 'Keithley 4200-SCS UMS server starting up on %s port %s' % self.server_address
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
                print "Keithley object is of type: ",type(self.background_worker.keithley4200)
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
                    elif data == "create_keithley4200_object": # Means create_impedance_object
                        print >>sys.stderr, 'got create_keithley4200_object'
                        if self.last_received_command is "DEL" or self.last_received_command is "TES": # You can only do this if you don't have a device up
                            self.last_received_command = "create_keithley4200_object"
                            connection.sendall("OK")
                            Thread(target=self.background_worker.create_keithley4200_object()).start()
                        else:
                            connection.sendall("ER")
                    elif data[0:3] == "GNP": # Means get_number_of_points_measured
                        print >>sys.stderr, 'got GNP (get_number_of_points_measured)'
                        self.last_received_command = "GNP"
                        Thread(target=self.background_worker.make_get_number_of_points_measured).start() # New thread
                        connection.sendall("OK"+str(self.background_worker.number_of_points_measured))
                        print >>sys.stderr, 'sent back GNP number_of_points_measured='+str(self.background_worker.number_of_points_measured)
                    elif data == "get_data":
                        print >>sys.stderr, 'got get_data'
                        self.last_received_command = "get_data"
                        Thread(target=self.background_worker.make_get_data).start() # New thread
                        time.sleep(5)
                        n = "|".join(",".join(map(str,l)) for l in self.background_worker.data)
                        print "sending...","OK"+str(n)
                        connection.sendall("OK"+str(n))
                    elif data[0:3] == "DEL": # Means delete current measurement and reset
                        print >>sys.stderr, 'got DEL (will delete current measurement and reset)'
                        self.last_received_command = "DEL"
                        connection.sendall("OK")
                        Thread(target=self.background_worker.close_keithley4200_object).start() # New thread
                    else:
                        print >>sys.stderr, 'got custom string: ',data
                        self.last_received_command = "string"
                        connection.sendall("OK")
                        Thread(target=self.background_worker.make_send_string(data)).start()
                    request_processed = True
            finally:
                # Clean up the connection
                connection.close()

    def close(self):
        self.stop_daemon = True
        try:
            self.background_worker.close_keithley4200_object()
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

main_prog = daemon_keithley_server()
main_prog.run_it()

        
        