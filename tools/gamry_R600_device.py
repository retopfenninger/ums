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


import comtypes
import comtypes.client as client
import time
import numpy as np
import pythoncom # For coinitialize


GamryCOM=client.GetModule(r'C:\Program Files (x86)\Gamry Instruments\Framework 6\GamryCom.exe')
current_datapoint_has_been_measured = False

# utilities: #####################
class GamryCOMError(Exception):
    #pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
    pass

def gamry_error_decoder(e):
    pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
    if isinstance(e, comtypes.COMError):
        hresult = 2**32+e.args[0]
        if hresult & 0x20000000:
            return GamryCOMError('0x{0:08x}: {1}'.format(2**32+e.args[0], e.args[1]))
    pythoncom.CoUninitialize() # Windows shit
    return e

class GamryReadZEvents(object):
    def __init__(self, readz):
        pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        self.readz = readz
        self.acquired_points = []
        self.Vreal = []
        self.Vimag = []
        self.Vsig = []
        self.Vdc = []
        self.Ireal = []
        self.Iimag = []
        self.Isig = []
        self.Idc = []
        self.Zreal = []
        self.Zimag = []
        self.Zsig = []
        self.Zfreq = []
        self.Imod = []
        self.Iphz = []
        self.Vmod = []
        self.Vphz = []
        self.Zmod = []
        self.Zphz = []
        self.Gain = []
        self.VNoise = []
        self.INoise = []
        self.IENoise = []
        self.IERange = []
        
        
    def cook(self): # What a stupid name for a function!
        # This broken crap is not documented well and I could not make it work properly
        print "I am not a Cook!"
        
    def _IGamryReadZEvents_OnDataAvailable(self, this): # "This" is a variable which is actually only used in other programming languages. References to the class itself are covered with the "self" attribute. RTFM !!!
        time.sleep(1) # Needed, otherwise all data is 0.0. Why is the programmer of this device API not feeling ashamed? 
        self.Vreal.append(self.readz.Vreal())
        self.Vimag.append(self.readz.Vimag())
        self.Vsig.append(self.readz.Vsig())
        self.Vdc.append(self.readz.Vdc())
        self.Ireal.append(self.readz.Ireal())
        self.Iimag.append(self.readz.Iimag())
        self.Isig.append(self.readz.Isig())
        self.Idc.append(self.readz.Idc())
        self.Zreal.append(self.readz.Zreal())
        self.Zimag.append(self.readz.Zimag())
        self.Zsig.append(self.readz.Zsig())
        self.Zfreq.append(self.readz.Zfreq())
        self.Imod.append(self.readz.Imod())
        self.Iphz.append(self.readz.Iphz())
        self.Vmod.append(self.readz.Vmod())
        self.Vphz.append(self.readz.Vphz())
        self.Zmod.append(self.readz.Zmod())
        self.Zphz.append(self.readz.Zphz())
        self.Gain.append(self.readz.Gain())
        self.VNoise.append(self.readz.VNoise())
        self.INoise.append(self.readz.INoise())
        self.IENoise.append(self.readz.IENoise())
        self.IERange.append(self.readz.IERange())

    def _IGamryReadZEvents_OnDataDone(self, this, error):
        global current_datapoint_has_been_measured
        current_datapoint_has_been_measured = True
        print "Datadone",str(error)
        time.sleep(1) # Needed, otherwise all data is 0.0. Never heard something about interrupts?
        self.Vreal.append(self.readz.Vreal())
        self.Vimag.append(self.readz.Vimag())
        self.Vsig.append(self.readz.Vsig())
        self.Vdc.append(self.readz.Vdc())
        self.Ireal.append(self.readz.Ireal())
        self.Iimag.append(self.readz.Iimag())
        self.Isig.append(self.readz.Isig())
        self.Idc.append(self.readz.Idc())
        self.Zreal.append(self.readz.Zreal())
        self.Zimag.append(self.readz.Zimag())
        self.Zsig.append(self.readz.Zsig())
        self.Zfreq.append(self.readz.Zfreq())
        self.Imod.append(self.readz.Imod())
        self.Iphz.append(self.readz.Iphz())
        self.Vmod.append(self.readz.Vmod())
        self.Vphz.append(self.readz.Vphz())
        self.Zmod.append(self.readz.Zmod())
        self.Zphz.append(self.readz.Zphz())
        self.Gain.append(self.readz.Gain())
        self.VNoise.append(self.readz.VNoise())
        self.INoise.append(self.readz.INoise())
        self.IENoise.append(self.readz.IENoise())
        self.IERange.append(self.readz.IERange())
        
    def close(self):
        pythoncom.CoUninitialize() # Windows shit
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
        
