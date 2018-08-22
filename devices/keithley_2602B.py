#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Pure python VXI-11 client
# Copyright (c) 2011 Michael Walle
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

import logging
import rpc
import time
import numpy as np

DEVICE_CORE_PROG = 0x0607af
DEVICE_CORE_VERS = 1
DEVICE_ASYNC_PROG = 0x0607b0
DEVICE_ASYNC_VERS = 1
DEVICE_INTR_PROG = 0x0607b1
DEVICE_INTR_VERS = 1

CREATE_LINK = 10
DEVICE_WRITE = 11
DEVICE_READ = 12
DEVICE_READSTB = 13
DEVICE_TRIGGER = 14
DEVICE_CLEAR = 15
DEVICE_REMOTE = 16
DEVICE_LOCAL = 17
DEVICE_LOCK = 18
DEVICE_UNLOCK = 19
DEVICE_ENABLE_SRQ = 20
DEVICE_DOCMD = 22
DESTROY_LINK = 23
CREATE_INTR_CHAN = 25
DESTROY_INTR_CHAN = 26

ERR_NO_ERROR = 0
ERR_INVALID_LINK_IDENTIFIER = 4
ERR_PARAMETER_ERROR = 5
ERR_DEVICE_LOCKED_BY_ANOTHER_LINK = 11
ERR_IO_TIMEOUT = 15
ERR_IO_ERROR = 17
ERR_ABORT = 23

OP_FLAG_WAIT_BLOCK = 1
OP_FLAG_END = 8
OP_FLAG_TERMCHAR_SET = 128

REASON_REQCNT = 1
REASON_CHR = 2
REASON_END = 4

def chunks(d, n):
    for i in xrange(0, len(d), n):
        yield d[i:i+n]

log = logging.getLogger(__name__)

class Vxi11Packer(rpc.RpcPacker):
    def pack_device_link(self, link):
        self.pack_int(link)

    def pack_create_link_parms(self, params):
        id, lock_device, lock_timeout, device = params
        self.pack_int(id)
        self.pack_bool(lock_device)
        self.pack_uint(lock_timeout)
        self.pack_string(device)

    def pack_device_write_parms(self, params):
        link, io_timeout, lock_timeout, flags, data = params
        self.pack_device_link(link)
        self.pack_uint(io_timeout)
        self.pack_uint(lock_timeout)
        self.pack_int(flags)
        self.pack_opaque(data)

    def pack_device_read_parms(self, params):
        link, request_size, io_timeout, lock_timeout, flags, term_char = params
        self.pack_device_link(link)
        self.pack_uint(request_size)
        self.pack_uint(io_timeout)
        self.pack_uint(lock_timeout)
        self.pack_int(flags)
        self.pack_int(term_char)


class Vxi11Unpacker(rpc.RpcUnpacker):
    def unpack_device_link(self):
        return self.unpack_int()

    def unpack_device_error(self):
        return self.unpack_int()

    def unpack_create_link_resp(self):
        error = self.unpack_int()
        link = self.unpack_device_link()
        abort_port = self.unpack_uint()
        max_recv_size = self.unpack_uint()
        return error, link, abort_port, max_recv_size

    def unpack_device_write_resp(self):
        error = self.unpack_int()
        size = self.unpack_uint()
        return error, size

    def unpack_device_read_resp(self):
        error = self.unpack_int()
        reason = self.unpack_int()
        data = self.unpack_opaque()
        return error, reason, data


class Vxi11Client(rpc.RawTCPClient):
    def __init__(self, host):
        self.packer = Vxi11Packer()
        self.unpacker = Vxi11Unpacker('')
        pmap = rpc.TCPPortMapperClient(host)
        mapping = (DEVICE_CORE_PROG, DEVICE_CORE_VERS, rpc.IPPROTO_TCP, 0)
        port = pmap.get_port(mapping)
        pmap.close()
        log.debug('VXI-11 uses port %d', port)

        rpc.RawTCPClient.__init__(self, host, DEVICE_CORE_PROG,
                DEVICE_CORE_VERS, port)

    def create_link(self, id, lock_device, lock_timeout, name):
        params = (id, lock_device, lock_timeout, name)
        return self.make_call(CREATE_LINK, params,
                self.packer.pack_create_link_parms,
                self.unpacker.unpack_create_link_resp)

    def device_write(self, link, io_timeout, lock_timeout, flags, data):
        params = (link, io_timeout, lock_timeout, flags, data)
        return self.make_call(DEVICE_WRITE, params,
                self.packer.pack_device_write_parms,
                self.unpacker.unpack_device_write_resp)

    def device_read(self, link, request_size, io_timeout, lock_timeout, flags,
            term_char):
        params = (link, request_size, io_timeout, lock_timeout, flags,
                term_char)
        return self.make_call(DEVICE_READ, params,
                self.packer.pack_device_read_parms,
                self.unpacker.unpack_device_read_resp)

    def destroy_link(self, link):
        return self.make_call(DESTROY_LINK, link,
                self.packer.pack_device_link,
                self.unpacker.unpack_device_error)


