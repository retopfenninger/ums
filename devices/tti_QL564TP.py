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

# device driver for the Lab power supply from TTi


import traceback
import socket
import sys
import re
import time

# Interface to LXI device. 
class LXIDevice:
  def __init__(self, address):
    try :
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      port = 9221 #normally: 5025
      sock.connect((address, port))
    except socket.error :
      raise RuntimeError("Error making connection to LXI device with address '%s'" %  address)
    self._sock = sock
    self._timeout = 0.5
    msg = self._flush()
    if msg:
      print "Warning, flushed : ", msg

  def settimeout(self, timeout):
    """ Set read timeout in seconds """
    self._sock.settimeout(timeout)
    self._timeout = timeout
  
  def _flush(self):
    """ Clear any read buffers out """
    self._sock.settimeout(0.1)
    line = self.read()
    result = ""
    while line != None:
      result += line
      line = self._read()
    self._sock.settimeout(self._timeout)
    return result

  def read(self):
    sock = self._sock
    msg = ""
    try:
      while True:
        msg += sock.recv(1024)
        end = msg.find("\n")
        if end == len(msg)-1:
          return msg
        elif end != -1:
          print "Warning, dropping %d byte tail of message. Tail='%s'"%(len(msg)-end, msg[end:])
          return msg[0:end-1]
    except socket.timeout:
      if len(msg) > 0:
        raise RuntimeError("Got timeout after receiving partial result : %s" % msg)
      else:
        return None

  def write(self, line):
    self._sock.sendall(line+'\n')
    
  def close(self):
    self._sock.close()
        
        
        
class tti_QL564TP:
    def __init__(self, host):
        self.host = host
        self.dev = LXIDevice(host)

    def close(self):
        self.dev.close()
        
    def write_to_dev(self, string):
        #print "Just wrote: ",string
        self.dev.write(string)
        time.sleep(0.6)
        return
        
    def get_id(self):
        return "tti_QL564TP"
        
    def set_voltage(self,voltage,output):
        self.write_to_dev("V"+str(int(output))+" "+str(float(voltage)))
        
    def set_current(self,current,output):
        self.write_to_dev("I"+str(int(output))+" "+str(float(current)))        
        
    def turn_output_on(self,output):
        self.write_to_dev("OP"+str(int(output))+" 1")
        
    def turn_output_off(self,output):
        self.write_to_dev("OP"+str(int(output))+" 0")
        
    def turn_all_output_off(self):
        self.write_to_dev("OPALL 0")
        
    def __exit__(self):
        try:
            self.turn_all_output_off()
            self.close()
        except Exception:
            pass
        return
        
    def __del__(self):
        try:
            self.turn_all_output_off()
            self.close()
        except Exception:
            pass
        return
       
       
# Little demo to show how the class can be used to acquire a simple task
if __name__ == "__main__":
   
    ip_address = "192.168.1.33"
    mypowersupply = tti_QL564TP(ip_address)
    mypowersupply.set_voltage(11.1,1)
    mypowersupply.set_current(0.5,1)
    mypowersupply.turn_output_on(1)
    print "Power supply has just been turned on! :-)"
    time.sleep(5)
    mypowersupply.turn_output_off(1)
    print "Power supply has just been turned off again! :-)"

