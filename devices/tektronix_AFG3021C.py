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


class tektronix_AFG3021C:
    def __init__(self, host, name=None, client_id=None):
        self.host = host
        self.io_timeout = 2
        self.lock_timeout = 2
        self.maximum_pulse_amplitude = 10.0
        self.vxi11_client = Vxi11Client(host)
        self.client_id = client_id
        if name is None:
            self.name = 'inst0'
        else:
            self.name = name

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
        return "tektronix_AFG3021C"
        
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
        self.write("SOUR1:VOLT:LEV:IMM:AMPL "+str(float(voltage))+"VPP")
        
    def turn_output_on(self):
        self.write("OUTP1:STAT ON")
        
    def turn_output_off(self):
        self.write("OUTP1:STAT OFF")
        
    def set_offset_voltage(self,voltage):
        self.write("SOUR1:VOLT:LEV:IMM:OFFS "+str(float(voltage))+"V")

    def set_AM_on(self):
        self.write("SOUR1:AM:STAT ON")
        
    def set_AM_off(self):
        self.write("SOUR1:AM:STAT OFF")
        
    def set_AM_source_int(self):
        self.write("SOUR1:AM:SOUR INT")
        
    def set_AM_source_ext(self):
        self.write("SOUR1:AM:SOUR EXT")
        
    def set_AM_frequency(self,f):
        self.write("SOUR1:AM:INT:FREQ "+str(float(f))+"Hz")
        
    def set_sweep_on(self):
        self.write("SOUR1:FREQ:CONC:STAT ON")
        
    def set_sweep_off(self):
        self.write("SOUR1:FREQ:CONC:STAT OFF")
        
    def set_sweep_start_frequency(self,f):
        self.write("SOUR1:FREQ:STAR "+str(float(f))+"Hz")
        
    def set_sweep_stop_frequency(self,f):
        self.write("SOUR1:FREQ:STOP "+str(float(f))+"Hz")
        
    def set_sweep_hold_time(self,t):
        self.write("SOUR1:SWE:HTIM "+str(float(t)))
        
    def set_sweep_return_time(self,t):
        self.write("SOUR1:SWE:RTIM "+str(float(t)))
        
    def set_sweep_spacing(self,s):
        if s not in ["LIN","LOG"]:
            print "Unkown spacing! Choose from: [LIN,LOG]"
            return
        self.write("SOUR1:SWE:SPAC "+str(s))
        
    def set_sweep_time(self,t):
        self.write("SOUR1:SWE:TIME "+str(float(t)))
        
    def set_sweep_mode(self,mode):
        if mode not in ["AUTO","MAN"]:
            print "Unkown mode! Choose from: [AUTO,MAN]"
            return
        self.write("OUTP1:SWE:MODE "+str(mode))
        
    def set_AM_depth(self,d):
        self.write("SOUR1:AM:DEPT "+str(float(d)))
        
    def set_AM_function(self,typ):
        if not typ in ["SIN","SQU","TRI","RAMP","NRAM","USER1","USER2","USER3","USER4","PRN","EMEM","EFIL"]:
            print "Unkown function type! Choose from: [SIN,SQU,TRI,RAMP,NRAM,USER1,USER2,USER3,USER4,PRN,EMEM,EFIL]"
            return
        self.write("SOUR1:AM:INT:FUNC "+str(typ))
        
    def set_burst_on(self):
        self.write("SOUR1:BURST:STAT ON")
        
    def set_burst_off(self):
        self.write("SOUR1:BURST:STAT OFF")
        
    def set_burst_number_of_cycles(self,n):
        if n is not "INF" and not str(n).isdigit():
            print "Unkown number of cycles! Choose from: [INF,1,5,..(any other integer number)]"
            return
        self.write("SOUR1:BURST:NCYC "+str(n))
        
    def set_pulse_duty_cycles(self,n):
        #edited by Eva 09.07.2015 - DCYC takes as an input percentage not cycle number (is unintuitive)
        if n > 99.9 or n < 0.1:
                print "The Duty percentage can be set between 0.1 and 99.9 in increments of 0.1%."
        #if n is not "INF" and not str(n).isdigit():
        #    print "Unkown number of cycles! Choose from: [INF,1,5,..(any other integer number)]"
        #    return
        self.write("SOUR1:PULS:DCYC "+str(float(n)))

        
    def set_burst_mode(self,mode):
        if mode not in ["GAT","TRIG"]:
            print "Unkown mode! Choose from: [GAT,TRIG]"
            return
        self.write("SOUR1:BURST:MODE "+str(mode))
        
    def set_burst_trig_delay(self,delay):
        self.write("SOUR1:BURST:TDEL "+str(float(delay)))
        
    def set_pulse_lead_delay(self,delay):
        self.write("SOUR1:PULS:DEL "+str(float(delay)))
        
    def set_pulse_trailing_edge(self,time):
        self.write("SOUR1:PULS:TRAN:TRA "+str(float(time)))
        
    def set_pulse_leading_edge(self,time):
        self.write("SOUR1:PULS:TRAN:LEAD "+str(float(time)))
        
    def set_pulse_width(self,width):
        self.write("SOUR1:PULS:WIDT "+str(float(width)))
        
    def set_pulse_period(self,period):
        self.write("SOUR1:PULS:PER "+str(float(period)))
        
    def set_low_voltage(self,voltage):
        self.write("SOUR1:VOLT:LEV:IMM:LOW "+str(float(voltage))+"V")
        
    def set_high_voltage(self,voltage):
        self.write("SOUR1:VOLT:LEV:IMM:HIGH "+str(float(voltage))+"V")
        
    def set_frequency(self,f):
        self.write("SOUR1:FREQ:FIX "+str(float(f))+"Hz")
        
    def set_phase(self,p):
        self.write("SOUR1:PHAS:ADJ "+str(float(p))+"DEG")
        
    def trigger(self):
        self.write("*TRG")
        
    def reset(self):
        self.write("*RST")
        
    def set_trigger_mode(self,mode):
        if mode not in ["INT","EXT"]:
            print "Unkown mode! Choose from: [INT,EXT]"
            return
        self.write("OUTP1:TRIG:MODE "+str(mode))
        
    def set_waveform_polarity(self,mode):
        if mode not in ["INV","NORM"]:
            print "Unkown mode! Choose from: [INVerted,NORMal]"
            return
        self.write("OUTP1:POL "+str(mode))
        
    def set_trigger_input(self,mode):
        if mode not in ["TIM","EXT"]:
            print "Unkown mode! Choose from: [TIM,EXT]"
            return
        self.write("TRIG:SEQ:SOUR "+str(mode))
        
    def set_function_type(self,typ):
        if not typ in ["SIN","SQU","RAMP","PULS","DC","PRN","SINC","GAUS","LOR","HAV","ERISE","EDEC"]:
            print "Unkown function type! Choose from: [SIN,SQU,RAMP,PULS,DC,PRN,SINC,GAUS,LOR,HAV,ERISE,EDEC] HAV==Haversine LOR==Lorentz, PRN==periodic random noise"
            return
        self.write("SOUR1:FUNC:SHAP "+str(typ))
        
    #editted by Eva 13.07.15 - to set the load impedance
    def set_load_impedance(self,impedance):
        #INF sets the impedance to >10kOhm
        #MIN sets the impedance to 1 Ohm
        #MAX sets the impedance to 10kOhm
        if impedance not in ["INF", "MIN", "MAX"]:
                print "Please choose a load impedance INF, MIN or MAX."
                return
        self.write("OUTP1:IMP "+str(impedance))
        
    def get_maximum_pulse_amplitude(self):
        return self.maximum_pulse_amplitude
        
    def query(self,text,sleep_time=0.5):
        self.write(str(text))
        time.sleep(sleep_time)
        return self.read()
        
        
