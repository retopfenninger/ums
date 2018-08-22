import time
import win32com.client as client

devicelist = client.Dispatch('GamryCOM.GamryDeviceList')

# Unfortunately it is necessary to sleep for 10 seconds after initializing the
# device list.  Results with-out this sleep are somewhat unpredictable.
import time
time.sleep(10)

# list pstats
print 'Available instruments:'
for i in range(devicelist.Count()):
    x = devicelist.EnumSections()[i]
    print x

pstat = client.Dispatch('GamryCOM.GamryPstat')
pstat.Init(x)

pstat.Open()

dtaqcpiv=client.Dispatch('GamryCOM.GamryDtaqCpiv')
dtaqcpiv.Init(pstat)

sigramp=client.Dispatch('GamryCOM.GamrySignalRamp')
sigramp.Init(pstat, -0.25, 0.25, 1, 0.01, 1) # 1 == GamryCOM.PstatMode

pstat.SetSignal(sigramp)
pstat.SetCell(1) # 1 == GamryCOM.CellOn

try:
    dtaqcpiv.Run(True)
except Exception as e:
    pstat.Close()
    raise

# NOTE:  The comtypes example in this same directory illustrates the use of com
# notification events.  The comtypes package is recommended as an alternative
# to win32com.
time.sleep(2) # just wait sufficiently long for the acquisition to complete.

acquired_points = []
count = 1
while count > 0:
    count, points = dtaqcpiv.Cook(10)
    # The columns exposed by GamryDtaq.Cook vary by dtaq and are
    # documented in the Toolkit Reference Manual.
    acquired_points.extend(zip(*points))

print len(acquired_points)

pstat.Close()
