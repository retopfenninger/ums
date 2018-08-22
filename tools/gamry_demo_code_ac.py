# -*- coding: utf-8 -*-
# Get comtypes from:
# sourceforge -- http://sourceforge.net/projects/comtypes/files/comtypes/
# or
# PyPI -- https://pypi.python.org/pypi/comtypes
import comtypes
import comtypes.client as client


GamryCOM=client.GetModule(r'C:\Program Files (x86)\Gamry Instruments\Framework 6\GamryCom.exe')
# ACHTUNG: Dieser Pfad stimmt nicht in den Demo-files die sie den Kunden verschicken!!!!!!!!!!!
# Habe ihn nun angepasst und die Datei GamryCom.exe liegt anscheinend neu unter "Framework 6"

class GamryCOMError(Exception):
    pass

def gamry_error_decoder(e):
    if isinstance(e, comtypes.COMError):
        hresult = 2**32+e.args[0]
        if hresult & 0x20000000:
            return GamryCOMError('0x{0:08x}: {1}'.format(2**32+e.args[0], e.args[1]))
    return e

class GamryReadZEvents(object):
    def __init__(self, readz):
        self.readz = readz
        self.acquired_points = []
        
    def cook(self):
        count = 1
        while count > 0:
            count, points = self.readz.Cook(10)
            # The columns exposed by GamryDtaq.Cook vary by dtaq and are
            # documented in the Toolkit Reference Manual.
            self.acquired_points.extend(zip(*points))
        
    def _IGamryReadZEvents_OnDataAvailable(self, this):
        self.cook()

    def _IGamryReadZEvents_OnDataDone(self, this):
        self.cook() # a final cook
        # TODO:  indicate completion to enclosing code?
###############################

devices=client.CreateObject('GamryCOM.GamryDeviceList')
print devices.EnumSections()

# Unfortunately it is necessary to sleep for 10 seconds after initializing the
# device list.  Results with-out this sleep are somewhat unpredictable.
import time
time.sleep(10)

pstat=client.CreateObject('GamryCOM.GamryPstat')
pstat.Init(devices.EnumSections()[0]) # grab first pstat

pstat.Open()

readz=client.CreateObject('GamryCOM.GamryReadZ')
readz.Init(pstat)


#sigramp=client.CreateObject('GamryCOM.GamrySignalRamp')
#sigramp.Init(pstat, -0.25, 0.25, 1, 0.01, GamryCOM.PstatMode)

#pstat.SetSignal(sigramp)
#pstat.SetCell(GamryCOM.CellOn)

readzsink = GamryReadZEvents(readz)

# Use the following code to discover events:
#client.ShowEvents(readz)
connection = client.GetEvents(readz, readzsink)

try:
    for i in range(10):
        readz.Measure(i,0.1)
except Exception as e:
    raise gamry_error_decoder(e)

client.PumpEvents(1)
print len(readzsink.acquired_points)
print readzsink.acquired_points

del connection

pstat.Close()

 