# Little demo to show how the class can be used to make pulses
if __name__ == "__main__":
   
    ip_address = "192.168.1.14"
    tektronix_AFG3021C = tektronix_AFG3021C(ip_address)
    tektronix_AFG3021C.open()
    tektronix_AFG3021C.reset()
    tektronix_AFG3021C.set_burst_on()
    tektronix_AFG3021C.set_burst_mode("TRIG")
    tektronix_AFG3021C.set_burst_number_of_cycles(1)
    tektronix_AFG3021C.set_trigger_input("EXT")
    tektronix_AFG3021C.set_function_type("PULS")
    tektronix_AFG3021C.set_load_impedance("INF")
    tektronix_AFG3021C.set_burst_trig_delay(4.2)
    tektronix_AFG3021C.set_frequency(1/(2.3))
    tektronix_AFG3021C.set_waveform_polarity("NORM")
    tektronix_AFG3021C.set_offset_voltage(0.5*4.4)
    tektronix_AFG3021C.set_high_voltage(4.4)
    tektronix_AFG3021C.set_low_voltage(0)
    tektronix_AFG3021C.turn_output_on()
    tektronix_AFG3021C.trigger()
    print "Pulse has been triggered"
    time.sleep(3)
    tektronix_AFG3021C.trigger()
    print "And another one..."
    tektronix_AFG3021C.turn_output_off()
    tektronix_AFG3021C.close()
