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
import time
from devices.prologix_GPIB_ethernet import prologix_ethernet

def write_to_dev(string):
   #print "Just wrote: ",string
   device.write(string + "\n")
   return

def read_from_dev():
   write_to_dev("++read eoi\n")
   return device.read()
        
def query(string):
   write_to_dev(string)
   time.sleep(1)
   return read_from_dev()
        
device = prologix_ethernet("192.168.1.33")
#print 'connecting'

try:
    write_to_dev("++mode 0")
    write_to_dev("++eot_enable 1")
    write_to_dev("++lon 1")
    while True:
        data = read_from_dev()
        print data

finally:
    print 'closing socket'
    device.close()