###############################

class gamry_R600_device:
    def __init__(self, mode="Potentiostat", which_one=0):
        pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        self.devices=client.CreateObject('GamryCOM.GamryDeviceList',clsctx=comtypes.CLSCTX_LOCAL_SERVER)
        # print self.devices.EnumSections()
        # Unfortunately it is necessary to sleep for 10 seconds after initializing the
        # device list.  Results with-out this sleep are somewhat unpredictable.
        time.sleep(10) # Another demonstration how immature this ugly interface is programmed
        self.pstat=client.CreateObject('GamryCOM.GamryPstat',clsctx=comtypes.CLSCTX_LOCAL_SERVER)
        self.pstat.Init(self.devices.EnumSections()[which_one]) # grab pstat selected
        time.sleep(10)
        self.pstat.Open()
        time.sleep(1)
        #self.pstat.SetCell(0) # 0=off 1=on
        #self.pstat.SetCell(GamryCOM.CellOff)
        #self.pstat.SetCtrlMode(1) # 0=Galvanostat (amp=const), 1=Potentiostat (volts=const), 2=Zero Resistance Ammeter 3=Frequency response analyser
        self.mode = mode
        if self.mode == "Potentiostat":
            self.pstat.SetCtrlMode(GamryCOM.PstatMode)
            print "Potentiostatic mode selected"
        elif self.mode == "Galvanostat":
            self.pstat.SetCtrlMode(GamryCOM.GstatMode)
            print "Galvanostatic mode selected"
        #self.pstat.SetStability(GamryCOM.StabilityFast) # 0=Fast 1=medfast 2=norm 3=slow
        #self.pstat.SetStability(2) # 0=Fast 1=medfast 2=norm 3=slow
        #self.pstat.SetCASpeed(GamryCOM.CASpeedMedFast) # use medfast ???
        self.pstat.SetSenseSpeedMode(1) # TRUE
        #self.pstat.SetConvention(1) # 0=cathodic 1=anodic
        self.pstat.SetGround(0) # 0=Float 1=Earth
        #self.pstat.SetIchRange(3.0)
        #self.pstat.SetIchRangeMode(0) # False
        #self.pstat.SetIchFilter(5.0)
        #self.pstat.SetVchRange(3.0)
        #self.pstat.SetVchRangeMode(0) # False
        #self.pstat.SetIchOffsetEnable(1) # True
        #self.pstat.SetVchOffsetEnable(1) # True
        #self.pstat.SetVchFilter(5.0)
        #self.pstat.SetAchRange(3.0)
        #self.pstat.SetIERangeLowerLimit() # NIL
        #self.pstat.SetIERange(0.03)
        #self.pstat.SetIERangeMode(0) # False
        #self.pstat.SetAnalogOut(0.0)
        #self.pstat.SetVoltage(0.0) # DCvoltage
        #self.pstat.SetPosFeedEnable(0) # False
        time.sleep(1)
        self.pstat.SetCell(GamryCOM.CellOn)
        time.sleep(1)
        self.readz=client.CreateObject('GamryCOM.GamryReadZ',clsctx=comtypes.CLSCTX_LOCAL_SERVER)
        self.readz.Init(self.pstat)
        self.readzsink = GamryReadZEvents(self.readz)
        self.connection = client.GetEvents(self.readz, self.readzsink)
        self.frequency_values = []
        self.wait_time_after_each_measurement = 5
        self.cycle_max = 10
        self.interrupt = False # Variable which makes it possible to stop a running measurement
        #self.setup_impedance_measurement()
        pythoncom.CoUninitialize() # Windows shit
        return
        
    def setup_impedance_measurement(self, cycle_min=5, cycle_max=10, speed=1, zmod=1000000, bias=0.0):
        pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        # Set up the experiment
        self.readz.SetCycleLim(cycle_min,cycle_max)
        self.cycle_max = cycle_max
        self.readz.SetSpeed(speed) # 0=Fast 1=Normal 2=Low
        self.readz.SetZmod(zmod) # Initial Guess of impedance
        if self.mode == "Potentiostat":
            self.pstat.SetBias(float(bias))
        elif self.mode == "Galvanostat" and bias is not 0:
            print "ERROR: In Galvanostatic mode no bias can be applied!"
        #self.readz.SetGain(1.5343)
        #self.readz.SetVNoise(1.5343)
        #self.readz.SetINoise(1.5343)
        #self.readz.SetIENoise(1.5343)
        #self.readz.SetIdc(1.5343)
        pythoncom.CoUninitialize() # Windows shit
        return
        
    def perform_single_measurement(self,frequency,amplitude):
        # Start a measurement. For each point alone
        # FIXME (on API level): There is a bug so that the first datapoint is measured(?) and returned twice. 
        pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        self.wait_time_after_each_measurement = 2+self.cycle_max/frequency
        try:
            if self.mode == "Potentiostat":
                print "measuring...",frequency,"Hz ",amplitude,"mV ",self.wait_time_after_each_measurement,"sec sleeptime"
            elif self.mode == "Galvanostat":
                print "measuring...",frequency,"Hz ",amplitude,"mA ",self.wait_time_after_each_measurement,"sec sleeptime"
            self.pstat.SetCell(GamryCOM.CellOn)
            time.sleep(1)
            self.readz.Measure(frequency,amplitude)
            print "Command sent"
            client.PumpEvents(1)
            global current_datapoint_has_been_measured
            while not current_datapoint_has_been_measured:
                time.sleep(2)
            current_datapoint_has_been_measured = False
        except Exception as e:
            raise gamry_error_decoder(e)
        pythoncom.CoUninitialize() # Windows shit
        return
         
    def perform_impedance_measurement(self, start_frequency, end_frequency, amplitude, num_points_per_decade=10):
        # Filter out line frequency 50Hz 100Hz and 200Hz afterwards
        frequency_values_generated = np.logspace(int(np.log10(start_frequency)),int(np.log10(end_frequency)),int(num_points_per_decade)*int(np.log10(end_frequency/start_frequency)))     
        frequency_values_without_50Hz = [float(i+4.5) if np.absolute(i-50)<1.0 else i for i in frequency_values_generated]
        frequency_values_without_100Hz = [float(i+2.5) if np.absolute(i-100)<1.0 else i for i in frequency_values_without_50Hz]
        frequency_values_without_200Hz = [float(i+1.5) if np.absolute(i-200)<0.8 else i for i in frequency_values_without_100Hz]
        self.frequency_values = frequency_values_without_200Hz
        pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        for single_frequency in self.frequency_values:
            if not self.interrupt:
                self.perform_single_measurement(single_frequency,amplitude)
        pythoncom.CoUninitialize() # Windows shit
        return
        
    def get_nyquist_data(self):
        print "ND is",self.readzsink.Zreal
        return [self.readzsink.Zreal,self.readzsink.Zimag]
        
    def get_bode_data(self):
        print "BD is",self.readzsink.Zmod
        return [self.frequency_values,self.readzsink.Zmod]
        
    def get_number_of_points_measured(self):
        return len(self.readzsink.Zreal) # You could basically pick any value
        
    def close(self):
        self.interrupt = True
        time.sleep(7)
        self.pstat.SetCell(GamryCOM.CellOff)
        pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        del self.connection
        self.pstat.Close()
        pythoncom.CoUninitialize() # Windows shit
        return
        
    def flush(self):
        self.interrupt = True
        time.sleep(7)
        return
        
    def unflush(self):
        self.interrupt = False
        return
        
    def __exit__(self):
        try:
            self.close()
        except Exception:
            pythoncom.CoUninitialize() # Windows shit
            pass
        return
        
    def __del__(self):
        try:
            self.close()
        except Exception:
            pythoncom.CoUninitialize() # Windows shit
            pass
        return

        
# Little demo to show how the class can be used to acquire a simple impedance measurement
if __name__ == "__main__":
    gamry = gamry_R600_device()
    gamry.setup_impedance_measurement()
    gamry.perform_impedance_measurement(1, 10, 1)
    print gamry.get_nyquist_data()
    print gamry.get_bode_data()
    gamry.close()

#print readzsink.Vimag
#print readzsink.Vsig
#print readzsink.Vdc
#print readzsink.Ireal
#print readzsink.Iimag
#print readzsink.Isig
#print readzsink.Idc
#print readzsink.Zreal
#print readzsink.Zimag
#print readzsink.Zsig
#print readzsink.Zfreq
#print readzsink.Imod
#print readzsink.Iphz
#print readzsink.Vmod
#print readzsink.Vphz
#print readzsink.Zmod
#print readzsink.Zphz
#print readzsink.Gain
#print readzsink.VNoise
#print readzsink.INoise
#print readzsink.IENoise
#print readzsink.IERange