class Vxi11Error(Exception):
    pass


class keithley_2602B:
    def __init__(self, host, channel="A", name=None, client_id=None):
        self.host = host
        self.io_timeout = 2
        self.lock_timeout = 2
        self.vxi11_client = Vxi11Client(host)
        self.client_id = client_id
        self.nplc_a = 1
        self.nplc_b = 1
        self.what_is_measured = ""
        maxval = max([self.nplc_a,self.nplc_b])
        self.nplc_delay_time = maxval/50.0+self.io_timeout*0.001+self.lock_timeout*0.001+0.01
        self.maximum_current_allowed = 3 # Ampere
        self.maximum_voltage_allowed = 40 # Volts
        self.channel_in_use = channel
        self.channel_A_done = False # internally to make dual-channel cycling easier. If True, the device does not react on any commands for that channel anymore
        self.channel_B_done = False # internally to make dual-channel cycling easier. If True, the device does not react on any commands for that channel anymore
        if name is None:
            self.name = 'inst0'
        else:
            self.name = name
        #self.open()
        
    def open(self):
        log.info('Opening connection to %s', self.host)

        # If no client id was given, get it from the Vxi11 object
        client_id = self.client_id
        if client_id is None:
            client_id = id(self) & 0x7fffffff
        error, link_id, abort_port, max_recv_size = \
                self.vxi11_client.create_link(client_id, 0, 0, self.name)

        if error != 0:
            raise RuntimeError('TBD. This means the internal firmware of the device hangs. Turn the device off and on again and everything should work again!')

        # Some devices seem to return -1, but max_recv_size is unsigned.
        # As a workaround we set an upper boundary of 16k
        max_recv_size = min(max_recv_size, 16*1024)

        log.debug('link id is %d, max_recv_size is %d',
                link_id, max_recv_size)

        self.link_id = link_id
        self.max_recv_size = max_recv_size

    def close(self):
        log.info('Close connection to %s', self.host)
        self.vxi11_client.destroy_link(self.link_id)
        self.vxi11_client.close()

    def write(self, message):
        #print message
        #time.sleep(2)
        log.debug('Writing %d bytes (%s)', len(message), message)
        io_timeout = self.io_timeout * 1000       # in ms
        lock_timeout = self.lock_timeout * 1000   # in ms
        flags = 0
        # split into chunks
        msg_chunks = list(chunks(message, self.max_recv_size))
        for (n,chunk) in enumerate(msg_chunks):
            if n == len(msg_chunks)-1:
                flags = OP_FLAG_END
            else:
                flags = 0
            error, size = self.vxi11_client.device_write(self.link_id,
                    io_timeout, lock_timeout, flags, chunk)
            if error != ERR_NO_ERROR:
                raise Vxi11Error(error)
            assert size == len(chunk)

    def ask(self, message):
        self.write(message)
        return self.read()

    def read(self):
        read_size = self.max_recv_size
        io_timeout = self.io_timeout * 1000       # in ms
        lock_timeout = self.lock_timeout * 1000   # in ms
        reason = 0
        flags = 0
        term_char = 0
        data_list = list()
        while reason == 0:
            error, reason, data = self.vxi11_client.device_read(self.link_id,
                    read_size, io_timeout, lock_timeout, flags, term_char)
            if error != ERR_NO_ERROR:
                raise Vxi11Error(error)
            data_list.append(data)
            log.debug('Received %d bytes', len(data))

            if reason & REASON_REQCNT:
                reason &= ~REASON_REQCNT

        return ''.join(data_list)

    def get_id(self):
        return "keithley_2602B"
        
    def __exit__(self):
        try:
            self.turn_output_off()
            self.close()
        except Exception:
            pass
        return
        
    def __del__(self):
        try:
            self.turn_output_off()
            self.close()
        except Exception:
            pass
        return
        
    def set_voltage(self,voltage):
        if self.channel_in_use is "A":
            self.write("smua.source.levelv = "+str(float(voltage)))
        elif self.channel_in_use is "B":
            self.write("smub.source.levelv = "+str(float(voltage)))
        return
        
    def set_voltage_range(self): # needed for compatibility with keithley_6517B
        return
        
    def set_compliance_current(self,cc):
        if self.channel_in_use is "A":
            if cc is 0 or cc is None:
                self.write("smua.source.limiti = "+str(self.maximum_current_allowed))
            else:
                self.write("smua.source.limiti = "+str(cc))
        elif self.channel_in_use is "B":
            if cc is 0 or cc is None:
                self.write("smub.source.limiti = "+str(self.maximum_current_allowed))
            else:
                self.write("smub.source.limiti = "+str(cc))
        return
        
    def set_compliance_voltage(self,cc):
        if self.channel_in_use is "A":
            if cc is 0 or cc is None:
                self.write("smua.source.limitv = "+str(self.maximum_voltage_allowed))
            else:
                self.write("smua.source.limitv = "+str(cc))
        elif self.channel_in_use is "B":
            if cc is 0 or cc is None:
                self.write("smub.source.limitv = "+str(self.maximum_voltage_allowed))
            else:
                self.write("smub.source.limitv = "+str(cc))
        return

    def set_current(self,current):
        if self.channel_in_use is "A":
            self.write("smua.source.leveli = "+str(float(current)))
        elif self.channel_in_use is "B":
            self.write("smub.source.leveli = "+str(float(current)))
        return
        
    def set_nplc(self,nplc):
        if self.channel_in_use is "A":
            self.write("smua.measure.nplc = "+str(float(nplc)))
            self.nplc_a = nplc
            maxval = max([self.nplc_a,self.nplc_b])
            self.nplc_delay_time = maxval/50.0+self.io_timeout*0.001+self.lock_timeout*0.001+0.01
        elif self.channel_in_use is "B":
            self.write("smub.measure.nplc = "+str(float(nplc)))
            self.nplc_b = nplc
            maxval = max([self.nplc_a,self.nplc_b])
            self.nplc_delay_time = maxval/50.0+self.io_timeout*0.001+self.lock_timeout*0.001+0.01
        return
        
    def get_current(self,delay=0.01):
        if delay is not 0:
            self.write("delay("+str(delay)+")")
        if self.channel_in_use is "A":
            val = self.ask("print(smua.measure.i())")
        elif self.channel_in_use is "B":
            val = self.ask("print(smub.measure.i())")
        if float(val) > 1e30: # overflow
            return 0.0
        return float(val)
        
    def get_voltage(self,delay=0.01):
        if delay is not 0:
            self.write("delay("+str(delay)+")")
        if self.channel_in_use is "A":
            val = self.ask("print(smua.measure.v())")
        elif self.channel_in_use is "B":
            val = self.ask("print(smub.measure.v())")
        if float(val) > 1e30: # overflow
            return 0.0
        return float(val)
        
    def get_value(self,which=None): # needed for compatibility with keithley_6517B
        if self.what_is_measured is "current":
            A = [self.get_current(),time.time()]
        elif self.what_is_measured is "voltage":
            A = [self.get_voltage(),time.time()]
        return A
        
    def set_voltage_range(self,voltage): # needed for compatibility with keithley_6517B
        return
        
    def setup_current_measurement(self,nplc=1):
        self.what_is_measured = "current"
        if self.channel_in_use is "A":
            self.write("display.screen = display.SMUA")
            self.write("display.smua.measure.func = display.MEASURE_DCAMPS")
            self.write("smua.source.func = smua.OUTPUT_DCVOLTS")
            self.write("smua.source.autorangev = smua.AUTORANGE_ON")
            self.write("smua.source.autorangei = smua.AUTORANGE_ON")
            self.set_nplc(nplc)
            self.write("smua.measure.autozero = smua.AUTOZERO_AUTO")
            #self.write("smua.source.limiti = 0.1")
            #self.write("smua.source.rangei = 0.1")
        elif self.channel_in_use is "B":
            self.write("display.screen = display.SMUB")
            self.write("display.smub.measure.func = display.MEASURE_DCAMPS")
            self.write("smub.source.func = smub.OUTPUT_DCVOLTS")
            self.write("smub.source.autorangev = smub.AUTORANGE_ON")
            self.write("smub.source.autorangei = smub.AUTORANGE_ON")
            self.set_nplc(nplc)
            self.write("smub.measure.autozero = smub.AUTOZERO_AUTO")
            #self.write("smub.source.limiti = 0.1")
            #self.write("smub.source.rangei = 0.1")
        return
        
    def setup_voltage_measurement(self,nplc=1):
        self.what_is_measured = "voltage"
        if self.channel_in_use is "A":
            self.write("display.screen = display.SMUA")
            self.write("display.smua.measure.func = display.MEASURE_DCVOLTS")
            self.write("smua.source.func = smua.OUTPUT_DCAMPS")
            self.write("smua.source.autorangev = smua.AUTORANGE_ON")
            self.write("smua.source.autorangei = smua.AUTORANGE_ON")
            self.set_nplc(nplc)
            self.write("smua.measure.autozero = smua.AUTOZERO_AUTO")
            #self.write("smua.source.limiti = 0.1")
            #self.write("smua.source.rangei = 0.1")
        elif self.channel_in_use is "B":
            self.write("display.screen = display.SMUB")
            self.write("display.smub.measure.func = display.MEASURE_DCVOLTS")
            self.write("smub.source.func = smub.OUTPUT_DCAMPS")
            self.write("smub.source.autorangev = smub.AUTORANGE_ON")
            self.write("smub.source.autorangei = smub.AUTORANGE_ON")
            self.set_nplc(nplc)
            self.write("smub.measure.autozero = smub.AUTOZERO_AUTO")
            #self.write("smub.source.limiti = 0.1")
            #self.write("smub.source.rangei = 0.1")
        return
        
    def turn_output_on(self):
        if self.channel_in_use is "A":
            self.write("smua.source.output = smua.OUTPUT_ON")
        elif self.channel_in_use is "B":
            self.write("smub.source.output = smub.OUTPUT_ON")
            
    def turn_output_off(self):
        if self.channel_in_use is "A":
            self.write("smua.source.output = smua.OUTPUT_OFF")
        elif self.channel_in_use is "B":
            self.write("smub.source.output = smub.OUTPUT_OFF")
            
    def set_offmode_high_impedance(self): # Relay opens. Can wear out and degrade the relay if heavily used
        if self.channel_in_use is "A":
            self.write("smua.source.offmode = smua.OUTPUT_HIGH_Z")
        elif self.channel_in_use is "B":
            self.write("smub.source.offmode = smub.OUTPUT_HIGH_Z")
            
    def set_offmode_normal(self): # default value. source 0V 0A. Relay stays closed. There can be leackage current on each channel
        if self.channel_in_use is "A":
            self.write("smua.source.offmode = smua.OUTPUT_NORMAL")
        elif self.channel_in_use is "B":
            self.write("smub.source.offmode = smub.OUTPUT_NORMAL")
            
    def turn_output_off_high_impedance(self): # Relay opens. Can wear out and degrade the relay if heavily used
        if self.channel_in_use is "A":
            self.write("smua.source.output = smua.OUTPUT_HIGH_Z")
        elif self.channel_in_use is "B":
            self.write("smub.source.output = smub.OUTPUT_HIGH_Z")
            
    def reset(self):
        self.write("localnode.prompts = 0")
        self.write("reset()")
        self.write("display.clear()")
        
    def trigger(self):
        self.write("*TRG")
        
    def init(self): # needed for compatibility with keithley_6517B
        return

       
# Little demo to show how the class can be used to acquire a simple measurement
if __name__ == "__main__":
   
    ip_address = "192.168.1.34"
    keithley_2602B = keithley_2602B(ip_address)
    keithley_2602B.open()
    keithley_2602B.reset()
    keithley_2602B.setup_current_measurement()
    keithley_2602B.set_voltage(0.0042)
    keithley_2602B.turn_output_on()
    keithley_2602B.init()
    time.sleep(2) # wait 2 sec for the device to become ready
    result = []
    for i in range(10):
        a = keithley_2602B.get_value()
        print "Current is: ",a[0]
        result.append(a)
    keithley_2602B.turn_output_off()
    keithley_2602B.close()
    print result
