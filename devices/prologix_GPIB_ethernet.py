#!/usr/bin/python
#
# Software License Agreement (BSD License)
#
# Copyright (c) 2008, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#


##\author Derek King
##\brief Interface to Prologix GPIB-Ethernet controller

"""
Interactive interface to LXI device.

Usage: %(progname)s [-h] <address>

Options:
  address : Use address to connect to LXI device. Address can be IPv4 address or hostname.
  -h : show this help

Example:
  %(progname)s 10.0.1.197

Interative Usage:
  Type SCPI command at prompt '>'.  Pressing enter will send command to device.
  To read SCPI output from previous command, don't type anything and just press enter.

  Note : SCPI = Standard Commands for Programmable Instruments

Interactive Example : (Reading device identification string)
  > *idn? <enter>
  > << ENTER >>
  Agilent Technologies,34410A,MY47007427,2.35-2.35-0.09-46-09

Interactive Example : (Voltage measurement from DMM)
  > meas:volt:dc?
  > << ENTER >>
  -2.12071654E-04
"""

import traceback
import socket
import sys
import re

def usage(progname):
  print __doc__ % vars()


# Interface to LXI device. 
class prologix_ethernet:
  def __init__(self, address):
    try :
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      port = 1234 #5025
      sock.connect((address, port))
    except socket.error :
      raise RuntimeError("Error making connection to prologix_ethernet device with address '%s'" %  address)
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
    self._sock.sendall(line)
        
  def close(self):
    self._sock.close()
    return

def main(argv):
    progname = argv[0]
    import getopt
    optlist,argv = getopt.gnu_getopt(argv[1:], "h");

    dev = None
    for opt,arg in optlist:
        if (opt == "-h"):
            usage(progname)
            return 0
        else :
            print "Internal error : opt = ", opt
            return 2

    if len(argv) != 1:
      usage(progname)
      return 1

    address = argv[0]
    print "Connecting to prologix_ethernet device using network address %s" % address
    dev = prologix_ethernet(address) 

    import readline
    line = raw_input("> ")
    while True:
        if line:
            dev.write(line+"\n")
        else:
          result = dev.read()
          if result != None:
            print result
          else:
            print '<<< NO RESPONSE >>>'
        line = raw_input("> ")


if __name__ == '__main__':
    sys.exit(main(sys.argv))
