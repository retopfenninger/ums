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

version = "2.19"
print "Unified measurement software UMS. Version:",str(version)

import time
import string
import struct
import os
import datetime
import sys

import numpy as np
import math
import source.pyqtgraph as pg
import source.pyqtgraph.multiprocess as mp
from source.pyqtgraph.Qt import QtGui, QtCore
from scipy.special import lambertw # for cooling curve extrapolation


def change_gpib_address(new_address):
    device = open(GPIB_adapter, "w+")
    device.write("++addr " + str(new_address) + "\n")
    device.close()
    return
    
pg.mkQApp()
# Create remote process with a plot window
proc = mp.QtProcess()
rpg = proc._import('source.pyqtgraph')
window_title = "Plotting"

# import all Keithley/Tektronix device drivers
from devices.tektronix_AFG2021 import tektronix_AFG2021
from devices.keithley_2601B import keithley_2601B
from devices.keithley_2602B import keithley_2602B
from devices.tektronix_AFG3021C import tektronix_AFG3021C
from devices.keithley_2612B import keithley_2612B
from devices.keithley_6517B import keithley_6517B
from devices.keithley_2700 import keithley_2700
from devices.keithley_2701 import keithley_2701
from devices.keithley_2182A import keithley_2182A
from devices.keithley_2000 import keithley_2000
from devices.keithley_2001 import keithley_2001
from devices.keithley_7001 import keithley_7001
from devices.keithley_740 import keithley_740
from devices.keithley_6220 import keithley_6220
from devices.keithley_4200gpib import keithley_4200gpib
#from devices.keithley_197A import keithley_197A

# import all oven device drivers
from devices.eurotherm_2404 import eurotherm_2404
from devices.eurotherm_2416 import eurotherm_2416
from devices.eurotherm_3216 import eurotherm_3216
from devices.eurotherm_nanodac import eurotherm_nanodac

# import power supply device drivers
from devices.tti_QL564TP import tti_QL564TP

# Import impedance bridges
from devices.gamry_R600 import gamry_R600
from devices.zahner_IM6 import zahner_IM6
from devices.solartron import solartron

# Import all flow meters
from devices.voegtlin_gsc import voegtlin_gsc
#from devices.bronkhorst_hitec import bronkhorst_hitec
#from devices.sensirion_mfc import sensirion_mfc

# Import Linkam stage controller for T-95
from devices.linkam import linkam

# Import WiTec Raman instrument alpha 300
#from devices.witec_alpha import witec_alpha

# Import data_writer-class for pretty output
from tools.data_writer import data_writer

GPIB_USB_adapter = "/dev/ttyUSB0" # here Prologix
USB = "/dev/ttyUSB0" # another synonym for Prologix

tektronix_AFG2021_ip_address = "172.31.46.10"
tektronix_AFG3021C_ip_address = "172.31.46.25"
keithley_2601B_ip_address = "172.31.46.11"
keithley_2612B_ip_address = "172.31.46.17"
keithley_2602B_ip_address = "172.31.46.18"
keithley_2701_ip_address = "172.31.46.19"
electrochem_m26_ip_address = "172.31.46.26"
electrochem_m27_ip_address = "172.31.46.27"
electrochem_m28_ip_address = "172.31.46.28"
keithley_6517B_address = 27 # GPIB Address
keithley_740_address = 14 # GPIB Address
keithley_2182A_address = 7 # GPIB Address
keithley_6220_address = 12 # GPIB Address
keithley_2000_GPIB_1_address = 1 # GPIB Address
keithley_2000_GPIB_4_address = 4 # GPIB Address
keithley_2001_GPIB_5_address = 5 # GPIB Address
keithley_2700_GPIB_3_address = 3 # GPIB Address
keithley_2700_GPIB_18_address = 18 # GPIB Address
keithley_7001_GPIB_2_address = 2 # GPIB Address
keithley_7001_GPIB_6_address = 6 # GPIB Address

#this is a python function that calls the KULT module pulsing in the electrochem library and executes set read and reset pulses
def pulsing4200(device, channel, Vset, Vreset, Vread, Vset_width, Vreset_width, Vread_width, points_per_rise, currentRng, measStart, measStop, preDatapct, postDatapct, maxpointSet, maxpointReset, maxpointRead, num_pulses, measureType, new_row = False, GUI = True):

    #this function measures with the waveform the read, set and reset pulses and plots them
    baseV = 0

    #allocate the output arrays
    dataRead = []
    dataPuls = []
    dataSM = []
    dataSet = []
    dataReset = []
    dataReadS = []
    dataReadR = []

    if(measureType == 2):
        set_size = 10000
        reset_size = 10000
        read_size = 10000

    elif(measureType == 1):
        set_size = 2
        reset_size = 2
        read_size = 2
 
    elif(measureType == 0):
        set_size = 2*maxpointSet
        reset_size = 2*maxpointReset
        read_size = 2

    else:
        print "Invalid measureType variable input. Please choose between 0, 1 or 2."

    #set-up the GUI
    if GUI:
      # create an empty list in the remote process
        p1 = win.addPlot(title="Voltage vs. time Set pulse")
        if measureType == 2 or measureType == 0:
            curve_V_t_Puls = p1.plot(pen='y')
        else:
            curve_V_t_Puls = p1.plot(pen = None, symbol = 'o')
        p1.setLabel('left', "Voltage", units='V')
        p1.setLabel('bottom', "time", units='s')
        curve_V_t_Puls.setData([], _callSync='off')

        p2 = win.addPlot(title="Current vs. time Set pulse")
        if measureType == 2 or measureType == 0:
            curve_I_t_Puls = p2.plot(pen='y')
        else:
            curve_I_t_Puls = p2.plot(pen = None, symbol = 'o')
        p2.setLabel('left', "Current", units='A')
        p2.setLabel('bottom', "time", units='s')
        curve_I_t_Puls.setData([], _callSync='off')

        win.nextRow()

        p5 = win.addPlot(title="Voltage vs. time Reading")
        if measureType == 1 or measureType == 0:
            curve_V_t_Read = p5.plot(pen=None, symbol = 'o')
        else:
            curve_V_t_Read = p5.plot(pen = 'y')
        p5.setLabel('left', "Voltage", units='V')
        p5.setLabel('bottom', "time", units='s')
        curve_V_t_Read.setData([], _callSync='off')

        p6 = win.addPlot(title="Current vs. time Reding pulse")
        if measureType == 1 or measureType == 0:
            curve_I_t_Read = p6.plot(pen = None, symbol = 'o')
        else:
            curve_I_t_Read = p6.plot(pen = 'y')
        p6.setLabel('left', "Current", units='A')
        p6.setLabel('bottom', "time", units='s')
        curve_I_t_Read.setData([], _callSync='off')

        if new_row:
            win.nextRow()

    #KXCI command to access the KULT library calling page
    device.access_usrlib_mode()
    t_lastPulse = 0
    t_lastread = 0
    #loop over the number of SET-RESET pairs
    for p in range(num_pulses):
        #int pulsing2( int channel, double Vset, double Vreset, double Vset_width, double Vreset_width, double Vread, double Vread_width, int points_per_rise, double baseV, int measureType, double measStart, double measStop, double preDatapct, double postDatapct, int MaxNumPoints_set, int MaxNumPoints_reset, int MaxNumPoints_read,double currentMeasureRng, double *Vms, int size_Vms, double *Ims, int size_Ims, double *Ts, int size_Ts, double *Vmr, int size_Vmr, double *Imr, int size_Imr, double *Tr, int size_Tr , double *Vmsr, int size_Vmsr, double *Imsr, int size_Imsr, double *Tsr, int size_Tsr, double *Vmrr, int size_Vmrr, double *Imrr, int size_Imrr, double *Trr, int size_Trr  )
        exe_str = 'pulsing2txt(%d,%.4f,%.4f,%.9f,%.9f,%.4f,%.9f,%d,%.4f,%d,%.4f,%.4f,%.4f,%.4f,%d,%d,%d,%.4f, ,%d, ,%d, ,%d, ,%d, ,%d, ,%d, ,%d, ,%d, ,%d, ,%d, ,%d, ,%d)' %(channel, Vset, Vreset, Vset_width, Vreset_width, Vread, Vread_width, points_per_rise, baseV, measureType, measStart, measStop, preDatapct, postDatapct, maxpointSet, maxpointReset, maxpointRead, currentRng,set_size,set_size,set_size,reset_size,reset_size,reset_size,read_size,read_size,read_size,read_size,read_size,read_size)
        #execute the kult function
        device.execute_usrlib('electrochem_pulsing',exe_str) 
        #get the set puls
        device.wait_for_meas_end()
        device.wait_for_meas_end() #this function does not work for the first puls??!
        time.sleep(0.1)
        print "Measurement done. Retrieving data ..."

        temp = device.get_csv(os.path.join(device.path2dir_temp_4200,"set.csv"))
        for i in range(len(temp)):
            temp[i].append(p)
            dataSet.append(temp[i])
            t = temp[i][2]+t_lastPulse
            dataPuls.append([temp[i][0],temp[i][1],t])
        t_lastPulse = t_lastPulse + temp[-1][2] 
        temp[:] = [] 

        temp = device.get_csv(os.path.join(device.path2dir_temp_4200,"read1.csv"))
        for i in range(len(temp)):
            temp[i].append(p)
            dataReadS.append(temp[i])
            t = temp[i][2]+t_lastread
            dataRead.append([temp[i][0],temp[i][1],t])
        t_lastread = t_lastread + temp[-1][2]
        temp[:] = []


        temp = device.get_csv(os.path.join(device.path2dir_temp_4200,"reset.csv"))
        for i in range(len(temp)):
            temp[i].append(p)
            dataReset.append(temp[i])
            t = temp[i][2]+t_lastPulse
            dataPuls.append([temp[i][0],temp[i][1],t])
        t_lastPulse = t_lastPulse + temp[-1][2]
        temp[:] = []

        temp = device.get_csv(os.path.join(device.path2dir_temp_4200,"read2.csv"))
        for i in range(len(temp)):
            temp[i].append(p)
            dataReadR.append(temp[i])
            t = temp[i][2]+t_lastread
            dataRead.append([temp[i][0],temp[i][1],t])
        t_lastread = t_lastread + temp[-1][2]
        temp[:] = []

        if GUI:
            curve_V_t_Puls.setData(x=[k[2] for k in dataPuls], y=[k[0] for k in dataPuls], _callSync='off')
            curve_I_t_Puls.setData(x=[k[2] for k in dataPuls], y=[k[1] for k in dataPuls], _callSync='off')

            curve_V_t_Read.setData(x=[k[2] for k in dataRead], y=[k[0] for k in dataRead], _callSync='off')
            curve_I_t_Read.setData(x=[k[2] for k in dataRead], y=[k[1] for k in dataRead], _callSync='off')
   
    return[dataSet,dataReadS,dataReset,dataReadR]

def dualSweep4200(device, channel, irange, ilimit, startv, topv, rate, points, new_row = False, GUI = True):
    data_all = []

    if GUI:
        # create an empty list in the remote process
        p1 = win.addPlot(title="Voltage vs. current")
        curve_V_I = p1.plot(pen='y')
        p1.setLabel('left', "Current", units='A')
        p1.setLabel('bottom', "Voltage", units='V')
        curve_V_I.setData([], _callSync='off')

        p2 = win.addPlot(title="Voltage vs. time")
        curve_V_t = p2.plot(pen='y')
        p2.setLabel('left', "Voltage", units='V')
        p2.setLabel('bottom', "time", units='s')
        curve_V_t.setData([], _callSync='off')

        p3 = win.addPlot(title="Current vs. time")
        curve_I_t = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_I_t.setData([], _callSync='off')
      
        if new_row:
            win.nextRow()

    device.access_usrlib_mode()
    exe_str = 'DCDualSweep(SMU%d,%.4f,%.4f,%.4f,%.4f,%d,%.4f, ,%d, ,%d, ,%d)' %(channel, irange, ilimit, startv, topv, points, rate,points,points,points)
    #here we send the command to execute the DCDualSweep.c module in the library of KULT
    device.execute_usrlib('electrochem_cycling',exe_str)
    #have to have this function twice? not sure why 
    device.wait_for_meas_end()
    device.wait_for_meas_end()

    #get the data from a file that was generated by the module in KULT - the location is in umdata - check the device file if the path is correct
    temp = device.get_csv(os.path.join(device.path2dir_temp_4200,"DualSweep.csv"))

    #copy the data from the file to a python file - much easier
    for row in temp:
        data_all.append(row)
    if GUI: #this visualizes the plots
        curve_I_t.setData(x=[k[2] for k in data_all], y=[k[1] for k in data_all], _callSync='off')
        curve_V_t.setData(x=[k[2] for k in data_all], y=[k[0] for k in data_all], _callSync='off')
        curve_V_I.setData(x=[k[0] for k in data_all], y=[k[1] for k in data_all], _callSync='off')

    return data_all

def cycling4200(device, channel, startv, topv, bottomv, ramp_speed, cycles, irange_pos, irange_neg, ilimit_pos, ilimit_neg, points, new_row = False, GUI = True):
    data_all = []
    if GUI:
        # create an empty list in the remote process
        p1 = win.addPlot(title="Voltage vs. current")
        curve_V_I = p1.plot(pen='y')
        p1.setLabel('left', "Current", units='A')
        p1.setLabel('bottom', "Voltage", units='V')
        curve_V_I.setData([], _callSync='off')

        p2 = win.addPlot(title="Voltage vs. time")
        curve_V_t = p2.plot(pen='y')
        p2.setLabel('left', "Voltage", units='V')
        p2.setLabel('bottom', "time", units='s')
        curve_V_t.setData([], _callSync='off')

        p3 = win.addPlot(title="Current vs. time")
        curve_I_t = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_I_t.setData([], _callSync='off')
      
        if new_row:
            win.nextRow()
    if topv - startv > 0:
        irange1 = irange_pos
        ilimit1 = ilimit_pos
        irange2 = irange_neg
        ilimit2 = ilimit_neg
    else:
        irange1 = irange_neg
        ilimit1 = ilimit_neg
        irange2 = irange_pos
        ilimit2 = ilimit_pos
    ramp_speed = np.absolute(ramp_speed)
    pointDual = points/(2*cycles)
    last_time = 0
    for i in range(cycles):

        #this is the execution of the dualSweep function that calls KULT through KXCI
        temp = dualSweep4200(device, channel, irange1, ilimit1, startv, topv, ramp_speed, pointDual, False, False)
        for row in temp:
            row[2] = row[2] + last_time
            row.append(i)
            data_all.append(row)
        last_time = temp[-1][2]
        if GUI: #this visualizes the plots
            curve_I_t.setData(x=[k[2] for k in data_all], y=[k[1] for k in data_all], _callSync='off')
            curve_V_t.setData(x=[k[2] for k in data_all], y=[k[0] for k in data_all], _callSync='off')
            curve_V_I.setData(x=[k[0] for k in data_all], y=[k[1] for k in data_all], _callSync='off')

        #this is the execution of the dualSweep function that calls KULT through KXCI
        temp = dualSweep4200(device, channel, irange2, ilimit2, startv, bottomv, ramp_speed, pointDual, False, False)
        for row in temp:
            row[2] = row[2] + last_time
            row.append(i)
            data_all.append(row)
        last_time = temp[-1][2]
        if GUI: #this visualizes the plots
            curve_I_t.setData(x=[k[2] for k in data_all], y=[k[1] for k in data_all], _callSync='off')
            curve_V_t.setData(x=[k[2] for k in data_all], y=[k[0] for k in data_all], _callSync='off')
            curve_V_I.setData(x=[k[0] for k in data_all], y=[k[1] for k in data_all], _callSync='off')

    return data_all

def DCVoltage4200(device, channel, irange, ilimit, voltage_level, duration, new_row = False, GUI=True):
    data_all = []
    if GUI:
        # create an empty list in the remote process

        p2 = win.addPlot(title="Voltage vs. time")
        curve_V_t = p2.plot(pen='y')
        p2.setLabel('left', "Voltage", units='V')
        p2.setLabel('bottom', "time", units='s')
        curve_V_t.setData([], _callSync='off')

        p3 = win.addPlot(title="Current vs. time")
        curve_I_t = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_I_t.setData([], _callSync='off')

        if new_row:
            win.nextRow()
    points = 10000
    device.access_usrlib_mode()
    exe_str = 'DCVoltage(SMU%d,%.4f,%.4f,%.4f,%.4f, ,%d, ,%d, ,%d)' %(channel, irange, ilimit, voltage_level, duration,points,points,points)
    #here we send the command to execute the DCDualSweep.c module in the library of KULT
    device.execute_usrlib('electrochem_cycling',exe_str)
    #have to have this function twice? not sure why 
    device.wait_for_meas_end()
    device.wait_for_meas_end()

    #get the data from a file that was generated by the module in KULT - the location is in umdata - check the device file if the path is correct
    temp = device.get_csv(os.path.join(device.path2dir_temp_4200,"DCVoltage.csv"))

    #copy the data from the file to a python file - much easier
    for row in temp:
        data_all.append(row)
    if GUI: #this visualizes the plots
        curve_I_t.setData(x=[k[2] for k in data_all], y=[k[1] for k in data_all], _callSync='off')
        curve_V_t.setData(x=[k[2] for k in data_all], y=[k[0] for k in data_all], _callSync='off')

    return data_all

def pulse_rnone(device_smu,device_function_generator,V_peak,const_pulse_width,time_between_pulses, num_pulses,new_row=False,GUI=True):
# This function just measures the current responce to a series of voltage pulses - there is no reading voltage and the currents starts and ends at zero voltage.
    device_smu.reset()
    device_function_generator.reset()
    device_smu.setup_current_measurement()
    device_smu.turn_output_off()
    data_V_t_2 = []
    data_I_t_2 = []
    if GUI:
        if new_row:
            win.nextRow()

        p5 = win.addPlot(title="Voltage vs. time")
        curve_V_t_2 = p5.plot(pen='y')
        p5.setLabel('left', "Voltage", units='V')
        p5.setLabel('bottom', "time", units='s')
        curve_V_t_2.setData([], _callSync='off')

        p6 = win.addPlot(title="Current vs. time")
        curve_I_t_2 = p6.plot(pen='y')
        p6.setLabel('left', "Current", units='A')
        p6.setLabel('bottom', "time", units='s')
        curve_I_t_2.setData([], _callSync='off')
    device_function_generator.set_burst_on()
    device_function_generator.set_burst_mode("TRIG")
    device_function_generator.set_burst_number_of_cycles(1)
    device_function_generator.set_trigger_input("EXT")
    device_function_generator.set_function_type("PULS")
    device_function_generator.set_load_impedance("INF")
    device_function_generator.set_burst_trig_delay(0)
    device_function_generator.set_frequency(1/(const_pulse_width))
    if V_peak < 0:
        device_function_generator.set_waveform_polarity("INV")
        device_function_generator.set_offset_voltage(0.5*V_peak)
        device_function_generator.set_low_voltage(V_peak)
        device_function_generator.set_high_voltage(0) 
    else:
        device_function_generator.set_waveform_polarity("NORM")
        device_function_generator.set_offset_voltage(0.5*V_peak)
        device_function_generator.set_high_voltage(V_peak)
        device_function_generator.set_low_voltage(0) 
    device_function_generator.turn_output_on()
    device_function_generator.set_pulse_duty_cycles(99.9)
    pulse_end_time = 0
    V_pulse = V_peak
    measuring = True
    if np.absolute(V_pulse) > device_function_generator.get_maximum_pulse_amplitude(): # limitation of function generator
        V_pulse = device_function_generator.get_maximum_pulse_amplitude()*np.sign(V_pulse)
    cycle = 1
    pulse_off = True
    t0 = time.time() # measurement start time
    timestamp = 0
    while measuring:
        V = 0
        if time.time()-t0 >= cycle*time_between_pulses + (cycle-1)*const_pulse_width: #gives the time to start pulsing 
            pulse_off = False
            timestamp = time.time()-t0
            device_function_generator.trigger() # apply pulse
            cycle = cycle + 1
            pulse_end_time = timestamp+const_pulse_width
            data_V_t_2.append([timestamp,V_pulse])
            data_V_t_2.append([pulse_end_time,V_pulse])
        I = device_smu.get_current() #read the current from the keithley device
        timestamp = time.time()-t0  #get the correct time for the current read-out
        data_I_t_2.append([timestamp,I]) #writes into the plot variable the current and time (at any case)
        if timestamp > pulse_end_time:  # if the pulse is not ongoing we need to stop the cycle
            pulse_off = True #turn the puls off
        if pulse_off:
            data_V_t_2.append([timestamp,V]) #this line is saving the voltage vs. time curve
        if cycle == num_pulses + 1 and timestamp >= pulse_end_time + 0.8*time_between_pulses:
            measuring = False
        if GUI: #this visualizes the plots
            curve_I_t_2.setData(x=[k[0] for k in data_I_t_2], y=[k[1] for k in data_I_t_2], _callSync='off')
            curve_V_t_2.setData(x=[k[0] for k in data_V_t_2], y=[k[1] for k in data_V_t_2], _callSync='off')
    device_function_generator.turn_output_off()
    return [data_V_t_2,data_I_t_2] #here are the variable we are saving
    
def pulse_rsquare(device_smu,device_function_generator,Vset_peak,Vreset_peak,reset_pulse_width,set_pulse_width,time_between_pulses, num_pulses,time_at_zero, V_read,alternate=True,new_row=False,GUI=True):
# This function allows you to measure also the resistance during (depending on the time scale) and between pulses. - that means that there is a square reading scheme between the pulses.
# Vset_peak will be used as first pulse so make sure it is the correct polarity - need to put a sign before it
# if alternate = False just the set parameters will be used - that means Vset_peak and set_pulse_width
# be careful so far works just for positive V_read if alternate = True
    if V_read < 0:
        V_read = abs(V_read)
    read_time = time_between_pulses - 2*time_at_zero
    if read_time <= 0:
        print "The time the voltage is at zero between two pulses is too long. Please decrease the time_at_zero or increase time_between_pulses."
    const_pulse_width = set_pulse_width
    device_smu.reset()
    device_function_generator.reset()
    device_smu.setup_current_measurement()
    device_smu.turn_output_off()
    data_cycle_R_2 = []
    data_cycle_post_R_2 = []
    data_V_t_2 = []
    data_I_t_2 = []
    if GUI:
        if new_row:
            win.nextRow()
        p3 = win.addPlot(title="Resistance between pulses")
        curve_cycle_post_R_2 = p3.plot(pen=None, symbol='o')
        p3.setLabel('left', "Resistance", units='Ohm')
        p3.setLabel('bottom', "Cycles", units='')
        curve_cycle_post_R_2.setData([], _callSync='off')
    
        p4 = win.addPlot(title="Resistance during pulse")
        curve_cycle_R_2 = p4.plot(pen=None, symbol='o')
        p4.setLabel('left', "Resistance", units='Ohm')
        p4.setLabel('bottom', "Cycles", units='')
        curve_cycle_R_2.setData([], _callSync='off')

        p5 = win.addPlot(title="Voltage vs. time")
        curve_V_t_2 = p5.plot(pen='y')
        p5.setLabel('left', "Voltage", units='V')
        p5.setLabel('bottom', "time", units='s')
        curve_V_t_2.setData([], _callSync='off')

        p6 = win.addPlot(title="Current vs. time")
        curve_I_t_2 = p6.plot(pen='y')
        p6.setLabel('left', "Current", units='A')
        p6.setLabel('bottom', "time", units='s')
        curve_I_t_2.setData([], _callSync='off')
    device_function_generator.set_burst_on()
    device_function_generator.set_burst_mode("TRIG")
    device_function_generator.set_burst_number_of_cycles(1)
    device_function_generator.set_trigger_input("EXT")
    device_function_generator.set_trigger_mode("EXT")
    device_function_generator.set_function_type("PULS")
    device_function_generator.set_burst_trig_delay(0)
    device_function_generator.set_load_impedance("INF")
    device_function_generator.set_pulse_duty_cycles(99.9)
    device_function_generator.set_low_voltage(0)
    device_function_generator.set_pulse_period(const_pulse_width)
    device_function_generator.turn_output_on()
    vset_pol = np.sign(Vset_peak)
    vreset_pol = np.sign(Vreset_peak)
    Vs_pulse = Vset_peak
    if np.absolute(Vs_pulse) > device_function_generator.get_maximum_pulse_amplitude(): # limitation of function generator
        Vs_pulse = device_function_generator.get_maximum_pulse_amplitude()*vset_pol  
    Vr_pulse = Vreset_peak
    if np.absolute(Vr_pulse) > device_function_generator.get_maximum_pulse_amplitude(): # limitation of function generator
        Vr_pulse = device_function_generator.get_maximum_pulse_amplitude()*vreset_pol
    pulse_end_time = 0
    cycle = 1
    read_average = []
    read_average_post = []
    pulse_off = True
    read_pulse = False
    measuring = True
    reset = False
    t0 = time.time() # measurement start time
    timestamp = 0
    V = 0
    data_V_t_2.append([timestamp,V])
    data_V_t_2.append([timestamp+5,V])
    while measuring:
        if cycle == 1:
            pulse_cond = 5 #just wait 5 seconds before starting to pulse
        elif not alternate:
            pulse_cond = 5+(cycle-1)*time_between_pulses + (cycle-1)*const_pulse_width
        elif (cycle%2)==0:
            pulse_cond = 5+(cycle-1)*time_between_pulses + np.floor(0.5*cycle)*set_pulse_width + (np.floor(0.5*cycle)-1)*reset_pulse_width
        else:
            pulse_cond = 5+(cycle-1)*time_between_pulses + np.floor(0.5*cycle)*set_pulse_width + np.floor(0.5*cycle)*reset_pulse_width
        if time.time()-t0 >= pulse_cond: #gives the time to start pulsing 
            if read_average_post: # its not empty. This means we catched an event. this variable traces everything between pulses    
                i_post = abs(V_read/np.average(read_average_post))
                data_cycle_post_R_2.append([cycle-1,i_post])
            read_average_post = [] 
            device_function_generator.set_pulse_duty_cycles(99.9)
            #since we changed the options of the function generator for the reading scheme we need to save them here again for pulsing
            if cycle == 1 or not alternate:
                const_pulse_width = set_pulse_width    
                V_pulse = Vs_pulse
                if V_pulse > 0:
                        device_function_generator.set_offset_voltage(0.5*V_pulse)
                        device_function_generator.set_high_voltage(V_pulse) 
                        device_function_generator.set_low_voltage(0) 
                        device_function_generator.set_waveform_polarity("NORM")
                        device_function_generator.set_pulse_period(const_pulse_width)
                else:
                        device_function_generator.set_offset_voltage(0.5*V_pulse)
                        device_function_generator.set_high_voltage(0)
                        device_function_generator.set_low_voltage(V_pulse) 
                        device_function_generator.set_waveform_polarity("INV")
                        device_function_generator.set_pulse_period(const_pulse_width)
            else:
                if reset:
                        V_pulse = Vr_pulse
                        const_pulse_width = reset_pulse_width
                else:
                        V_pulse = Vs_pulse
                        const_pulse_width = set_pulse_width
                if V_pulse > 0:
                        device_function_generator.set_offset_voltage(0.5*V_pulse)
                        device_function_generator.set_high_voltage(V_pulse) 
                        device_function_generator.set_low_voltage(0) 
                        device_function_generator.set_waveform_polarity("NORM")
                        device_function_generator.set_pulse_period(const_pulse_width)
                else:
                        device_function_generator.set_offset_voltage(0.5*V_pulse)
                        device_function_generator.set_low_voltage(V_pulse) 
                        device_function_generator.set_high_voltage(0) 
                        device_function_generator.set_waveform_polarity("INV")
                        device_function_generator.set_pulse_period(const_pulse_width)
            pulse_off = False
            timestamp = time.time()-t0
            reset = not(reset) #change reset to einther True or False - switch the pulse
            pulse_end_time = timestamp+const_pulse_width
            data_V_t_2.append([timestamp,V_pulse])
            data_V_t_2.append([pulse_end_time,V_pulse])
            cycle = cycle + 1
            device_function_generator.trigger() # apply pulse
        I = device_smu.get_current() #read the current from the keithley device
        timestamp = time.time()-t0  #get the correct time for the current read-out (this is under no if statement - it is read every time)
        data_I_t_2.append([timestamp,I]) #writes into the plot variable the current and time (at any case)
        if timestamp < pulse_end_time and cycle != 1: #if the pulse is ongoing now we save the current value in read_average
            read_average.append(I)
        elif not pulse_off:  #we turn on the pulse_off variable so we know that we are in between the pulses
            if read_average: # its not empty. This means we catched an event
                i = abs(V_pulse/np.average(read_average)) #this actually calculates the resistance but is called i
                data_cycle_R_2.append([cycle-1,i]) #this saves the resistance
            #here we iterate all the variables since we came to an end of an pulse
            read_average = []
            pulse_off = True #turn the pulse off
            read_pulse = True #this is a variable to control the reading pulses - set it just once to true between the pulses    

        if pulse_off and cycle != 1:
            #timestamp = time.time()-t0  #get the correct time
            if timestamp >= pulse_end_time + time_at_zero and read_pulse: #now we trigger the reading pulse
                device_function_generator.set_pulse_duty_cycles(99.9)
                if V_pulse > 0 or alternate:
                   device_function_generator.set_high_voltage(V_read) 
                   device_function_generator.set_low_voltage(0)
                   device_function_generator.set_offset_voltage(0.5*V_read)
                   device_function_generator.set_waveform_polarity("NORM")
                   data_V_t_2.append([timestamp, V_read])
                   data_V_t_2.append([timestamp + read_time, V_read])
                else:
                   device_function_generator.set_high_voltage(0) 
                   device_function_generator.set_low_voltage(-V_read)
                   device_function_generator.set_offset_voltage(-0.5*V_read)
                   device_function_generator.set_waveform_polarity("INV")
                   data_V_t_2.append([timestamp, -V_read])
                   data_V_t_2.append([timestamp + read_time, -V_read])
                device_function_generator.set_pulse_period(read_time)
                read_pulse = False #now turn the read pulse off so we trigger it just once
                device_function_generator.trigger() # apply reading pulse
            if pulse_end_time + time_at_zero < timestamp < pulse_end_time + time_at_zero + read_time: #if the read pulse is ongoing then save the current
                read_average_post.append(I)
            else:
                data_V_t_2.append([timestamp,V]) #this line is saving the voltage vs. time curve
        if timestamp >= pulse_end_time + 0.9*time_between_pulses:
            if cycle > num_pulses:
                measuring = False
        if GUI: #this visualizes the plots
            curve_I_t_2.setData(x=[k[0] for k in data_I_t_2], y=[k[1] for k in data_I_t_2], _callSync='off')
            curve_cycle_post_R_2.setData(x=[k[0] for k in data_cycle_post_R_2], y=[k[1] for k in data_cycle_post_R_2], _callSync='off')
            curve_cycle_R_2.setData(x=[k[0] for k in data_cycle_R_2], y=[k[1] for k in data_cycle_R_2], _callSync='off')
            curve_V_t_2.setData(x=[k[0] for k in data_V_t_2], y=[k[1] for k in data_V_t_2], _callSync='off')
    device_function_generator.turn_output_off()
    return [data_V_t_2,data_I_t_2,data_cycle_R_2,data_cycle_post_R_2] #here are the variables we are saving

def pulse_rbipolar(device_smu,device_function_generator,Vset_peak, Vreset_peak,set_pulse_width,reset_pulse_width,time_between_pulses, num_pulses,time_at_zero, V_read, alternate=True, new_row=False,GUI=True):
# This function allows you to measure also the resistance during (depending on the time scale) and between pulses. 
# There is a bipolar pulse reading scheme between the pulses. This is an advantage over a constant reading scheme since the device will not be disturbed.
# No resistence will be measured during the time at zero. This is just an option to leave the current to equilibrate.
    if V_read < 0:
        V_read = abs(V_read)
    read_time = time_between_pulses - 2*time_at_zero
    if read_time <= 0:
        print "There is not enough time to implement a reading scheme. Please decrease the time_at_zero or/and increase time_between_pulses."
    const_pulse_width = set_pulse_width
    device_smu.reset()
    device_function_generator.reset()
    device_smu.setup_current_measurement()
    device_smu.turn_output_off()
    data_cycle_R_2 = []
    data_cycle_post_R_2 = []
    data_V_t_2 = []
    data_I_t_2 = []
    if GUI:
        if new_row:
            win.nextRow()

        p3 = win.addPlot(title="Resistance between pulses.")
        curve_cycle_post_R_2 = p3.plot(pen=None, symbol='o')
        p3.setLabel('left', "Resistance", units='Ohm')
        p3.setLabel('bottom', "Cycles", units='')
        curve_cycle_post_R_2.setData([], _callSync='off')
    
        p4 = win.addPlot(title="Resistance during pulse")
        curve_cycle_R_2 = p4.plot(pen=None, symbol='o')
        p4.setLabel('left', "Resistance", units='Ohm')
        p4.setLabel('bottom', "Cycles", units='')
        curve_cycle_R_2.setData([], _callSync='off')

        p5 = win.addPlot(title="Voltage vs. time")
        curve_V_t_2 = p5.plot(pen='y')
        p5.setLabel('left', "Voltage", units='V')
        p5.setLabel('bottom', "time", units='s')
        curve_V_t_2.setData([], _callSync='off')

        p6 = win.addPlot(title="Current vs. time")
        curve_I_t_2 = p6.plot(pen='y')
        p6.setLabel('left', "Current", units='A')
        p6.setLabel('bottom', "time", units='s')
        curve_I_t_2.setData([], _callSync='off')

    device_function_generator.set_burst_on()
    device_function_generator.set_burst_mode("TRIG")
    device_function_generator.set_burst_number_of_cycles(1)
    device_function_generator.set_trigger_input("EXT")
    device_function_generator.set_trigger_mode("EXT")
    device_function_generator.set_function_type("PULS")
    device_function_generator.set_burst_trig_delay(0)
    device_function_generator.set_low_voltage(0)
    device_function_generator.set_load_impedance("INF")
    device_function_generator.set_pulse_duty_cycles(99.9)
    device_function_generator.set_pulse_period(const_pulse_width)
    device_function_generator.turn_output_on()
    pulse_end_time = 0
    Vs_pulse = Vset_peak
    if np.absolute(Vs_pulse) > device_function_generator.get_maximum_pulse_amplitude(): # limitation of function generator
        Vs_pulse = device_function_generator.get_maximum_pulse_amplitude()*np.sign(Vs_pulse)
    Vr_pulse = Vreset_peak
    if np.absolute(Vr_pulse) > device_function_generator.get_maximum_pulse_amplitude(): # limitation of function generator
        Vr_pulse = device_function_generator.get_maximum_pulse_amplitude()*np.sign(Vr_pulse)
    cycle = 1
    read_average = []
    read_average_post = []
    pulse_off = True
    read_pulse_first = False
    read_pulse_second = False
    reset = False
    t0 = time.time() # measurement start time
    timestamp = 0
    measuring = True
    data_V_t_2.append([timestamp,V])
    data_V_t_2.append([timestamp+5,V])
    while measuring:
        V = 0
        if cycle == 1:
            pulse_cond = 5 #just wait 5 seconds before starting to pulse
        elif not alternate:
            pulse_cond = cycle*time_between_pulses + (cycle-1)*const_pulse_width
        elif (cycle%2)==0:
            pulse_cond = cycle*time_between_pulses + np.floor(0.5*cycle)*set_pulse_width + (np.floor(0.5*cycle)-1)*reset_pulse_width
        else:
            pulse_cond = cycle*time_between_pulses + np.floor(0.5*cycle)*set_pulse_width + np.floor(0.5*cycle)*reset_pulse_width
        if time.time()-t0 >= pulse_cond: #gives the time to start pulsing 
            if read_average_post: # its not empty. This means we catched an event. 
                i_post = abs(V_read/np.average(read_average_post))
                data_cycle_post_R_2.append([cycle-1,i_post])
            read_average_post = [] 
            device_function_generator.set_pulse_duty_cycles(99.9)
            #since we changed the options of the function generator for the reading scheme we need to set them here again
            if cycle == 1 or not alternate:
                const_pulse_width = set_pulse_width
                V_pulse = Vs_pulse
                if V_pulse > 0:
                        device_function_generator.set_high_voltage(V_pulse) 
                        device_function_generator.set_low_voltage(0)
                        device_function_generator.set_offset_voltage(0.5*V_pulse)
                        device_function_generator.set_waveform_polarity("NORM")
                        device_function_generator.set_pulse_period(const_pulse_width)
                else:
                        device_function_generator.set_high_voltage(0) 
                        device_function_generator.set_low_voltage(V_pulse)
                        device_function_generator.set_offset_voltage(0.5*V_pulse)
                        device_function_generator.set_waveform_polarity("INV")
                        device_function_generator.set_pulse_period(const_pulse_width)
            else:
                if reset:
                        V_pulse = Vr_pulse
                        const_pulse_width = reset_pulse_width
                        
                else:
                        V_pulse = Vs_pulse
                        const_pulse_width = set_pulse_width
                if V_pulse < 0:
                        device_function_generator.set_high_voltage(0) 
                        device_function_generator.set_low_voltage(V_pulse)
                        device_function_generator.set_offset_voltage(0.5*V_pulse)
                        device_function_generator.set_waveform_polarity("INV")
                        device_function_generator.set_pulse_period(const_pulse_width)
                else:
                        device_function_generator.set_high_voltage(V_pulse) 
                        device_function_generator.set_low_voltage(0)
                        device_function_generator.set_offset_voltage(0.5*V_pulse)
                        device_function_generator.set_waveform_polarity("NORM")
                        device_function_generator.set_pulse_period(const_pulse_width)
            pulse_off = False
            timestamp = time.time()-t0
            device_function_generator.trigger() # apply pulse
            reset = not(reset)
            cycle = cycle+1 #append cycle count
            data_V_t_2.append([timestamp,V_pulse])
            pulse_end_time = timestamp+const_pulse_width
            data_V_t_2.append([pulse_end_time,V_pulse])
        I = device_smu.get_current() #read the current from the keithley device
        timestamp = time.time()-t0  #get the correct time (this is under no if statement - it is read every time)
        data_I_t_2.append([timestamp,I]) #writes into the plot variable the current and time (at any case)
        if timestamp < pulse_end_time and cycle != 1: #if the pulse is ongoing now we save the current value in read_average
            read_average.append(I)
        elif not pulse_off:  #we turn on the pulse_off variable so we know that we are in between the pulses
            if read_average: # its not empty. This means we catched an event
                i = float(V_pulse)/np.average(read_average) #this actually calculates the resistance but is called i
                data_cycle_R_2.append([cycle,i]) #this saves the resistance
            #here we set the Boolean variables since we came to an end of an pulse
            read_average = []
            pulse_off = True #turn the pulse_off variable on - now we are between two pulses
            read_pulse_second = True #this is a variable to control the reading pulses - set it just once to true between the pulses  
            read_pulse_first = True
  
        if pulse_off and cycle != 1: #here we are in between the pulses and we employ the whole reading scheme
            start_read = pulse_end_time + time_at_zero
            #here we set the function generator to the correct reading parameters
            device_function_generator.set_pulse_period(0.5*read_time)
            device_function_generator.set_pulse_duty_cycles(99.9)       
            #these are conditions for triggering
            #they will just be called once (therefore the read_pulse_first and read_puls_second variables)
            if timestamp >= start_read and read_pulse_first:  #condition to trigger the first part of the bipolar reading pulse
                device_function_generator.set_offset_voltage(0.5*V_read)
                device_function_generator.set_waveform_polarity("NORM") 
                device_function_generator.set_low_voltage(0) 
                device_function_generator.set_high_voltage(V_read) 
                device_function_generator.trigger() # apply pulse
                read_pulse_first = False
                data_V_t_2.append([timestamp, V_read])
                data_V_t_2.append([timestamp + 0.5*read_time, V_read])
            elif timestamp >= start_read + 0.5*read_time and read_pulse_second:  #condition to trigger the second part of the bipolar reading pulse 
                device_function_generator.set_offset_voltage(-0.5*V_read)
                device_function_generator.set_waveform_polarity("INV") 
                device_function_generator.set_high_voltage(0) 
                device_function_generator.set_low_voltage(-V_read) 
                device_function_generator.trigger() # apply pulse
                read_pulse_second = False #now turn the read_pulse_second off so we trigger it just once
                data_V_t_2.append([timestamp, -V_read])
                data_V_t_2.append([timestamp + 0.5*read_time, -V_read])
                
            #now that we triggered the pulses we can record the data (I)
            #the current will be recorded at all times (not just once)
            timestamp = time.time()-t0
            if start_read <= timestamp <= start_read + read_time:
                read_average_post.append(abs(I))
            else:
                data_V_t_2.append([timestamp,V]) #V is actually just 0 - this saves the time_at_zero voltage
        if cycle == num_pulses+1 and timestamp >= pulse_end_time + 1.8*time_at_zero + read_time:
            measuring = False
        if GUI: #this visualizes the plots
            curve_I_t_2.setData(x=[k[0] for k in data_I_t_2], y=[k[1] for k in data_I_t_2], _callSync='off')
            curve_cycle_post_R_2.setData(x=[k[0] for k in data_cycle_post_R_2], y=[k[1] for k in data_cycle_post_R_2], _callSync='off')
            curve_cycle_R_2.setData(x=[k[0] for k in data_cycle_R_2], y=[k[1] for k in data_cycle_R_2], _callSync='off')
            curve_V_t_2.setData(x=[k[0] for k in data_V_t_2], y=[k[1] for k in data_V_t_2], _callSync='off')
    device_function_generator.turn_output_off()
    return [data_V_t_2,data_I_t_2,data_cycle_R_2,data_cycle_post_R_2_plus, data_cycle_post_R_2_minus] #here are the variable we are saving

def preforming_ramp(device,start_voltage,ramp_speed_1,top_voltage,hold_time,ramp_speed_2,end_voltage,compliance_current=0,new_row=False, GUI=True):
    device.reset()
    device.setup_current_measurement(1)
    if top_voltage>100:
        device.set_voltage_range(1000)
    else:
        device.set_voltage_range(100)
    if compliance_current is not 0:
        device.set_compliance_current(compliance_current)
    device.set_voltage(start_voltage)
    device.turn_output_on()
    device.init()
    data_V_I = []
    data_V_t = []
    data_I_t = []
    if GUI:
        # create an empty list in the remote process
        p1 = win.addPlot(title="Voltage vs. current")
        curve_V_I = p1.plot(pen='y')
        p1.setLabel('left', "Current", units='A')
        p1.setLabel('bottom', "Voltage", units='V')
        curve_V_I.setData(data_V_I, _callSync='off')

        p2 = win.addPlot(title="Voltage vs. time")
        curve_V_t = p2.plot(pen='y')
        p2.setLabel('left', "Voltage", units='V')
        p2.setLabel('bottom', "time", units='s')
        curve_V_t.setData(data_V_t, _callSync='off')

        p3 = win.addPlot(title="Current vs. time")
        curve_I_t = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_I_t.setData(data_I_t, _callSync='off')
      
        if new_row:
            win.nextRow()
    first_step_time = np.absolute(top_voltage-start_voltage)/np.absolute(ramp_speed_1)
    v0 = start_voltage
    t0 = time.time() # measurement start time
    old_time = 0 # to remember the timestamp in the (t-1) cycle. You need to find out the time for each loop
    timestamp = 0
    keithley_time0 = 0 # Keithley saves also a time with each measurement
    first_time = True
    while True:
        I = device.get_value()
        V_actual = device.get_voltage()
        if first_time:
            keithley_time0 = I[1]
            first_time = False
        keithley_time = I[1]-keithley_time0
        old_time = timestamp
        device.set_voltage(v0)
        timestamp = time.time()-t0
        if timestamp < first_step_time:
            delta_V = ramp_speed_1*(timestamp-old_time)*float(old_time>0)
        elif timestamp >= first_step_time and timestamp-first_step_time < hold_time:
            delta_V=0.0
            if v0 is not top_voltage: # Did we reach the hold voltage? Adjust if not so...
                delta_V = top_voltage-v0
        else:
            delta_V = ramp_speed_2*(timestamp-old_time)*float(old_time>0)
            if (v0 < end_voltage and ramp_speed_2 < 0) or (v0 > end_voltage and ramp_speed_2 > 0):
                device.set_voltage(end_voltage)
                break
        v0=v0+delta_V
        if V_actual is None: # Means we are working on keithley_6517B
            V_actual = v0
        else: # Means we are working on keithley_26xxB
            keithley_time = timestamp
        data_I_t.append([I[0],keithley_time])
        data_V_I.append([V_actual,I[0]])
        data_V_t.append([V_actual,timestamp])
        if GUI:
            curve_I_t.setData(x=[k[1] for k in data_I_t], y=[k[0] for k in data_I_t], _callSync='off')
            curve_V_I.setData(x=[k[0] for k in data_V_I], y=[k[1] for k in data_V_I], _callSync='off')
            curve_V_t.setData(x=[k[1] for k in data_V_t], y=[k[0] for k in data_V_t], _callSync='off')
    device.turn_output_off()
    return [data_V_I,data_V_t,data_I_t]
    
def preforming_ramp_with_current_hold_time(device,start_voltage,ramp_speed_1,top_voltage,hold_time,ramp_speed_2,end_voltage,compliance_current=0,trigger_current=0,trigger_hold_time=0,new_row=False,GUI=True):
    device.reset()
    device.setup_current_measurement(1)
    if top_voltage>100:
        device.set_voltage_range(1000)
    else:
        device.set_voltage_range(100)
    if compliance_current is not 0:
        device.set_compliance_current(compliance_current)
        if trigger_current is not 0:
            if trigger_current >= compliance_current:
                print "the trigger_current you specified will never be reached since it is bigger than the allowed maximum current in compliance_current"
                return
    device.set_voltage(start_voltage)
    device.turn_output_on()
    device.init()
    data_V_I = []
    data_V_t = []
    data_I_t = []
    if GUI:
        # create an empty list in the remote process
        p1 = win.addPlot(title="Voltage vs. current")
        curve_V_I = p1.plot(pen='y')
        p1.setLabel('left', "Current", units='A')
        p1.setLabel('bottom', "Voltage", units='V')
        curve_V_I.setData(data_V_I, _callSync='off')

        p2 = win.addPlot(title="Voltage vs. time")
        curve_V_t = p2.plot(pen='y')
        p2.setLabel('left', "Voltage", units='V')
        p2.setLabel('bottom', "time", units='s')
        curve_V_t.setData(data_V_t, _callSync='off')

        p3 = win.addPlot(title="Current vs. time")
        curve_I_t = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_I_t.setData(data_I_t, _callSync='off')
      
        if new_row:
            win.nextRow()
    first_step_time = np.absolute(top_voltage-start_voltage)/np.absolute(ramp_speed_1)
    v0 = start_voltage
    t0 = time.time() # measurement start time
    old_time = 0 # to remember the timestamp in the (t-1) cycle. You need to find out the time for each loop
    timestamp = 0
    keithley_time0 = 0 # Keithley saves also a time with each measurement
    triggered_remaining_time = 0 # this counter time tells you how many seconds have to pass till we will be done
    first_time = True
    trigger_armed = False
    while True:
        I = device.get_value()
        V_actual = device.get_voltage()
        if first_time:
            keithley_time0 = I[1]
            first_time = False
        if not first_time and trigger_current is not 0:
            if I[0] >= trigger_current and not trigger_armed:
                triggered_remaining_time = timestamp+trigger_hold_time
                trigger_armed = True
        keithley_time = I[1]-keithley_time0
        old_time = timestamp
        device.set_voltage(v0)
        timestamp = time.time()-t0
        if timestamp > triggered_remaining_time and triggered_remaining_time is not 0:
            break
        if timestamp < first_step_time:
            delta_V = ramp_speed_1*(timestamp-old_time)*float(old_time>0)
        elif timestamp >= first_step_time and timestamp-first_step_time < hold_time:
            delta_V=0.0
            if v0 is not top_voltage: # Did we reach the hold voltage? Adjust if not so...
                delta_V = top_voltage-v0
        else:
            delta_V = ramp_speed_2*(timestamp-old_time)*float(old_time>0)
            if (v0 < end_voltage and ramp_speed_2 < 0) or (v0 > end_voltage and ramp_speed_2 > 0):
                device.set_voltage(end_voltage)
                break
        v0=v0+delta_V
        if V_actual is None: # Means we are working on keithley_6517B
            V_actual = v0
        else: # Means we are working on keithley_26xxB
            keithley_time = timestamp
        data_I_t.append([I[0],keithley_time])
        data_V_I.append([V_actual,I[0]])
        data_V_t.append([V_actual,timestamp])
        if GUI:
            curve_I_t.setData(x=[k[1] for k in data_I_t], y=[k[0] for k in data_I_t], _callSync='off')
            curve_V_I.setData(x=[k[0] for k in data_V_I], y=[k[1] for k in data_V_I], _callSync='off')
            curve_V_t.setData(x=[k[1] for k in data_V_t], y=[k[0] for k in data_V_t], _callSync='off')
    device.turn_output_off()
    return [data_V_I,data_V_t,data_I_t]

def preforming_ramp_with_current_limit(device,start_voltage,ramp_speed_1,top_voltage,hold_time,ramp_speed_2,end_voltage,stop_current,new_row=False, GUI=True):
    device.reset()
    device.setup_current_measurement(1)
    if top_voltage>100:
        device.set_voltage_range(1000)
    else:
        device.set_voltage_range(100)
    device.set_voltage(start_voltage)
    device.turn_output_on()
    device.init()
    data_V_I = []
    data_V_t = []
    data_I_t = []
    if GUI:
        # create an empty list in the remote process
        p1 = win.addPlot(title="Voltage vs. current")
        curve_V_I = p1.plot(pen='y')
        p1.setLabel('left', "Current", units='A')
        p1.setLabel('bottom', "Voltage", units='V')
        curve_V_I.setData(data_V_I, _callSync='off')

        p2 = win.addPlot(title="Voltage vs. time")
        curve_V_t = p2.plot(pen='y')
        p2.setLabel('left', "Voltage", units='V')
        p2.setLabel('bottom', "time", units='s')
        curve_V_t.setData(data_V_t, _callSync='off')

        p3 = win.addPlot(title="Current vs. time")
        curve_I_t = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_I_t.setData(data_I_t, _callSync='off')
      
        if new_row:
            win.nextRow()
    first_step_time = np.absolute(top_voltage-start_voltage)/np.absolute(ramp_speed_1)
    v0 = start_voltage
    t0 = time.time() # measurement start time
    old_time = 0 # to remember the timestamp in the (t-1) cycle. You need to find out the time for each loop
    timestamp = 0
    keithley_time0 = 0 # Keithley saves also a time with each measurement
    first_time = True
    while True:
        I = device.get_value()
        if first_time:
            keithley_time0 = I[1]
            first_time = False        
        keithley_time = I[1]-keithley_time0
        old_time = timestamp
        device.set_voltage(v0)
        timestamp = time.time()-t0
        if timestamp < first_step_time:
            delta_V = ramp_speed_1*(timestamp-old_time)*float(old_time>0)
        elif timestamp >= first_step_time and timestamp-first_step_time < hold_time:
            delta_V=0.0
            if v0 is not top_voltage: # Did we reach the hold voltage? Adjust if not so...
                delta_V = top_voltage-v0
        else:
            delta_V = ramp_speed_2*(timestamp-old_time)*float(old_time>0)
            if (v0 < end_voltage and ramp_speed_2 < 0) or (v0 > end_voltage and ramp_speed_2 > 0):
                device.set_voltage(end_voltage)
                break
        v0=v0+delta_V
        V = v0
        data_I_t.append([I[0],keithley_time])
        data_V_I.append([V,I[0]])
        data_V_t.append([V,timestamp])
        if GUI:
            curve_I_t.setData(x=[k[1] for k in data_I_t], y=[k[0] for k in data_I_t], _callSync='off')
            curve_V_I.setData(x=[k[0] for k in data_V_I], y=[k[1] for k in data_V_I], _callSync='off')
            curve_V_t.setData(x=[k[1] for k in data_V_t], y=[k[0] for k in data_V_t], _callSync='off')
        if I[0] >= stop_current:
            break
    device.turn_output_off()
    return [data_V_I,data_V_t,data_I_t]
    
def cycling(device,start_voltage,ramp_speed_1,top_voltage,top_hold_time,ramp_speed_2,bottom_voltage,bottom_hold_time,end_voltage,n,compliance_current_pos=0,compliance_current_neg=0,new_row=False, GUI=True):
    device.reset()
    device.setup_current_measurement(1)
    if top_voltage>100:
        device.set_voltage_range(1000)
    else:
        device.set_voltage_range(100)
    device.set_voltage(start_voltage)
    device.turn_output_on()
    device.init()
    data_V_I = []
    data_V_t = []
    data_I_t = []
    if GUI:
        # create an empty list in the remote process
        p1 = win.addPlot(title="Voltage vs. current")
        curve_V_I = p1.plot(pen='y')
        p1.setLabel('left', "Current", units='A')
        p1.setLabel('bottom', "Voltage", units='V')
        curve_V_I.setData(data_V_I, _callSync='off')

        p2 = win.addPlot(title="Voltage vs. time")
        curve_V_t = p2.plot(pen='y')
        p2.setLabel('left', "Voltage", units='V')
        p2.setLabel('bottom', "time", units='s')
        curve_V_t.setData(data_V_t, _callSync='off')

        p3 = win.addPlot(title="Current vs. time")
        curve_I_t = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_I_t.setData(data_I_t, _callSync='off')
      
        if new_row:
            win.nextRow()
    first_step_time = np.absolute(top_voltage-start_voltage)/np.absolute(ramp_speed_1)
    second_step_time = np.absolute(top_voltage-bottom_voltage)/np.absolute(ramp_speed_2)
    last_step_time = np.absolute(bottom_voltage-end_voltage)/np.absolute(ramp_speed_1)
    total_time_needed = first_step_time+top_hold_time+second_step_time+bottom_hold_time+last_step_time
    v0 = start_voltage
    t0 = time.time() # measurement start time
    old_time = 0 # to remember the timestamp in the (t-1) cycle. You need to find out the time for each loop
    timestamp = 0
    keithley_time0 = 0 # Keithley saves also a time with each measurement
    time_at_end = 0
    first_time = True
    for u in range(n):
        in_first_cc = True
        if compliance_current_pos is not 0:
            device.set_compliance_current(np.absolute(compliance_current_pos))
        while timestamp < total_time_needed+time_at_end:
            device.set_voltage(v0)
            I = device.get_value()
            V_actual = device.get_voltage()
            if first_time: # first time
                keithley_time0 = I[1]
                first_time = False
            keithley_time = I[1]-keithley_time0
            old_time = timestamp
            timestamp = time.time()-t0
            if timestamp < first_step_time+time_at_end:
                delta_V = ramp_speed_1*(timestamp-old_time)*float(old_time>0)
            elif timestamp >= first_step_time+time_at_end and timestamp < first_step_time+top_hold_time+time_at_end: # means we are in the top hold regime
                delta_V=0.0
                if v0 is not top_voltage: # Did we reach the top hold voltage? Little adjustment if not so...
                    delta_V = top_voltage-v0
            elif timestamp >= first_step_time+top_hold_time+time_at_end and timestamp < first_step_time+top_hold_time+second_step_time+time_at_end: # means we are in the second ramp regime
                delta_V = ramp_speed_2*(timestamp-old_time)*float(old_time>0)
                if compliance_current_neg is not 0 and in_first_cc and timestamp >= first_step_time+top_hold_time+second_step_time/2.0+time_at_end:
                    device.set_compliance_current(np.absolute(compliance_current_neg))
                    in_first_cc = False
            elif timestamp >= first_step_time+top_hold_time+second_step_time+time_at_end and timestamp < first_step_time+top_hold_time+second_step_time+bottom_hold_time+time_at_end: # means we are in the bottom hold regime
                delta_V=0.0
                if v0 is not bottom_voltage: # Did we reach the bottom hold voltage? Little adjustment if not so...
                    delta_V = bottom_voltage-v0
            else: # means we are in the last ramping up regime
                delta_V = ramp_speed_1*(timestamp-old_time)*float(old_time>0)
                if (v0 < end_voltage and ramp_speed_1 < 0) or (v0 > end_voltage and ramp_speed_1 > 0) or (bottom_voltage is end_voltage):
                    device.set_voltage(end_voltage)
                    delta_V = end_voltage-v0
            v0=v0+delta_V
            if V_actual is None: # Means we are working on keithley_6517B
                V_actual = v0
            else: # Means we are working on keithley_26xxB
                keithley_time = timestamp
            data_I_t.append([I[0],keithley_time])
            data_V_I.append([V_actual,I[0],int(u+1)])
            data_V_t.append([V_actual,timestamp])
            if GUI:
                curve_I_t.setData(x=[k[1] for k in data_I_t], y=[k[0] for k in data_I_t], _callSync='off')
                curve_V_I.setData(x=[k[0] for k in data_V_I], y=[k[1] for k in data_V_I], _callSync='off')
                curve_V_t.setData(x=[k[1] for k in data_V_t], y=[k[0] for k in data_V_t], _callSync='off')
        time_at_end = timestamp
        device.set_voltage(end_voltage)
    device.turn_output_off()
    return [data_V_I,data_V_t,data_I_t]
    
def cycling_current(device,start,ramp_speed_1,top,top_hold_time,ramp_speed_2,bottom,bottom_hold_time,end,n,maximum_voltage,new_row=False,GUI=True):
    device.reset()
    device.setup_current_measurement(1)
    device.set_voltage(maximum_voltage)
    device.set_compliance_current(start)
    device.turn_output_on()
    device.init()
    data_V_I = []
    data_V_t = []
    data_I_t = []
    if GUI:
        # create an empty list in the remote process
        p1 = win.addPlot(title="Voltage vs. current")
        curve_V_I = p1.plot(pen='y')
        p1.setLabel('left', "Current", units='A')
        p1.setLabel('bottom', "Voltage", units='V')
        curve_V_I.setData(data_V_I, _callSync='off')

        p2 = win.addPlot(title="Voltage vs. time")
        curve_V_t = p2.plot(pen='y')
        p2.setLabel('left', "Voltage", units='V')
        p2.setLabel('bottom', "time", units='s')
        curve_V_t.setData(data_V_t, _callSync='off')

        p3 = win.addPlot(title="Current vs. time")
        curve_I_t = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_I_t.setData(data_I_t, _callSync='off')
      
        if new_row:
            win.nextRow()
    first_step_time = np.absolute(top-start)/np.absolute(ramp_speed_1)
    second_step_time = np.absolute(top-bottom)/np.absolute(ramp_speed_2)
    last_step_time = np.absolute(bottom-end)/np.absolute(ramp_speed_1)
    total_time_needed = first_step_time+top_hold_time+second_step_time+bottom_hold_time+last_step_time
    v0 = start
    t0 = time.time() # measurement start time
    old_time = 0 # to remember the timestamp in the (t-1) cycle. You need to find out the time for each loop
    timestamp = 0
    keithley_time0 = 0 # Keithley saves also a time with each measurement
    time_at_end = 0
    first_time = True
    for u in range(n):
        while timestamp < total_time_needed+time_at_end:
            device.set_compliance_current(v0)
            I = device.get_value()
            V_actual = device.get_voltage()
            if first_time: # first time
                keithley_time0 = I[1]
                first_time = False
            keithley_time = I[1]-keithley_time0
            old_time = timestamp
            timestamp = time.time()-t0
            if timestamp < first_step_time+time_at_end:
                delta_V = ramp_speed_1*(timestamp-old_time)*float(old_time>0)
            elif timestamp >= first_step_time+time_at_end and timestamp < first_step_time+top_hold_time+time_at_end: # means we are in the top hold regime
                delta_V=0.0
                if v0 is not top: # Did we reach the top hold voltage? Little adjustment if not so...
                    delta_V = top-v0
            elif timestamp >= first_step_time+top_hold_time+time_at_end and timestamp < first_step_time+top_hold_time+second_step_time+time_at_end: # means we are in the second ramp regime
                delta_V = ramp_speed_2*(timestamp-old_time)*float(old_time>0)
            elif timestamp >= first_step_time+top_hold_time+second_step_time+time_at_end and timestamp < first_step_time+top_hold_time+second_step_time+bottom_hold_time+time_at_end: # means we are in the bottom hold regime
                delta_V=0.0
                if v0 is not bottom: # Did we reach the bottom hold voltage? Little adjustment if not so...
                    delta_V = bottom-v0
            else: # means we are in the last ramping up regime
                delta_V = ramp_speed_1*(timestamp-old_time)*float(old_time>0)
                if (v0 < end and ramp_speed_1 < 0) or (v0 > end and ramp_speed_1 > 0) or (bottom is end):
                    device.set_compliance_current(end)
                    delta_V = end-v0
            v0=v0+delta_V
            if V_actual is None: # Means we are working on keithley_6517B
                print "This function cannot be run with a device that does not support compliance currents! Function aborted"
                return
            else: # Means we are working on keithley_26xxB
                keithley_time = timestamp
            data_I_t.append([I[0],keithley_time])
            data_V_I.append([V_actual,I[0],int(u+1)])
            data_V_t.append([V_actual,timestamp])
            if GUI:
                curve_I_t.setData(x=[k[1] for k in data_I_t], y=[k[0] for k in data_I_t], _callSync='off')
                curve_V_I.setData(x=[k[0] for k in data_V_I], y=[k[1] for k in data_V_I], _callSync='off')
                curve_V_t.setData(x=[k[1] for k in data_V_t], y=[k[0] for k in data_V_t], _callSync='off')
        time_at_end = timestamp
        device.set_compliance_current(end)
    device.turn_output_off()
    return [data_V_I,data_V_t,data_I_t]
    
def cycling_unipolar(device,start_voltage,ramp_speed_1,set_voltage,set_hold_time,compliance_current,ramp_speed_2,wait_before_reset_time,reset_voltage,reset_ramp_rate,reset_hold_time,n,new_row=False, GUI=True):
    device.reset()
    device.setup_current_measurement(1)
    if set_voltage>100:
        device.set_voltage_range(1000)
    else:
        device.set_voltage_range(100)
    device.set_voltage(start_voltage)
    device.turn_output_on()
    device.init()
    data_V_I = []
    data_V_t = []
    data_I_t = []
    if GUI:
        # create an empty list in the remote process
        p1 = win.addPlot(title="Voltage vs. current")
        curve_V_I = p1.plot(pen='y')
        p1.setLabel('left', "Current", units='A')
        p1.setLabel('bottom', "Voltage", units='V')
        curve_V_I.setData(data_V_I, _callSync='off')

        p2 = win.addPlot(title="Voltage vs. time")
        curve_V_t = p2.plot(pen='y')
        p2.setLabel('left', "Voltage", units='V')
        p2.setLabel('bottom', "time", units='s')
        curve_V_t.setData(data_V_t, _callSync='off')

        p3 = win.addPlot(title="Current vs. time")
        curve_I_t = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_I_t.setData(data_I_t, _callSync='off')
      
        if new_row:
            win.nextRow()
    first_step_time = np.absolute(set_voltage-start_voltage)/np.absolute(ramp_speed_1)
    second_step_time = np.absolute(set_voltage-start_voltage)/np.absolute(ramp_speed_2)
    reset_step_time = np.absolute(reset_voltage-start_voltage)/np.absolute(reset_ramp_rate)
    total_time_needed = first_step_time+set_hold_time+second_step_time+wait_before_reset_time+2*reset_step_time+reset_hold_time
    v0 = start_voltage
    t0 = time.time() # measurement start time
    old_time = 0 # to remember the timestamp in the (t-1) cycle. You need to find out the time for each loop
    timestamp = 0
    time_at_end = 0
    for u in range(n):
        in_first_cc = True
        device.set_compliance_current(np.absolute(compliance_current))
        while timestamp < total_time_needed+time_at_end:
            device.set_voltage(v0)
            I = device.get_value()
            V_actual = device.get_voltage()
            old_time = timestamp
            timestamp = time.time()-t0
            if timestamp < first_step_time+time_at_end:
                delta_V = ramp_speed_1*(timestamp-old_time)*float(old_time>0)
            elif timestamp >= first_step_time+time_at_end and timestamp < first_step_time+set_hold_time+time_at_end: # means we are in the top hold regime
                delta_V=0.0
                if v0 is not set_voltage: # Did we reach the set voltage? Little adjustment if not so...
                    delta_V = set_voltage-v0
            elif timestamp >= first_step_time+set_hold_time+time_at_end and timestamp < first_step_time+set_hold_time+second_step_time+time_at_end: # means we are in the second ramp regime
                delta_V = ramp_speed_2*(timestamp-old_time)*float(old_time>0)
            elif timestamp >= first_step_time+set_hold_time+second_step_time+time_at_end and timestamp < first_step_time+set_hold_time+second_step_time+wait_before_reset_time+time_at_end: # means we are in the wait_before_reset_time regime
                delta_V=0.0
                if in_first_cc:
                    device.set_compliance_current(0)
                    in_first_cc = False
                if v0 is not start_voltage: # Did we reach the start voltage? Little adjustment if not so...
                    delta_V = start_voltage-v0
            elif timestamp >= first_step_time+set_hold_time+second_step_time+wait_before_reset_time+time_at_end and timestamp < first_step_time+set_hold_time+second_step_time+wait_before_reset_time+reset_step_time+time_at_end: # means we are in the reset_step regime
                delta_V = reset_ramp_rate*(timestamp-old_time)*float(old_time>0)
                if in_first_cc:
                    device.set_compliance_current(0)
                    in_first_cc = False
            elif timestamp >= first_step_time+set_hold_time+second_step_time+wait_before_reset_time+reset_step_time+time_at_end and timestamp < first_step_time+set_hold_time+second_step_time+wait_before_reset_time+reset_step_time+reset_hold_time+time_at_end: # means we are in the reset_hold_time regime
                delta_V = 0.0
                if v0 is not reset_voltage: # Did we reach the reset voltage? Little adjustment if not so...
                    delta_V = reset_voltage-v0
            else: # means we are in the last ramping down regime
                delta_V = -reset_ramp_rate*(timestamp-old_time)*float(old_time>0)
                if v0 < start_voltage:
                    device.set_voltage(start_voltage)
                    delta_V = start_voltage-v0
            v0=v0+delta_V
            data_I_t.append([I[0],timestamp])
            data_V_I.append([V_actual,I[0],int(u+1)])
            data_V_t.append([V_actual,timestamp])
            if GUI:
                curve_I_t.setData(x=[k[1] for k in data_I_t], y=[k[0] for k in data_I_t], _callSync='off')
                curve_V_I.setData(x=[k[0] for k in data_V_I], y=[k[1] for k in data_V_I], _callSync='off')
                curve_V_t.setData(x=[k[1] for k in data_V_t], y=[k[0] for k in data_V_t], _callSync='off')
        time_at_end = timestamp
        v0 = start_voltage
        device.set_voltage(v0)
    device.turn_output_off()
    return [data_V_I,data_V_t,data_I_t]
  
def cycling_two_channels(device,start_voltage_1,start_voltage_2,ramp_speed_1_1,ramp_speed_1_2,top_voltage_1,top_voltage_2,top_hold_time_1,top_hold_time_2,ramp_speed_2_1,ramp_speed_2_2,bottom_voltage_1,bottom_voltage_2,bottom_hold_time_1,bottom_hold_time_2,end_voltage_1,end_voltage_2,n_1,n_2,compliance_current_pos_1=0,compliance_current_pos_2=0,compliance_current_neg_1=0,compliance_current_neg_2=0,new_row=False,GUI=True):
    device.reset()
    device.setup_current_measurement(1,channel="A")
    device.setup_current_measurement(1,channel="B")
    device.set_voltage(start_voltage_1,channel="A")
    device.set_voltage(start_voltage_2,channel="B")
    device.turn_output_on("A")
    device.turn_output_on("B")
    device.init()
    data_V_I_1 = []
    data_V_t_1 = []
    data_I_t_1 = []
    data_V_I_2 = []
    data_V_t_2 = []
    data_I_t_2 = []
    if GUI:
        # create an empty list in the remote process
        p1 = win.addPlot(title="Voltage vs. current Channel A")
        curve_V_I_1 = p1.plot(pen='y')
        p1.setLabel('left', "Current", units='A')
        p1.setLabel('bottom', "Voltage", units='V')
        curve_V_I_1.setData(data_V_I_1, _callSync='off')

        p2 = win.addPlot(title="Voltage vs. time Channel A")
        curve_V_t_1 = p2.plot(pen='y')
        p2.setLabel('left', "Voltage", units='V')
        p2.setLabel('bottom', "time", units='s')
        curve_V_t_1.setData(data_V_t_1, _callSync='off')

        p3 = win.addPlot(title="Current vs. time Channel A")
        curve_I_t_1 = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_I_t_1.setData(data_I_t_1, _callSync='off')
        
        win.nextRow()
        p1 = win.addPlot(title="Voltage vs. current Channel B")
        curve_V_I_2 = p1.plot(pen='y')
        p1.setLabel('left', "Current", units='A')
        p1.setLabel('bottom', "Voltage", units='V')
        curve_V_I_2.setData(data_V_I_2, _callSync='off')

        p2 = win.addPlot(title="Voltage vs. time Channel B")
        curve_V_t_2 = p2.plot(pen='y')
        p2.setLabel('left', "Voltage", units='V')
        p2.setLabel('bottom', "time", units='s')
        curve_V_t_2.setData(data_V_t_2, _callSync='off')

        p3 = win.addPlot(title="Current vs. time Channel B")
        curve_I_t_2 = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_I_t_2.setData(data_I_t_2, _callSync='off')
        if new_row:
            win.nextRow()
    first_step_time_1 = np.absolute(top_voltage_1-start_voltage_1)/np.absolute(ramp_speed_1_1)
    second_step_time_1 = np.absolute(top_voltage_1-bottom_voltage_1)/np.absolute(ramp_speed_2_1)
    last_step_time_1 = np.absolute(bottom_voltage_1-end_voltage_1)/np.absolute(ramp_speed_1_1)
    total_time_needed_1 = first_step_time_1+top_hold_time_1+second_step_time_1+bottom_hold_time_1+last_step_time_1
    first_step_time_2 = np.absolute(top_voltage_2-start_voltage_2)/np.absolute(ramp_speed_1_2)
    second_step_time_2 = np.absolute(top_voltage_2-bottom_voltage_2)/np.absolute(ramp_speed_2_2)
    last_step_time_2 = np.absolute(bottom_voltage_2-end_voltage_2)/np.absolute(ramp_speed_1_2)
    total_time_needed_2 = first_step_time_2+top_hold_time_2+second_step_time_2+bottom_hold_time_2+last_step_time_2
    v0_1 = start_voltage_1
    v0_2 = start_voltage_2
    t0 = time.time() # measurement start time
    old_time = 0 # to remember the timestamp in the (t-1) cycle. You need to find out the time for each loop
    timestamp = 0
    keithley_time0 = 0 # Keithley saves also a time with each measurement
    time_at_end = 0
    first_time = True
    both_channels_finished = False
    new_u_channel_A = False
    new_u_channel_B = False
    u_1 = 0
    u_2 = 0
    while not both_channels_finished:
        if u_1 < n_1 and new_u_channel_A:
            in_first_cc_A = True
            new_u_channel_A = False
            if compliance_current_pos_1 is not 0:
                device.set_compliance_current(np.absolute(compliance_current_pos_1),"A")
        if u_1 >= n_1:
            device.channel_A_done = True
            device.turn_output_off("A")
        if u_2 < n_2 and new_u_channel_B:
            in_first_cc_B = True
            new_u_channel_B = False
            if compliance_current_pos_2 is not 0:
                device.set_compliance_current(np.absolute(compliance_current_pos_1),"B")
        if u_2 >= n_2:
            device.channel_B_done = True
            device.turn_output_off("B")
        if u_2 >= n_2 and u_1 >= n_1:
            both_channels_finished = True
        device.set_voltage(v0_1,"A")
        device.set_voltage(v0_2,"B")
        I_1 = device.get_value(None,"A")
        I_2 = device.get_value(None,"B")
        V_actual_1 = device.get_voltage("A")
        V_actual_2 = device.get_voltage("B")
        if first_time: # first time
            keithley_time0 = I_1[1]
            first_time = False
        keithley_time = I_1[1]-keithley_time0
        old_time = timestamp
        timestamp = time.time()-t0
        if timestamp < first_step_time_1+time_at_end_1:
            delta_V_1 = ramp_speed_1_1*(timestamp-old_time)*float(old_time>0)
        elif timestamp >= first_step_time_1+time_at_end_1 and timestamp < first_step_time_1+top_hold_time_1+time_at_end_1: # means we are in the top hold regime
            delta_V_1=0.0
            if v0_1 is not top_voltage_1: # Did we reach the top hold voltage? Little adjustment if not so...
                delta_V_1 = top_voltage_1-v0_1
        elif timestamp >= first_step_time_1+top_hold_time_1+time_at_end_1 and timestamp < first_step_time_1+top_hold_time_1+second_step_time_1+time_at_end_1: # means we are in the second ramp regime
            delta_V_1 = ramp_speed_2_1*(timestamp-old_time)*float(old_time>0)
            if compliance_current_neg_1 is not 0 and in_first_cc_A and timestamp >= first_step_time_1+top_hold_time_1+second_step_time_1/2.0+time_at_end_1:
                device.set_compliance_current(np.absolute(compliance_current_neg_1),"A")
                in_first_cc_A = False
        elif timestamp >= first_step_time_1+top_hold_time_1+second_step_time_1+time_at_end_1 and timestamp < first_step_time_1+top_hold_time_1+second_step_time_1+bottom_hold_time_1+time_at_end_1: # means we are in the bottom hold regime
            delta_V_1=0.0
            if v0_1 is not bottom_voltage_1: # Did we reach the bottom hold voltage? Little adjustment if not so...
                delta_V_1 = bottom_voltage_1-v0_1
        else: # means we are in the last ramping up regime
            delta_V_1 = ramp_speed_1_1*(timestamp-old_time)*float(old_time>0)
            if (v0_1 < end_voltage_1 and ramp_speed_1_1 < 0) or (v0_1 > end_voltage_1 and ramp_speed_1_1 > 0) or (bottom_voltage_1 is end_voltage_1):
                device.set_voltage(end_voltage_1,"A")
                delta_V_1 = end_voltage_1-v0_1
        v0_1=v0_1+delta_V_1
        if timestamp < first_step_time_2+time_at_end_2:
            delta_V_2 = ramp_speed_1_2*(timestamp-old_time)*float(old_time>0)
        elif timestamp >= first_step_time_2+time_at_end_2 and timestamp < first_step_time_2+top_hold_time_2+time_at_end_2: # means we are in the top hold regime
            delta_V_2=0.0
            if v0_2 is not top_voltage_2: # Did we reach the top hold voltage? Little adjustment if not so...
                delta_V_2 = top_voltage_2-v0_2
        elif timestamp >= first_step_time_2+top_hold_time_2+time_at_end_2 and timestamp < first_step_time_2+top_hold_time_2+second_step_time_2+time_at_end_2: # means we are in the second ramp regime
            delta_V_2 = ramp_speed_2_2*(timestamp-old_time)*float(old_time>0)
            if compliance_current_neg_2 is not 0 and in_first_cc_B and timestamp >= first_step_time_2+top_hold_time_2+second_step_time_2/2.0+time_at_end_2:
                device.set_compliance_current(np.absolute(compliance_current_neg_2),"B")
                in_first_cc_B = False
        elif timestamp >= first_step_time_2+top_hold_time_2+second_step_time_2+time_at_end_2 and timestamp < first_step_time_2+top_hold_time_2+second_step_time_2+bottom_hold_time_2+time_at_end_2: # means we are in the bottom hold regime
            delta_V_2=0.0
            if v0_2 is not bottom_voltage_2: # Did we reach the bottom hold voltage? Little adjustment if not so...
                delta_V_2 = bottom_voltage_2-v0_2
        else: # means we are in the last ramping up regime
            delta_V_2 = ramp_speed_1_2*(timestamp-old_time)*float(old_time>0)
            if (v0_2 < end_voltage_2 and ramp_speed_1_2 < 0) or (v0_2 > end_voltage_2 and ramp_speed_1_2 > 0) or (bottom_voltage_2 is end_voltage_2):
                device.set_voltage(end_voltage_2,"B")
                delta_V_2 = end_voltage_2-v0_2
        v0_2=v0_2+delta_V_2
        keithley_time = timestamp
        data_I_t_1.append([I_1[0],keithley_time])
        data_V_I_1.append([V_actual_1,I_1[0],int(u_1+1)])
        data_V_t_1.append([V_actual_1,timestamp])
        data_I_t_2.append([I_2[0],keithley_time])
        data_V_I_2.append([V_actual_2,I_2[0],int(u_2+1)])
        data_V_t_2.append([V_actual_2,timestamp])
        if GUI:
            curve_I_t_1.setData(x=[k[1] for k in data_I_t_1], y=[k[0] for k in data_I_t_1], _callSync='off')
            curve_V_I_1.setData(x=[k[0] for k in data_V_I_1], y=[k[1] for k in data_V_I_1], _callSync='off')
            curve_V_t_1.setData(x=[k[1] for k in data_V_t_1], y=[k[0] for k in data_V_t_1], _callSync='off')
            curve_I_t_2.setData(x=[k[1] for k in data_I_t_2], y=[k[0] for k in data_I_t_2], _callSync='off')
            curve_V_I_2.setData(x=[k[0] for k in data_V_I_2], y=[k[1] for k in data_V_I_2], _callSync='off')
            curve_V_t_2.setData(x=[k[1] for k in data_V_t_2], y=[k[0] for k in data_V_t_2], _callSync='off')
        if timestamp > total_time_needed_1*(u_1+1):
            time_at_end_1 = timestamp
            device.set_voltage(end_voltage_1,"A")
            u_1 = u_1+1
            new_u_channel_A = True
        if timestamp > total_time_needed_2*(u_2+1):
            time_at_end_2 = timestamp
            device.set_voltage(end_voltage_2,"B")
            u_2 = u_2+1
            new_u_channel_B = True
    device.turn_output_off()
    return [data_V_I_1,data_V_t_1,data_I_t_1,data_V_I_2,data_V_t_2,data_I_t_2]
    
def voltage_logger(device,total_measurement_time,bias_current=0,new_row=False, GUI=True):
    device.reset()
    device.setup_voltage_measurement()
    if bias_current is not 0:
        device.turn_output_off()
        device.set_current(bias_current)
        device.turn_output_on()
    if device.get_id() is not "keithley_6517B": # the high resistance meter is the only device where the output does not need to be turned on to measure only
        device.turn_output_on()
    data_V_t = []
    if GUI:
        # create an empty list in the remote process
        p3 = win.addPlot(title="Voltage vs. time")
        curve_V_t = p3.plot(pen='y')
        p3.setLabel('left', "Voltage", units='V')
        p3.setLabel('bottom', "time", units='s')
        curve_V_t.setData(data_V_t, _callSync='off')
        if new_row:
            win.nextRow()
    t0 = time.time() # measurement start time
    while time.time()-t0 < total_measurement_time:
        V = device.get_value()
        time_val = time.time() - t0
        data_V_t.append([V[0],time_val])
        if GUI:
            curve_V_t.setData(x=[k[1] for k in data_V_t], y=[k[0] for k in data_V_t], _callSync='off')
    return [data_V_t]
    
def current_logger(device,total_measurement_time,bias_voltage=0,new_row=False, GUI=True):
    device.reset()
    device.setup_current_measurement()
    if bias_voltage is not 0:
        device.turn_output_off()
        device.set_voltage(bias_voltage)
        device.turn_output_on()
    if device.get_id() is not "keithley_6517B": # the high resistance meter is the only device where the output does not need to be turned on to measure only
        device.turn_output_on()
    data_I_t = []
    if GUI:
        # create an empty list in the remote process
        p3 = win.addPlot(title="Current vs. time")
        curve_I_t = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_I_t.setData(data_I_t, _callSync='off')
        if new_row:
            win.nextRow()
    t0 = time.time() # measurement start time
    while time.time()-t0 < total_measurement_time:
        I = device.get_value()
        time_val = time.time() - t0
        data_I_t.append([I[0],time_val])
        if GUI:
            curve_I_t.setData(x=[k[1] for k in data_I_t], y=[k[0] for k in data_I_t], _callSync='off')
    if bias_voltage is not 0:
        device.turn_output_off()
    return [data_I_t]
 
def resistance_2w_logger(device,total_measurement_time,new_row=False, GUI=True):
    device.reset()
    device.setup_2w_resistance_measurement()
    data_R_t = []
    if GUI:
        # create an empty list in the remote process
        p3 = win.addPlot(title="Resistance vs. time")
        curve_R_t = p3.plot(pen='y')
        p3.setLabel('left', "Resistance", units='Ohm')
        p3.setLabel('bottom', "time", units='s')
        curve_R_t.setData(data_R_t, _callSync='off')
        if new_row:
            win.nextRow()
    t0 = time.time() # measurement start time
    while time.time()-t0 < total_measurement_time:
        R = device.get_value()
        time_val = time.time() - t0
        data_R_t.append([R[0],time_val])
        if GUI:
            curve_R_t.setData(x=[k[1] for k in data_R_t], y=[k[0] for k in data_R_t], _callSync='off')
    return [data_R_t]
 
def resistance_4w_logger(device,total_measurement_time,new_row=False, GUI=True):
    device.reset()
    device.setup_4w_resistance_measurement()
    data_R_t = []
    if GUI:
        # create an empty list in the remote process
        p3 = win.addPlot(title="Resistance vs. time")
        curve_R_t = p3.plot(pen='y')
        p3.setLabel('left', "Resistance", units='Ohm')
        p3.setLabel('bottom', "time", units='s')
        curve_R_t.setData(data_R_t, _callSync='off')
        if new_row:
            win.nextRow()
    t0 = time.time() # measurement start time
    while time.time()-t0 < total_measurement_time:
        R = device.get_value()
        time_val = time.time() - t0
        data_R_t.append([R[0],time_val])
        if GUI:
            curve_R_t.setData(x=[k[1] for k in data_R_t], y=[k[0] for k in data_R_t], _callSync='off')
    return [data_R_t]
    
def temperature_logger(device,total_measurement_time,sensor="K",num_of_channels=1,new_row=False, GUI=True):
    device.reset()
    device.setup_temperature_measurement(sensor)
    data_T_t = []
    data_T2_t = []
    if GUI:
        # create an empty list in the remote process
        p3 = win.addPlot(title="Temperature vs. time")
        curve_T_t = p3.plot(pen='y')
        p3.setLabel('left', "Temperature", units='C')
        p3.setLabel('bottom', "time", units='s')
        curve_T_t.setData(data_T_t, _callSync='off')

        if num_of_channels > 1:
            p3 = win.addPlot(title="Temperature 2 vs. time")
            curve_T2_t = p3.plot(pen='y')
            p3.setLabel('left', "Temperature", units='C')
            p3.setLabel('bottom', "time", units='s')
            curve_T2_t.setData(data_T2_t, _callSync='off')
      
        if new_row:
            win.nextRow()
    t0 = time.time() # measurement start time
    while time.time()-t0 < total_measurement_time:
        T = device.get_value()
        T_val = T[0]
        if T_val > 2000:
            T_val = 0
        time_val = time.time() - t0
        data_T_t.append([T_val,time_val])
        if num_of_channels > 1:
            T2 = device.get_value()
            T_val = T2[0]
            if T_val > 2000:
                T_val = 0
            data_T2_t.append([T_val,time_val])
        if GUI:
            curve_T_t.setData(x=[k[1] for k in data_T_t], y=[k[0] for k in data_T_t], _callSync='off')
            if num_of_channels > 1:
                curve_T2_t.setData(x=[k[1] for k in data_T2_t], y=[k[0] for k in data_T2_t], _callSync='off')
    if num_of_channels > 1:
        return [data_T_t,data_T2_t]
    return [data_T_t]
    
#def temperature_scanner(device,total_measurement_time,sensor="K",slots,channels,new_row=False, all_in_one_graph=True, GUI=True):
    #device.reset()
    #if type(slots)==float or type(slots)==int:
        #slots = [slots] # make an array
    #else:
        #slots = [slots[0]]
    #if type(channels)==float or type(channels)==int:
        #channels = [channels] # make an array
    #device.setup_temperature_measurement(sensor,slot=slots,channel=channels)
    #if GUI:
        #data_T_t = []
        #curve_T_t = []   
        #if all_in_one_graph: # Different colored lines in the same graph
            ##win.addLegend()
            #p3 = win.addPlot(title="Temperature vs. time")
            #p3.setLabel('left', "Temperature", units='C')
            #p3.setLabel('bottom', "time", units='s')
            #p3.addLegend()
            #for j,slot in enumerate(slots):
                #for i,channel in enumerate(channels):
                    #data_T_t.append([]) # [None for i in range(num_measurement_points)]
                    #curve = p3.plot(pen=(i+j,len(slots)*len(channels)),name="Slot "+str(slot)+" channel "+str(channel))
                    #curve_T_t.append(curve)
            #for j,slot in enumerate(slots):
                #for i,channel in enumerate(channels):
                    #curve_T_t[i+j].setData(data_T_t[i+j], _callSync='off')
        #else: # Each graph in a separate window
            #for j,slot in enumerate(slots):
                #for i,channel in enumerate(channels):
                    ## create an empty list in the remote process
                    #p3 = win.addPlot(title="Temperature vs. time slot "+str(slot)+" channel "+str(channel))
                    #curve_T_t.append(p3.plot(pen='y'))
                    #p3.setLabel('left', "Temperature", units='C')
                    #p3.setLabel('bottom', "time", units='s')
                    #data_T_t.append([]) # [None for i in range(num_measurement_points)]
                    #curve_T_t[i+j].setData(data_T_t[i+j], _callSync='off')
      
        #if new_row:
            #win.nextRow()
    #else:
        #data_T_t = [[] for i in range(len(channels)*len(slots))]
    #t0 = time.time() # measurement start time
    #while time.time()-t0 < total_measurement_time:
        #T = device.get_value()
        #for i in range(len(channels)*len(slots)):
            #time_val = time.time() - t0
            #T_val = T[0][i]
            #if T_val > 2000:
                #T_val = 0
            #data_T_t[i].append([T_val,time_val])
            #if GUI:
                #for i in range(len(channels)*len(slots)):
                    #curve_T_t[i].setData(x=[k[1] for k in data_T_t[i]], y=[k[0] for k in data_T_t[i]], _callSync='off')
    #return [data_T_t]
    
def temperature_current_logger(device_temperature,device_smu,total_measurement_time,bias_voltage=0,sensor="K",new_row=False, GUI=True):
    device_temperature.reset()
    device_smu.reset()
    device_temperature.setup_temperature_measurement(sensor)
    device_smu.setup_current_measurement(10)
    device_smu.turn_output_off()
    device_smu.set_voltage(bias_voltage)
    device_smu.turn_output_on()
    data_T_t = []
    data_I_t = []
    if GUI:
        # create an empty list in the remote process
        p3 = win.addPlot(title="Temperature vs. time")
        curve_T_t = p3.plot(pen='y')
        p3.setLabel('left', "Temperature", units='C')
        p3.setLabel('bottom', "time", units='s')
        curve_T_t.setData(data_T_t, _callSync='off')
        
        p3 = win.addPlot(title="Current vs. time")
        curve_I_t = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_I_t.setData(data_I_t, _callSync='off')
        if new_row:
            win.nextRow()
    t0 = time.time() # measurement start time
    while time.time()-t0 < total_measurement_time:
        T = device_temperature.get_value()
        T_val = T[0]
        if T_val > 2000:
            T_val = 0
        I = device_smu.get_current()
        time_val = time.time() - t0
        data_T_t.append([T_val,time_val])
        data_I_t.append([I,time_val])
        if GUI:
            curve_T_t.setData(x=[k[1] for k in data_T_t], y=[k[0] for k in data_T_t], _callSync='off')
            curve_I_t.setData(x=[k[1] for k in data_I_t], y=[k[0] for k in data_I_t], _callSync='off')
    device_smu.turn_output_off()
    return [data_T_t,data_I_t]
    
def arrhenius_dc(device_temperature,device_smu,device_oven,temperature_values,ramp_rates,stabilization_times,voltage_values,measurement_time=60,continuous_voltage=True,GUI=True):
    oven_constant = device_oven.get_oven_constant()
    global window_title
    window_title = str(device_oven.get_oven_name())
    oven_name = " "+str(device_oven.get_oven_name())
    room_temperature = 23
    if type(temperature_values)==float or type(temperature_values)==int:
       temperature_values = [temperature_values] # make an array
    temperature_values.append(room_temperature)
    if type(ramp_rates)==float or type(ramp_rates)==int:
       ramp_rates = [ramp_rates] # make an array
    # Compare length of ramp_rates array and make it fit to the temperature_values
    while len(ramp_rates) < len(temperature_values):
        ramp_rates.append(ramp_rates[-1])
    if type(stabilization_times)==float or type(stabilization_times)==int:
       stabilization_times = [stabilization_times] # make an array
    if type(voltage_values)==float or type(voltage_values)==int:
       voltage_values = [voltage_values] # make an array
    if len(voltage_values) > 1 and continuous_voltage:
        print "It is not possible to measure in continuous voltage mode with multiple voltages set!"
        return
    # Compare length of ramp_rates array and make it fit to the temperature_values
    while len(stabilization_times) < len(temperature_values):
        stabilization_times.append(stabilization_times[-1])
    # Setup temperature measuring device
    if device_temperature is not None:
        device_temperature.reset()
        device_temperature.setup_temperature_measurement()
    device_smu.reset()
    device_smu.setup_current_measurement(10)
    device_smu.turn_output_off()
    if continuous_voltage:
        device_smu.set_voltage(voltage_values[0])
        device_smu.turn_output_on()
    # set oven to first setpoint
    device_oven.set_auto_mode()
    device_oven.disable_programmer_mode()
    device_oven.select_setpoint(0) # means setpoint 1
    device_oven.set_sp1(temperature_values[0])
    device_oven.set_setpoint_rate(ramp_rates[0])
    device_oven.disable_setpoint_rate()
    data_T_t = [[],[]]
    data_P_t = [[],[[],[]],[]]
    data_I_t = []
    data_R_T = [[] for i in range(len(voltage_values))]
    if GUI:
        curve_T_t = []
        curve_P_t = []
        curve_I_t = []
        curve_R_T = []
        # Plot with temperature
        p3 = win.addPlot(title="Temperature vs. time")
        p3.setLabel('left', "Temperature", units='C')
        p3.setLabel('bottom', "time", units='s')
        p3.addLegend()
        curve = p3.plot(pen=(0,2),name="Temperature in chamber")
        curve_T_t.append(curve)
        curve = p3.plot(pen=(1,2),name="PV (Eurotherm)"+oven_name)
        curve_T_t.append(curve)
        # now a new plot where we show the optimal curve
        p3 = win.addPlot(title="Program vs. time")
        p3.setLabel('left', "Temperature", units='C')
        p3.setLabel('bottom', "time", units='s')
        p3.addLegend()
        curve = p3.plot(pen=(0,3),name="Programmed profile")
        curve_P_t.append(curve)
        curve = p3.plot(pen={'color': (2,3), 'width': 2, 'style': QtCore.Qt.DotLine}, symbolPen=(2,3),symbol=None,name="Air-cooling offset")
        curve_P_t.append(curve)
        curve = p3.plot(pen=None, symbol='o',name="Current position")
        curve_P_t.append(curve)
    # Print how long the process will take with each step
    estimated_total_time = 0
    time_at_each_temperature = len(voltage_values)*measurement_time
    temp_T = device_oven.get_pv()
    connected_lines_array = np.array([], np.int32)
    for i,T_set in enumerate(temperature_values):
        data_P_t[0].append([temp_T,estimated_total_time])
        former_time = estimated_total_time
        estimated_total_time = estimated_total_time+np.absolute(T_set-temp_T)/(ramp_rates[i]/60.0)
        print "Ramping to ",str(T_set),"°C @ ",str(ramp_rates[i]),"°C/min will take ",str(datetime.timedelta(seconds=estimated_total_time))," reached at ",datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(seconds=estimated_total_time),"%d.%m.%y %H:%M")
        data_P_t[0].append([T_set,estimated_total_time])
        # Now calculate the air-cooling curve. First find the y=m*t+q
        if former_time-estimated_total_time is not 0: # prevent division by zero
            m = (temp_T-T_set)/(former_time-estimated_total_time)
            q = temp_T
            if m < 0: # Cooling
                # Find temperature of intersection with exp() cooling curve
                a = float(temp_T-room_temperature)
                time_of_intersection = float(((-oven_constant*q+m*lambertw((a*np.exp((oven_constant*q)/m)*oven_constant)/m))/(oven_constant*m)).real) # real part only. Time0 is where the ramping down starts! Its relative to this time
                intersection_temperature = m*time_of_intersection+q
                if intersection_temperature < temp_T and intersection_temperature > T_set: # Somewhere in the line
                    # Start drawing a line with small dots where the cooling is followed
                    time_when_at_low_temp = -np.log(T_set/a)/oven_constant
                    if i == len(temperature_values)-1: # its the final last cooling
                        final_cooldown_time = -np.log(100.0/a)/oven_constant+estimated_total_time-np.absolute(T_set-temp_T)/(ramp_rates[i]/60.0)
                        print "-----------------------------"
                        print "final Cool-down to 100°C will be reached at:",datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(seconds=final_cooldown_time),"%d.%m.%y %H:%M")
                        print "-----------------------------"
                    x_values = np.linspace(time_of_intersection, time_when_at_low_temp, num=25)
                    connected_lines_array = np.append(connected_lines_array,[1 for j in range(24)])
                    connected_lines_array = np.append(connected_lines_array,0) # not connected between different segments
                    y_values = map(lambda x: a*np.exp(-oven_constant*x),x_values)
                    data_P_t[1][0].extend(list([x+estimated_total_time-np.absolute(T_set-temp_T)/(ramp_rates[i]/60.0) for x in x_values]))
                    data_P_t[1][1].extend(list(y_values))
        temp_T = T_set
        estimated_total_time = estimated_total_time+stabilization_times[i]+time_at_each_temperature
    if GUI:
        curve_P_t[0].setData(x=[k[1] for k in data_P_t[0]], y=[k[0] for k in data_P_t[0]], _callSync='off') # program
        curve_P_t[1].setData(x=data_P_t[1][0], y=data_P_t[1][1],connect=connected_lines_array, _callSync='off') # cooling
        # now a new row and the arrhenius plots
        win.nextRow()
        p3 = win.addPlot(title="Current vs. time")
        p3.setLabel('left', "current", units='A')
        p3.setLabel('bottom', "time", units='s')
        if continuous_voltage:
            curve = p3.plot(pen=(0,2))
        else:
            curve = p3.plot(pen=None,symbol='+')
        curve_I_t.append(curve)
        p3 = win.addPlot(title="Resistance vs. temperature")
        p3.setLabel('left', "resistance", units='Ohm')
        p3.setLabel('bottom', "temperature", units=u"°C")
        p3.addLegend()
        dynamic_legend_resistance = p3.legend
        for i,voltage_val in enumerate(voltage_values):
            curve = p3.plot(pen=None,symbol='+',symbolPen=(i,len(voltage_values)))
            dynamic_legend_resistance.addItem(curve, name=str(voltage_val)+"V")
            curve_R_T.append(curve)
        for i in range(len(voltage_values)):
            curve_R_T[i].setData(data_R_T[i], _callSync='off')
    t0 = time.time() # measurement start time
    T_now = device_oven.get_pv()
    time_summing_last_actions = 0
    for index,T_set in enumerate(temperature_values):
        step_done = False
        while not step_done:
            if device_temperature is not None:
                T = device_temperature.get_value()
                if T[0] > 2000:
                    T[0] = 0 # make graphical output nicer in case of overflow
            else:
                T = [0,0]
            PV = device_oven.get_pv()
            if PV is None: # We have a communication error. Stop the program
                step_done = True
                continue
            time_val = time.time() - t0
            # graphical output
            data_T_t[0].append([T[0],time_val])
            data_T_t[1].append([PV,time_val])
            data_P_t[2] = [PV,time_val]
            if continuous_voltage:
                I = device_smu.get_value()
                data_I_t.append([I[0],time_val])
            if GUI:
                curve_T_t[0].setData(x=[k[1] for k in data_T_t[0]], y=[k[0] for k in data_T_t[0]], _callSync='off') # Chamber
                curve_T_t[1].setData(x=[k[1] for k in data_T_t[1]], y=[k[0] for k in data_T_t[1]], _callSync='off') # PV
                curve_P_t[2].setData(x=[time_val], y=[PV], _callSync='off')
                if continuous_voltage:
                    curve_I_t[0].setData(x=[k[1] for k in data_I_t], y=[k[0] for k in data_I_t], _callSync='off')
            if time_val > stabilization_times[index]+np.absolute(T_set-T_now)/(ramp_rates[index]/60.0)+time_summing_last_actions:
                time_summing_last_actions = time_summing_last_actions+stabilization_times[index]+np.absolute(T_set-T_now)/(ramp_rates[index]/60.0)
                step_done = True
                # Now we can start with dc measurement  
                time_before_dc_run = time_val
                for i,voltage_val in enumerate(voltage_values):
                    device_smu.set_voltage(voltage_values[i])
                    device_smu.turn_output_on()
                    time.sleep(1)
                    average_current = []
                    while time_val-time_before_dc_run < float(i+1)*(measurement_time-1):
                        time_val = time.time() - t0
                        I = device_smu.get_value()
                        PV = device_oven.get_pv()
                        data_T_t[1].append([PV,time_val])
                        temperature_at_sample = PV
                        if device_temperature is not None:
                            T1 = device_temperature.get_value()
                            temperature_at_sample = T1[0]
                            if T[0] > 2000:
                                temperature_at_sample = 0 # make graphical output nicer in case of overflow
                                average_current.append([I[0],PV,time_val])
                            else:
                                average_current.append([I[0],temperature_at_sample,time_val])
                        else:
                            temperature_at_sample = 0
                            average_current.append([I[0],PV,time_val])
                        data_T_t[0].append([temperature_at_sample,time_val])
                        # graphical output
                        data_P_t[2] = [PV,time_val]
                        if continuous_voltage:
                            data_I_t.append([I[0],time_val])
                        if GUI:
                            curve_T_t[0].setData(x=[k[1] for k in data_T_t[0]], y=[k[0] for k in data_T_t[0]], _callSync='off')
                            curve_T_t[1].setData(x=[k[1] for k in data_T_t[1]], y=[k[0] for k in data_T_t[1]], _callSync='off')
                            curve_P_t[2].setData(x=[time_val], y=[PV], _callSync='off')
                            if continuous_voltage:
                                curve_I_t[0].setData(x=[k[1] for k in data_I_t], y=[k[0] for k in data_I_t], _callSync='off')
                    data_R_T[i].append([float(voltage_val/np.average([k[0] for k in average_current])),np.average([k[1] for k in average_current])])
                    if GUI:
                        curve_R_T[i].setData(x=[k[1] for k in data_R_T[i]], y=[k[0] for k in data_R_T[i]], _callSync='off')
                        if not continuous_voltage:
                            data_I_t.extend([[k[0],k[2]] for k in average_current])
                            curve_I_t[0].setData(x=[k[1] for k in data_I_t], y=[k[0] for k in data_I_t], _callSync='off')
                if not continuous_voltage:
                    device_smu.turn_output_off()
                T_now = PV
                time_val = time.time() - t0
                dc_time = time_val-time_before_dc_run
                time_summing_last_actions = time_summing_last_actions+dc_time
                # Now dc is done for this temperature.
                if (index+1) < len(temperature_values):
                    device_oven.set_sp1(temperature_values[index+1])
                    device_oven.set_setpoint_rate(ramp_rates[index+1])
    return [data_T_t,data_P_t,data_I_t,data_R_T]
    
def sintering(device_temperature,device_oven,temperature_values,ramp_rates,stabilization_times,sensor="K",GUI=True):
    room_temperature = 23
    oven_constant = device_oven.get_oven_constant()
    global window_title
    window_title = str(device_oven.get_oven_name())
    oven_name = " "+str(device_oven.get_oven_name())
    if type(temperature_values)==float or type(temperature_values)==int:
       temperature_values = [temperature_values] # make an array
    temperature_values.append(room_temperature)
    if type(ramp_rates)==float or type(ramp_rates)==int:
       ramp_rates = [ramp_rates] # make an array
    # Compare length of ramp_rates array and make it fit to the temperature_values
    while len(ramp_rates) < len(temperature_values):
        ramp_rates.append(ramp_rates[-1])
    if type(stabilization_times)==float or type(stabilization_times)==int:
       stabilization_times = [stabilization_times] # make an array
    # Compare length of stabilization_times array and make it fit to the temperature_values
    while len(stabilization_times) < len(temperature_values):
        stabilization_times.append(stabilization_times[-1])
    # set oven to first setpoint
    #device_oven.set_ptyp_none()
    #device_oven.set_auto_mode()
    #device_oven.disable_programmer_mode()
    device_oven.set_instrument_mode(0)
    device_oven.select_setpoint(0) # means setpoint 1
    device_oven.set_sp1(temperature_values[0])
    device_oven.set_setpoint_rate(ramp_rates[0])
    device_oven.disable_setpoint_rate()
    # Setup temperature measuring device
    if device_temperature is not None:
        device_temperature.reset()
        device_temperature.setup_temperature_measurement(sensor)
    data_T_t = [[],[]]
    data_P_t = [[],[[],[]],[]]
    if GUI:
        curve_T_t = []
        curve_P_t = []
        p3 = win.addPlot(title="Temperature vs. time")
        p3.setLabel('left', "Temperature", units='C')
        p3.setLabel('bottom', "time", units='s')
        p3.addLegend()
        curve = p3.plot(pen=(0,2),name="Temperature in chamber")
        curve_T_t.append(curve)
        curve = p3.plot(pen=(1,2),name="PV (Eurotherm)"+oven_name)
        curve_T_t.append(curve)
        # now a new plot where we show the optimal curve
        p3 = win.addPlot(title="Program vs. time")
        p3.setLabel('left', "Temperature", units='C')
        p3.setLabel('bottom', "time", units='s')
        p3.addLegend()
        curve = p3.plot(pen=(0,3),name="Programmed profile")
        curve_P_t.append(curve)
        curve = p3.plot(pen={'color': (2,3), 'width': 2, 'style': QtCore.Qt.DotLine}, symbolPen=(2,3),symbol=None,name="Air-cooling offset")
        curve_P_t.append(curve)
        curve = p3.plot(pen=None, symbol='o',name="Current position")
        curve_P_t.append(curve)
    # Print how long the process will take with each step
    estimated_total_time = 0
    temp_T = device_oven.get_pv()
    connected_lines_array = np.array([], np.int32)
    for i,T_set in enumerate(temperature_values):
        data_P_t[0].append([temp_T,estimated_total_time])
        former_time = estimated_total_time
        estimated_total_time = estimated_total_time+np.absolute(T_set-temp_T)/(ramp_rates[i]/60.0)
        print "Ramping to ",str(T_set),"°C @ ",str(ramp_rates[i]),"°C/min will take ",str(datetime.timedelta(seconds=estimated_total_time))," reached at ",datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(seconds=estimated_total_time),"%d.%m.%y %H:%M")
        data_P_t[0].append([T_set,estimated_total_time])
        # Now calculate the air-cooling curve. First find the y=m*t+q
        if former_time-estimated_total_time is not 0: # prevent division by zero
            m = (temp_T-T_set)/(former_time-estimated_total_time)
            q = temp_T
            if m < 0: # Cooling
                # Find temperature of intersection with exp() cooling curve
                a = float(temp_T-room_temperature)
                time_of_intersection = float(((-oven_constant*q+m*lambertw((a*np.exp((oven_constant*q)/m)*oven_constant)/m))/(oven_constant*m)).real) # real part only. Time0 is where the ramping down starts! Its relative to this time
                intersection_temperature = m*time_of_intersection+q
                if intersection_temperature < temp_T and intersection_temperature > T_set: # Somewhere in the line
                    # Start drawing a line with small dots where the cooling is followed
                    time_when_at_low_temp = -np.log(T_set/a)/oven_constant
                    if i == len(temperature_values)-1: # its the final last cooling
                        final_cooldown_time = -np.log(100.0/a)/oven_constant+estimated_total_time-np.absolute(T_set-temp_T)/(ramp_rates[i]/60.0)
                        print "-----------------------------"
                        print "final Cool-down to 100°C will be reached at:",datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(seconds=final_cooldown_time),"%d.%m.%y %H:%M")
                        print "-----------------------------"
                    x_values = np.linspace(time_of_intersection, time_when_at_low_temp, num=25)
                    connected_lines_array = np.append(connected_lines_array,[1 for j in range(24)])
                    connected_lines_array = np.append(connected_lines_array,0) # not connected between different segments
                    y_values = map(lambda x: a*np.exp(-oven_constant*x),x_values)
                    data_P_t[1][0].extend(list([x+estimated_total_time-np.absolute(T_set-temp_T)/(ramp_rates[i]/60.0) for x in x_values]))
                    data_P_t[1][1].extend(list(y_values))
        temp_T = T_set
        estimated_total_time = estimated_total_time+stabilization_times[i]
    if GUI:
        curve_P_t[0].setData(x=[k[1] for k in data_P_t[0]], y=[k[0] for k in data_P_t[0]], _callSync='off') # program
        curve_P_t[1].setData(x=data_P_t[1][0], y=data_P_t[1][1],connect=connected_lines_array, _callSync='off') # cooling
    t0 = time.time() # measurement start time
    T_now = device_oven.get_pv()
    time_summing_last_actions = 0
    for index,T_set in enumerate(temperature_values):
        step_done = False
        while not step_done:
            if device_temperature is not None:
                T = device_temperature.get_value()
                if T[0] > 2000:
                    T[0] = 0 # make graphical output nicer in case of overflow
            else:
                T = [0,0]
            PV = device_oven.get_pv()
            if PV is None: # We have a communication error. Stop the program
                step_done = True
                continue
            time_val = time.time() - t0
            if time_val > stabilization_times[index]+np.absolute(T_set-T_now)/(ramp_rates[index]/60.0)+time_summing_last_actions:
                time_summing_last_actions = time_summing_last_actions+stabilization_times[index]+np.absolute(T_set-T_now)/(ramp_rates[index]/60.0)
                step_done = True
                T_now = PV
                if (index+1) < len(temperature_values):
                    device_oven.set_sp1(temperature_values[index+1])
                    device_oven.set_setpoint_rate(ramp_rates[index+1])
            # graphical output
            data_T_t[0].append([T[0],time_val])
            data_T_t[1].append([PV,time_val])
            data_P_t[2] = [PV,time_val]
            if GUI:
                curve_T_t[0].setData(x=[k[1] for k in data_T_t[0]], y=[k[0] for k in data_T_t[0]], _callSync='off')
                curve_T_t[1].setData(x=[k[1] for k in data_T_t[1]], y=[k[0] for k in data_T_t[1]], _callSync='off')
                curve_P_t[2].setData(x=[time_val], y=[PV], _callSync='off')
    return [data_T_t,data_P_t]
 
def mfc(device_mfc,stabilization_times,flow_rates,GUI=True):
    if type(stabilization_times)==float or type(stabilization_times)==int:
       stabilization_times = [stabilization_times] # make an array
    if not isinstance(flow_rates, list):
        print "ERROR: Wrong syntax for the variable flow_rates. Needs to be at least [ \"gastype1\" or modbus_address , set_flow ] for one gas and one flow for all steps. Or an array of arrays for more complicated setups"
        return
    # Check if the flow_rates array is in the right syntax
    # Should be [ [ [ "gastype1" or modbusnumber , set_flow ],[...] ] , [...] ]
    # or if only one gas used: [ [ "gastype1" or modbusnumber , set_flow ]  , [...] ]
    # or if only one gas and one flow used: [ "gastype1" or modbusnumber , set_flow ]
    mfc_array = device_mfc.get_all_flowmeter_addresses()
    mfc_str = []
    mfc_modbus = []
    mfc_steps = [] # the final array
    mfc_array_dim1 = len(flow_rates)
    if not isinstance(flow_rates[0], list): # This means we are in the case: [ "gastype1" or modbusnumber , set_flow ]. One sensor and one flow for all steps
        if mfc_array_dim1 != 2: # wrong syntax
            print "ERROR: Wrong syntax for the variable flow_rates. Needs to be at least [ \"gastype1\" or modbus_address , set_flow ] for one gas and one flow used for all steps."
            return
        mfc_to_be_used = flow_rates[0] # Is it a string like "Air 300" or a modbus address?
        try:
            if type(mfc_to_be_used)==str:
                mfc_str.append(mfc_to_be_used)
                mfc_modbus.append([e[0] for e in mfc_array if e[1]==mfc_to_be_used][0])
            else: # it's a number
                mfc_str.append([e[1] for e in mfc_array if e[0]==mfc_to_be_used][0])
                mfc_modbus.append(mfc_to_be_used)
        except Exception:
            print "ERROR: Wrong syntax for the variable flow_rates. You are trying to address a MFC which is unknown or not connected:",mfc_to_be_used
            print "Try to use one of those:",[e[1] for e in mfc_array],"or their corresponding modbus-address:",[e[0] for e in mfc_array]
            return
        mfc_steps.append([[mfc_modbus[-1],float(flow_rates[1])]]) # One flow for all steps
    elif isinstance(flow_rates[0][0], list): # This means we are definitely in the case: [ [ [ "gastype1" or modbusnumber , set_flow ],[...] ] , [...] ]
        step_shape = np.shape(flow_rates[0])
        # This is the most complicated setup: Multiple gases with multiple set_flow at multiple steps
        if any(np.shape(e) != step_shape for e in flow_rates): # Wrong syntax. Every MFC needs to be addressed in every step
            print "ERROR: Wrong syntax for the variable flow_rates. Every MFC needs to be addressed in every step"
            return
        list_of_mfcs = []
        for step in flow_rates:
            list_of_mfcs.append([e[0] for e in step]) # make the mfc list
            for mfc in step:
                if len(mfc) != 2: # Wrong syntax
                    print "ERROR: Wrong syntax for the variable flow_rates. You don't always specify 2 elements in the most inner array of this 3d-array. Needs to be a 3d-array [ [ [ \"gastype1\" or modbusnumber , set_flow ],[...] ] , [...] ]"
                    return
        # Check if all mfcs in every step are addressed
        if not all(x==list_of_mfcs[0] for x in list_of_mfcs):
            print "ERROR: Wrong syntax for the variable flow_rates. You don't specify all MFCs in all the steps. Or you mix up the order. Or you are not consistent with the naming. Clean up..."
            return
        # Check if all MFC exist
        for mfc_to_be_used in list_of_mfcs[0]:
            try:
                if type(mfc_to_be_used)==str:
                    mfc_str.append(mfc_to_be_used)
                    mfc_modbus.append([e[0] for e in mfc_array if e[1]==mfc_to_be_used][0])
                else: # it's a number
                    mfc_str.append([e[1] for e in mfc_array if e[0]==mfc_to_be_used][0])
                    mfc_modbus.append(mfc_to_be_used)
            except Exception:
                print "ERROR: Wrong syntax for the variable flow_rates. You are trying to address a MFC which is unknown or not connected:",mfc_to_be_used
                print "Try to use one of those:",[e[1] for e in mfc_array],"or their corresponding modbus-address:",[e[0] for e in mfc_array]
                return
        # make the final array [ [ [ "gastype1" or modbusnumber , set_flow ],[...] ] , [...] ]
        for step in flow_rates:
            step_array = []
            for i,mfc in enumerate(step):
                step_array.append([mfc_modbus[i],float(mfc[1])])    
            mfc_steps.append(step_array)
    else: # Check the last possibility: [ [ "gastype1" or modbusnumber , set_flow ]  , [...] ]
        # Check if all secondary array are of length 2
        if any(len(e) != 2 for e in flow_rates): # Wrong syntax. Only one MFC is allowed to be used
            print "ERROR: Wrong syntax for the variable flow_rates. Only one gas sensor is allowed for all steps with this syntax [ [ \"gastype1\" or modbusnumber , set_flow ]  , [...] ]. Use a 3d-array if you want to use multiple sensors and steps"
            return
        mfc_to_be_used = flow_rates[0][0] # Is it a string like "Air 300" or a modbus address?
        try:
            if type(mfc_to_be_used)==str:
                mfc_str.append(mfc_to_be_used)
                mfc_modbus.append([e[0] for e in mfc_array if e[1]==mfc_to_be_used][0])
            else: # it's a number
                mfc_str.append([e[1] for e in mfc_array if e[0]==mfc_to_be_used][0])
                mfc_modbus.append(mfc_to_be_used)
        except Exception:
            print "ERROR: Wrong syntax for the variable flow_rates. You are trying to address a MFC which is unknown or not connected:",mfc_to_be_used
            print "Try to use one of those:",[e[1] for e in mfc_array],"or their corresponding modbus-address:",[e[0] for e in mfc_array]
            return
        # Check if it is always the same flowmeter which is addressed:
        if any(mfc_to_be_used != e[0] for e in flow_rates): # Wrong syntax. Only one MFC is allowed to be used
            print "ERROR: Wrong syntax for the variable flow_rates. Only one gas sensor is allowed for all steps with this syntax [ [ \"gastype1\" or modbusnumber , set_flow ]  , [...] ]. Use a 3d-array if you want to use multiple sensors and steps"
            return
        for mfc in flow_rates:
            mfc_steps.append([[mfc_modbus[0],float(mfc[1])]])    
    while len(stabilization_times) < len(mfc_steps):
        stabilization_times.append(stabilization_times[-1])
    while len(mfc_steps) < len(stabilization_times): # Now do the opposite. If one has more stabilization_times than steps duplicate the last step
        mfc_steps.append(mfc_steps[-1])
    data_F_t = [[] for i in range(len(mfc_modbus))]
    data_FP_t = [[] for i in range(len(mfc_modbus))]
    if GUI:
        curve_F_t = []
        curve_FP_t = []
        p3 = win.addPlot(title="Mass flow vs. time")
        p3.setLabel('left', "Flow", units='sccm')
        p3.setLabel('bottom', "time", units='s')
        p3.addLegend()
        for i,mfc in enumerate(mfc_str):
            curve = p3.plot(pen=(i,len(mfc_str)),name=str(mfc))
            curve_F_t.append(curve)
        # now a new plot where we show the optimal curve
        p3 = win.addPlot(title="Flow-program vs. time")
        p3.setLabel('left', "Flow", units='sccm')
        p3.setLabel('bottom', "time", units='s')
        p3.addLegend()
        for i,mfc in enumerate(mfc_str):
            curve = p3.plot(pen=(i,len(mfc_str)),name=str(mfc))
            curve_FP_t.append(curve)
        vline = p3.addLine(x=0)
        curve_FP_t.append(vline)
    # Now build up the theoretical flow profile curves
    summed_time1 = 0
    summed_time2 = 0
    for j,step in enumerate(mfc_steps):
        summed_time1 = summed_time2
        summed_time2 = summed_time2+stabilization_times[j]
        for i,mfc in enumerate(step):
            data_FP_t[i].append([mfc[1],summed_time1])
            data_FP_t[i].append([mfc[1],summed_time2])
    if GUI:
        for i in range(len(mfc_modbus)):
            curve_FP_t[i].setData(x=[k[1] for k in data_FP_t[i]], y=[k[0] for k in data_FP_t[i]], _callSync='off')
    t0 = time.time() # measurement start time
    time_summing_last_actions = 0
    for index,timestep in enumerate(stabilization_times):
        step_done = False
        # set first valve positions
        for mfc in mfc_steps[index]:
            device_mfc.set_sp(mfc[1],mfc[0]) # value, address
        while not step_done:
            time_val = time.time() - t0
            for i,mfc in enumerate(mfc_steps[index]):
                data_F_t[i].append([device_mfc.get_flow(mfc[0]),time_val])
            if time_val > stabilization_times[index]+time_summing_last_actions:
                time_summing_last_actions = time_summing_last_actions+stabilization_times[index]
                step_done = True
                if (index+1) < len(stabilization_times):
                    for mfc in mfc_steps[index+1]:
                        device_mfc.set_sp(mfc[1],mfc[0]) # value, address
            # graphical output
            if GUI:
                for i in range(len(mfc_modbus)):
                    curve_F_t[i].setData(x=[k[1] for k in data_F_t[i]], y=[k[0] for k in data_F_t[i]], _callSync='off')
                curve_FP_t[-1].setValue(time_val)
    device_mfc.close() # set all setpoint to 0 to limit gas consumption
    return [data_F_t,data_FP_t]

def arrhenius_ac(device_temperature,device_oven,device_impedance,temperature_values,ramp_rates,stabilization_times,number_of_repetitions=1,start_frequency=0.1,end_frequency=1.0e6,ac_amplitude=0.1,bias=0,num_points_per_decade=10,path="/home/electrochem/lost_data",GUI=True):
    oven_constant = device_oven.get_oven_constant()
    global window_title
    window_title = str(device_oven.get_oven_name())
    oven_name = " "+str(device_oven.get_oven_name())
    room_temperature = 23
    path = path.rstrip("/")
    try: # Check if path exists and is writable
        with open(path+'/../'+"demo.txt", 'w') as f:
            f.write("Test_if_directory_is_writable.\n")
            f.close()
        os.remove(path+'/../'+"demo.txt")
    except Exception:
        print "The path:",path,"you specifiy is not existent or not writable!"
        return
    if type(temperature_values)==float or type(temperature_values)==int:
       temperature_values = [temperature_values] # make an array
    temperature_values.append(room_temperature)
    if type(ramp_rates)==float or type(ramp_rates)==int:
       ramp_rates = [ramp_rates] # make an array
    # Compare length of ramp_rates array and make it fit to the temperature_values
    while len(ramp_rates) < len(temperature_values):
        ramp_rates.append(ramp_rates[-1])
    if type(stabilization_times)==float or type(stabilization_times)==int:
       stabilization_times = [stabilization_times] # make an array
    # Compare length of ramp_rates array and make it fit to the temperature_values
    while len(stabilization_times) < len(temperature_values):
        stabilization_times.append(stabilization_times[-1])
    # set oven to first setpoint
    device_oven.set_auto_mode()
    device_oven.disable_programmer_mode()
    device_oven.select_setpoint(0) # means setpoint 1
    device_oven.set_sp1(temperature_values[0])
    device_oven.set_setpoint_rate(ramp_rates[0])
    device_oven.disable_setpoint_rate()
    # Setup temperature measuring device
    if device_temperature is not None:
        device_temperature.reset()
        device_temperature.setup_temperature_measurement()
    data_T_t = [[],[]]
    data_P_t = [[],[],[[],[]],[]]
    data_Zi_Zr = [[] for i in range(len(temperature_values))]
    data_freq_mod = [[] for i in range(len(temperature_values))]
    if GUI:
        curve_T_t = []
        curve_P_t = []
        curve_Zi_Zr = []
        curve_freq_mod = []
        # Plot with temperature
        p3 = win.addPlot(title="Temperature vs. time")
        p3.setLabel('left', "Temperature", units='C')
        p3.setLabel('bottom', "time", units='s')
        p3.addLegend()
        curve = p3.plot(pen=(0,2),name="Temperature in chamber")
        curve_T_t.append(curve)
        curve = p3.plot(pen=(1,2),name="PV (Eurotherm)"+oven_name)
        curve_T_t.append(curve)
        # now a new plot where we show the optimal curve
        p3 = win.addPlot(title="Program vs. time")
        p3.setLabel('left', "Temperature", units='C')
        p3.setLabel('bottom', "time", units='s')
        p3.addLegend()
        curve = p3.plot(pen=(0,3),name="Programmed profile")
        curve_P_t.append(curve)
        curve = p3.plot(pen={'color': (0,3), 'width': 6.5}, symbol=None, name="next AC-measurement")
        curve_P_t.append(curve)
        curve = p3.plot(pen={'color': (2,3), 'width': 2, 'style': QtCore.Qt.DotLine}, symbolPen=(2,3),symbol=None,name="Air-cooling offset")
        curve_P_t.append(curve)
        curve = p3.plot(pen=None, symbol='o',name="Current position")
        curve_P_t.append(curve)
    # Print how long the process will take with each step
    # How long will one impedance measurement take?
    estimated_impedance_time_per_run = 600 #TODO find out #420 # 7 min
    estimated_impedance_time_per_temperature = estimated_impedance_time_per_run*number_of_repetitions
    estimated_total_time = 0
    temp_T = device_oven.get_pv()
    first_time = True
    heating_index = 0
    cooling_index = 0
    connected_lines_array = np.array([], np.int32)
    for i,T_set in enumerate(temperature_values):
        if first_time:
            first_time = False
            if temp_T <= T_set:
                step_label = "H" # first step is heating
                heating_index = heating_index+1
            else:
                step_label  = "C" # first step is cooling
                cooling_index = cooling_index+1
        data_P_t[0].append([temp_T,estimated_total_time])
        former_time = estimated_total_time
        estimated_total_time = estimated_total_time+np.absolute(T_set-temp_T)/(ramp_rates[i]/60.0)
        print "Ramping to ",str(T_set),"°C @ ",str(ramp_rates[i]),"°C/min will take ",str(datetime.timedelta(seconds=estimated_total_time))," reached at ",datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(seconds=estimated_total_time),"%d.%m.%y %H:%M")
        data_P_t[0].append([T_set,estimated_total_time])
        # Now calculate the air-cooling curve. First find the y=m*t+q
        if former_time-estimated_total_time is not 0: # prevent division by zero
            m = (temp_T-T_set)/(former_time-estimated_total_time)
            q = temp_T
            if m < 0: # Cooling
                # Find temperature of intersection with exp() cooling curve
                a = float(temp_T-room_temperature)
                time_of_intersection = float(((-oven_constant*q+m*lambertw((a*np.exp((oven_constant*q)/m)*oven_constant)/m))/(oven_constant*m)).real) # real part only. Time0 is where the ramping down starts! Its relative to this time
                intersection_temperature = m*time_of_intersection+q
                if intersection_temperature < temp_T and intersection_temperature > T_set: # Somewhere in the line
                    # Start drawing a line with small dots where the cooling is followed
                    time_when_at_low_temp = -np.log(T_set/a)/oven_constant
                    if i == len(temperature_values)-1: # its the final last cooling
                        final_cooldown_time = -np.log(100.0/a)/oven_constant+estimated_total_time-np.absolute(T_set-temp_T)/(ramp_rates[i]/60.0)
                        print "-----------------------------"
                        print "final Cool-down to 100°C will be reached at:",datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(seconds=final_cooldown_time),"%d.%m.%y %H:%M")
                        print "-----------------------------"
                        ## Create text object, use HTML tags to specify color/size
                        #finish_text = pg.TextItem(html=u'<div style="text-align: center"><span style="color: #FFF;">Final cooldown to 100°C</span><br><span style="color: #FF0; font-size: 16pt;">'+datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(seconds=final_cooldown_time),"%d.%m.%y %H:%M")+u'</span></div>', anchor=(-0.3,1.3), border='w', fill=(0, 0, 255, 100))
                        #p3.addItem(finish_text,0,1)
                        #finish_text.setPos(final_cooldown_time, 100.0)
                        ## Draw an arrowhead next to the text box
                        #arrow = pg.ArrowItem(pos=(final_cooldown_time, 100.0), angle=-45)
                        #p3.addItem(arrow,0,1)
                    x_values = np.linspace(time_of_intersection, time_when_at_low_temp, num=25)
                    connected_lines_array = np.append(connected_lines_array,[1 for j in range(24)])
                    connected_lines_array = np.append(connected_lines_array,0) # not connected between different segments
                    y_values = map(lambda x: a*np.exp(-oven_constant*x),x_values)
                    data_P_t[2][0].extend(list([x+estimated_total_time-np.absolute(T_set-temp_T)/(ramp_rates[i]/60.0) for x in x_values]))
                    data_P_t[2][1].extend(list(y_values))
        temp_T = T_set
        estimated_total_time = estimated_total_time+stabilization_times[i]+estimated_impedance_time_per_temperature
    if GUI:
        curve_P_t[0].setData(x=[k[1] for k in data_P_t[0]], y=[k[0] for k in data_P_t[0]], _callSync='off') # program
        curve_P_t[2].setData(x=data_P_t[2][0], y=data_P_t[2][1],connect=connected_lines_array, _callSync='off') # cooling
        # now a new row and the arrhenius plots
        win.nextRow()
        p3 = win.addPlot(title="Nyquist plot")
        p3.setLabel('left', "-Zimag", units='Ohm')
        p3.setLabel('bottom', "Zreal", units='Ohm')
        p3.setAspectLocked(True)
        p3.setLogMode(x=False,y=False)
        p3.addLegend()
        dynamic_legend_nyquist = p3.legend
        for i,temperature_val in enumerate(temperature_values):
            curve = p3.plot(pen=None,symbol='+',symbolPen=(i,len(temperature_values)))
            dynamic_legend_nyquist.addItem(curve, name=str(temperature_val)+u"°C")
            curve_Zi_Zr.append(curve)
        for i in range(len(temperature_values)):
            curve_Zi_Zr[i].setData(data_Zi_Zr[i], _callSync='off')
        p3 = win.addPlot(title="Bode plot")
        p3.setLabel('left', "abs(Z)", units='')
        p3.setLabel('bottom', "frequency", units='Hz')
        p3.setAspectLocked(True)
        p3.setLogMode(x=True,y=True)
        p3.addLegend()
        dynamic_legend_bode = p3.legend
        for i,temperature_val in enumerate(temperature_values):
            curve = p3.plot(pen=None,symbol='+',symbolPen=(i,len(temperature_values)))
            dynamic_legend_bode.addItem(curve, name=str(temperature_val)+u"°C")
            curve_freq_mod.append(curve)
        for i in range(len(temperature_values)):
            curve_freq_mod[i].setData(data_freq_mod[i], _callSync='off')
    t0 = time.time() # measurement start time
    T_now = device_oven.get_pv()
    time_summing_last_actions = 0
    for index,T_set in enumerate(temperature_values):
        # Now draw the line where we measure AC-impedance next
        data_P_t[1] = [[T_set,stabilization_times[index]+np.absolute(T_set-T_now)/(ramp_rates[index]/60.0)+time_summing_last_actions],[T_set,stabilization_times[index]+np.absolute(T_set-T_now)/(ramp_rates[index]/60.0)+time_summing_last_actions+estimated_impedance_time_per_temperature]]
        step_done = False
        while not step_done:
            if device_temperature is not None:
                T = device_temperature.get_value()
                if T[0] > 2000:
                    T[0] = 0 # make graphical output nicer in case of overflow
            else:
                T = [0,0]
            PV = device_oven.get_pv()
            if PV is None: # We have a communication error. Stop the program
                step_done = True
                continue
            time_val = time.time() - t0
            # graphical output
            data_T_t[0].append([T[0],time_val])
            data_T_t[1].append([PV,time_val])
            data_P_t[3] = [PV,time_val]
            if GUI:
                curve_T_t[0].setData(x=[k[1] for k in data_T_t[0]], y=[k[0] for k in data_T_t[0]], _callSync='off') # Chamber
                curve_T_t[1].setData(x=[k[1] for k in data_T_t[1]], y=[k[0] for k in data_T_t[1]], _callSync='off') # PV
                curve_P_t[1].setData(x=[k[1] for k in data_P_t[1]], y=[k[0] for k in data_P_t[1]], _callSync='off') # ac_measurement
                curve_P_t[3].setData(x=[time_val], y=[PV], _callSync='off')
            if time_val > stabilization_times[index]+np.absolute(T_set-T_now)/(ramp_rates[index]/60.0)+time_summing_last_actions:
                time_summing_last_actions = time_summing_last_actions+stabilization_times[index]+np.absolute(T_set-T_now)/(ramp_rates[index]/60.0)
                step_done = True
                # Now we can start with impedance measurement  
                time_before_impedance_run = time_val
                if start_frequency < end_frequency:
                    low_frequency = start_frequency
                    high_frequency = end_frequency
                else:
                    low_frequency = end_frequency
                    high_frequency = start_frequency
                if device_impedance.get_id() is "Gamry_R600":
                    device_impedance.create_impedance_object()
                    time.sleep(21) # This is very important. Gamry needs at least 10 sec to startup. Do NOT continue before this is done
                    device_impedance.setup_impedance_measurement()
                    time.sleep(5)
                    device_impedance.perform_impedance_measurement(low_frequency, high_frequency, ac_amplitude, num_points_per_decade)
                elif device_impedance.get_id() is "Zahner_IM6":
                    device_impedance.setup_impedance_measurement(7,ac_amplitude,bias)
                    frequency_values_generated = np.logspace(np.log10(low_frequency),np.log10(high_frequency),int(num_points_per_decade)*np.log10(high_frequency/low_frequency)) 
                    frequency_values_without_50Hz = [float(i+4.5) if np.absolute(i-50)<1.0 else i for i in frequency_values_generated]
                    frequency_values_without_100Hz = [float(i+2.5) if np.absolute(i-100)<1.0 else i for i in frequency_values_without_50Hz]
                    frequency_values_without_200Hz = [float(i+1.5) if np.absolute(i-200)<0.8 else i for i in frequency_values_without_100Hz]
                    time.sleep(3)
                done = False
                total_number_measurement_points = len(np.logspace(np.log10(low_frequency),np.log10(high_frequency),int(num_points_per_decade)*np.log10(high_frequency/low_frequency)))
                number_of_points_measured = 0
                current_number_of_points_measured = 0
                data_bias_ampl_time_range_err_temp = []
                if device_impedance.get_id() is "Gamry_R600":
                    while not done:
                        time.sleep(10) # Do not generate too much overhead over the network interface
                        if current_number_of_points_measured > number_of_points_measured: # There is new data to be added to the plot!
                            N = device_impedance.get_nyquist_data()
                            B = device_impedance.get_bode_data()
                            # How many new datapoints are available?
                            a = 0
                            print data_Zi_Zr[index]
                            if data_Zi_Zr[index]:
                                a = len(data_Zi_Zr[index][0])
                            new_points = len(N[0])-a
                            print "N",N
                            print "NPoints",new_points
                            append_indices = [i+1 for i in range(new_points)][::-1]
                            print "f",append_indices
                            for j in append_indices:
                                data_Zi_Zr[index].append([-N[1][-j],N[0][-j]])
                                data_freq_mod[index].append([B[0][-j],B[1][-j]])
                        if current_number_of_points_measured >= total_number_measurement_points:
                            done = True
                        if GUI:
                            curve_Zi_Zr[index].setData(x=[k[1] for k in data_Zi_Zr[index]], y=[k[0] for k in data_Zi_Zr[index]], _callSync='off')
                            curve_freq_mod[index].setData(x=[k[0] for k in data_freq_mod[index]], y=[k[1] for k in data_freq_mod[index]], _callSync='off')
                        number_of_points_measured = current_number_of_points_measured
                        current_number_of_points_measured = device_impedance.get_number_of_points_measured()
                elif device_impedance.get_id() is "Zahner_IM6":
                    device_impedance.switch_cell_on()
                    for frequency in frequency_values_without_200Hz[::-1]: # reverse list so that it starts with the highest frequencies for faster plotting
                        # Try 5 times for this frequency, then continue
                        for i in range(5):
                            a = device_impedance.perform_single_measurement(frequency,1000*ac_amplitude,bias)
                            if a is None: # Means Potentiostatic loop interrupted! error message appeared.
                                device_impedance.switch_cell_on() # again
                                continue
                            else:
                                break
                        if a is None:
                            continue # No data for this frequency. Try another one
                        data_Zi_Zr[index].append([-a[1],a[0]])
                        # Calculate modulus of impedance
                        modulus = np.sqrt(a[0]**2+a[1]**2)
                        data_freq_mod[index].append([frequency,modulus])
                        time_val = time.time() - t0
                        PV = device_oven.get_pv()
                        data_T_t[1].append([PV,time_val])
                        temperature_at_sample = PV
                        if device_temperature is not None:
                            T1 = device_temperature.get_value()
                            temperature_at_sample = T1[0]
                            data_T_t[0].append([temperature_at_sample,time_val])
                        data_bias_ampl_time_range_err_temp.append([bias,ac_amplitude,0,time_val,a[2],0,temperature_at_sample])
                        # graphical output
                        data_P_t[3] = [PV,time_val]
                        if GUI:
                            curve_Zi_Zr[index].setData(x=[k[1] for k in data_Zi_Zr[index]], y=[k[0] for k in data_Zi_Zr[index]], _callSync='off')
                            curve_freq_mod[index].setData(x=[k[0] for k in data_freq_mod[index]], y=[k[1] for k in data_freq_mod[index]], _callSync='off')
                            curve_T_t[0].setData(x=[k[1] for k in data_T_t[0]], y=[k[0] for k in data_T_t[0]], _callSync='off')
                            curve_T_t[1].setData(x=[k[1] for k in data_T_t[1]], y=[k[0] for k in data_T_t[1]], _callSync='off')
                            curve_P_t[3].setData(x=[time_val], y=[PV], _callSync='off')
                device_impedance.flush()
                data_to_write = [data_Zi_Zr[index][::-1],data_freq_mod[index][::-1],data_bias_ampl_time_range_err_temp[::-1]]
                # In which cycle are we at the moment?
                if T_now <= T_set:
                    if step_label == "C": # was the last action a cooling?
                        heating_index = heating_index+1
                    step_label = "H" # means heating step
                    step_index = heating_index
                else:
                    if step_label == "H": # was the last action a heating?
                        cooling_index = cooling_index+1
                    step_label = "C" # cooling
                    step_index = cooling_index
                bias_label = ""
                if bias != 0:
                    bias_label = str(bias)+"bias_"
                write_file_zview(data_to_write,path,filename="S1_"+bias_label+str(step_label)+str(step_index)+"_"+str(T_set)+".csv")
                T_now = PV
                time_val = time.time() - t0
                impedance_time = time_val-time_before_impedance_run
                time_summing_last_actions = time_summing_last_actions+impedance_time
                # Now impedance is done for this temperature. We need to update the prediction graph and also the air-cooling
                estimated_impedance_time_per_run = impedance_time
                estimated_impedance_time_per_temperature = estimated_impedance_time_per_run*number_of_repetitions
                #TODO
                if (index+1) < len(temperature_values):
                    device_oven.set_sp1(temperature_values[index+1])
                    device_oven.set_setpoint_rate(ramp_rates[index+1])
    return
    
def impedance(device_impedance, start_frequency, end_frequency, ac_amplitude=0.05, bias=0, num_points_per_decade=10, new_row=False, GUI=True): # at the moment only Potentiostatic-mode available
    room_temperature = 23
    if start_frequency < end_frequency:
        low_frequency = start_frequency
        high_frequency = end_frequency
    else:
        low_frequency = end_frequency
        high_frequency = start_frequency
    if device_impedance.get_id() is "Gamry_R600":
        device_impedance.create_impedance_object()
        time.sleep(21) # This is very important. Gamry needs at least 10 sec to startup. Do NOT continue before this is done
        device_impedance.setup_impedance_measurement()
        time.sleep(5)
        device_impedance.perform_impedance_measurement(low_frequency, high_frequency, ac_amplitude,num_points_per_decade)
    elif device_impedance.get_id() is "Zahner_IM6" or device_impedance.get_id() is "Solartron":
        device_impedance.setup_impedance_measurement(7,ac_amplitude,bias)
        if device_impedance.is_ready():
            device_impedance.switch_cell_on()
        frequency_values_generated = np.logspace(np.log10(low_frequency),np.log10(high_frequency),int(num_points_per_decade)*np.log10(high_frequency/low_frequency)) 
        frequency_values_without_50Hz = [float(i+4.5) if np.absolute(i-50)<1.0 else i for i in frequency_values_generated]
        frequency_values_without_100Hz = [float(i+2.5) if np.absolute(i-100)<1.0 else i for i in frequency_values_without_50Hz]
        frequency_values_without_200Hz = [float(i+1.5) if np.absolute(i-200)<0.8 else i for i in frequency_values_without_100Hz]
        time.sleep(3)
    done = False
    total_number_measurement_points = len(np.logspace(np.log10(low_frequency),np.log10(high_frequency),int(num_points_per_decade)*np.log10(high_frequency/low_frequency)))
    number_of_points_measured = 0
    current_number_of_points_measured = 0
    data_bias_ampl_time_range_err_temp = []
    data_Zi_Zr = []
    data_freq_mod = []
    if GUI:
        # create an empty list in the remote process
        data_Zi_Zr = proc.transfer([])
        p3 = win.addPlot(title="Nyquist plot")
        curve_Zi_Zr = p3.plot(pen=None, symbol='+')
        p3.setLabel('left', "-Zimag", units='Ohm')
        p3.setLabel('bottom', "Zreal", units='Ohm')
        #p3.setAspectLocked(True)
        #p3.setAspectLocked(lock=True, ratio=1.0) # That semi-circles remain semi-circles on zooming
        curve_Zi_Zr.setData(data_Zi_Zr, _callSync='off')
        
        p3 = win.addPlot(title="Bode plot")
        curve_freq_mod = p3.plot(pen=None, symbol='+')
        p3.setLabel('left', "abs(Z)")
        p3.setLabel('bottom', "frequency", units='Hz')
        p3.setAspectLocked(True)
        p3.setLogMode(x=True,y=True)
        curve_freq_mod.setData(data_freq_mod, _callSync='off')
        if new_row:
            win.nextRow()
    if device_impedance.get_id() is "Gamry_R600":
        while not done:
            time.sleep(10) # Do not generate too much overhead over the network interface
            if current_number_of_points_measured > number_of_points_measured: # There is new data to be added to the plot!
                N = device_impedance.get_nyquist_data()
                B = device_impedance.get_bode_data()
                # How many new datapoints are available?
                a = 0
                if data_Zi_Zr:
                    a = len(data_Zi_Zr[0])
                new_points = len(N[0])-a
                append_indices = [i+1 for i in range(new_points)][::-1]
                for j in append_indices:
                    data_Zi_Zr.append([-N[1][-j],N[0][-j]])
                    data_freq_mod.append([B[0][-j],B[1][-j]])
            if current_number_of_points_measured >= total_number_measurement_points:
                done = True
            if GUI:
                curve_Zi_Zr.setData(x=[k[1] for k in data_Zi_Zr], y=[k[0] for k in data_Zi_Zr], _callSync='off')
                curve_freq_mod.setData(x=[k[0] for k in data_freq_mod], y=[k[1] for k in data_freq_mod], _callSync='off')
            number_of_points_measured = current_number_of_points_measured
            current_number_of_points_measured = device_impedance.get_number_of_points_measured()
    elif device_impedance.get_id() is "Zahner_IM6" or device_impedance.get_id() is "Solartron":
        t0 = time.time()
        for frequency in frequency_values_without_200Hz[::-1]: # reverse list so that it starts with the highest frequencies for faster plotting
            # Try 5 times for this frequency, then continue
            for i in range(5):
                a = device_impedance.perform_single_measurement(frequency,1000*ac_amplitude,bias)
                if a is None: # Means Potentiostatic loop interrupted! error message appeared.
                    device_impedance.switch_cell_on() # again
                    continue
                else:
                    break
            if a is None:
                continue
            data_Zi_Zr.append([-a[1],a[0]])
            # Calculate modulus of impedance
            modulus = np.sqrt(a[0]**2+a[1]**2)
            data_freq_mod.append([frequency,modulus])
            time_val = time.time()-t0
            data_bias_ampl_time_range_err_temp.append([bias,ac_amplitude,0,time_val,a[2],0,room_temperature])
            if GUI:
                curve_Zi_Zr.setData(x=[k[1] for k in data_Zi_Zr], y=[k[0] for k in data_Zi_Zr], _callSync='off')
                curve_freq_mod.setData(x=[k[0] for k in data_freq_mod], y=[k[1] for k in data_freq_mod], _callSync='off')
    device_impedance.close()
    return [data_Zi_Zr[::-1],data_freq_mod[::-1],data_bias_ampl_time_range_err_temp[::-1]]
    
def write_file_zview(data,path="/home/electrochem/lost_data",filename="impedance_data.csv"): 
    path = path.rstrip("/")
    if path == "/home/electrochem/lost_data":
        # We need to put the data in the lost+found folder
        path = path+"/"+datetime.datetime.strftime(datetime.datetime.now(),"%Y%m%d%H%M%S")
        os.makedirs(path)
    else:
        try:
            if not os.path.exists(path): 
                os.makedirs(path)
        except Exception:
            path = "/home/electrochem/lost_data"+"/"+datetime.datetime.strftime(datetime.datetime.now(),"%Y%m%d%H%M%S")
            print "There was a problem with the path you specified. Data has been moved to:",path
            os.makedirs(path)
    # now start saving the impedance data into a tab separated file which is readable by ZView2
    try:
        if os.path.isfile(path+'/'+filename):
            filename = filename[:-4]+str("_")+datetime.datetime.strftime(datetime.datetime.now(),"%Y%m%d%H%M%S")+str(".csv")
            print "The filename you want to save this data already exists! To prevent overwrite this has been used:",filename
        with open(path+'/'+filename, 'w') as f:
            f.write("Frequency\tZ'\tZ''\tModulus\tPhase\tBias\tAmplitude\tAux\ttime\tRange\tError\tTemperature\n\n\n\n\n\n\n")
            for line in range(len(data[0])):
                modulus = np.sqrt(data[0][line][1]**2+data[0][line][0]**2)
                phase = np.angle(complex(data[0][line][1],data[0][line][0]),True)
                f.write(str(data[1][line][0])+'\t'+str(data[0][line][1])+'\t'+str(-data[0][line][0])+'\t'+str(modulus)+'\t'+str(phase)+'\t'+str(data[2][line][0])+'\t'+str(data[2][line][1])+'\t'+str(data[2][line][2])+'\t'+str(data[2][line][3])+'\t'+str(data[2][line][4])+'\t'+str(data[2][line][5])+'\t'+str(data[2][line][6])+'\n')
    except Exception:
        print "Data could not be writen to the file. No access? Here is the data:"
        for line in range(len(data[0])):
            print str(data[1][line][0])+'\t'+str(data[0][line][1])+'\t'+str(-data[0][line][0])+'\t'+str(modulus)+'\t'+str(phase)+'\t'+str(data[2][line][0])+'\t'+str(data[2][line][1])+'\t'+str(data[2][line][2])+'\t'+str(data[2][line][3])+'\t'+str(data[2][line][4])+'\t'+str(data[2][line][5])+'\t'+str(data[2][line][6])+'\n'
    print "Data has been saved successfully in folder:",path
    return
    
def galvanostatic_cycling(device_smu,current_1,target_voltage_1,hold_time_1,hold_current_1,current_2,target_voltage_2,hold_time_2,hold_current_2,n=1,ocv_measurement_time=0,set_I_zero_after_cycle=False,new_row=False,GUI=True):
    delta = 0.05 # This is the voltage accuracy for change detection
    device_smu.reset()
    device_smu.set_offmode_high_impedance()
    device_smu.turn_output_off()
    device_smu.setup_voltage_measurement(1)
    data_0 = []
    data_1 = []
    data_2 = []
    data_3 = [[],[]]
    data_4 = [[],[]]
    if type(current_1)==float or type(current_1)==int:
       current_1 = [current_1] # make an array
    if type(target_voltage_1)==float or type(target_voltage_1)==int:
       target_voltage_1 = [target_voltage_1] # make an array
    if type(hold_time_1)==float or type(hold_time_1)==int:
       hold_time_1 = [hold_time_1] # make an array
    if type(hold_current_1)==float or type(hold_current_1)==int or isinstance(hold_current_1,type(None)):
       hold_current_1 = [hold_current_1] # make an array
    if type(current_2)==float or type(current_2)==int:
       current_2 = [current_2] # make an array
    if type(target_voltage_2)==float or type(target_voltage_2)==int:
       target_voltage_2 = [target_voltage_2] # make an array
    if type(hold_time_2)==float or type(hold_time_2)==int:
       hold_time_2 = [hold_time_2] # make an array
    if type(hold_current_2)==float or type(hold_current_2)==int or isinstance(hold_current_2,type(None)):
       hold_current_2 = [hold_current_2] # make an array
    if type(n)==float or type(n)==int:
       n = [n] # make an array
    if type(set_I_zero_after_cycle)==bool:
       set_I_zero_after_cycle = [set_I_zero_after_cycle] # make an array
    # Compare length of arrays. Make them all the same
    maxlength = max([len(current_1),len(target_voltage_1),len(hold_time_1),len(hold_current_1),len(current_2),len(target_voltage_2),len(hold_time_2),len(hold_current_2)])
    while len(current_1) < maxlength:
        current_1.append(current_1[-1])
    while len(current_2) < maxlength:
        current_2.append(current_2[-1])
    while len(target_voltage_1) < maxlength:
        target_voltage_1.append(target_voltage_1[-1])
    while len(target_voltage_2) < maxlength:
        target_voltage_2.append(target_voltage_2[-1])
    while len(hold_time_1) < maxlength:
        hold_time_1.append(hold_time_1[-1])
    while len(hold_time_2) < maxlength:
        hold_time_2.append(hold_time_2[-1])
    while len(hold_current_1) < maxlength:
        hold_current_1.append(hold_current_1[-1])
    while len(hold_current_2) < maxlength:
        hold_current_2.append(hold_current_2[-1])
    while len(n) < maxlength:
        n.append(n[-1])
    while len(set_I_zero_after_cycle) < maxlength:
        set_I_zero_after_cycle.append(set_I_zero_after_cycle[-1])
    charge_first = True
    if target_voltage_1[0] < target_voltage_2[0]:
        charge_first = False
    if GUI:
        connected_lines_array_charge = np.array([], np.int32)
        connected_lines_array_discharge = np.array([], np.int32)
        if ocv_measurement_time != 0:
            p0 = win.addPlot(title="open circuit Voltage vs. time")
            curve_0 = p0.plot(pen='y')
            p0.setLabel('left', "OCV", units='V')
            p0.setLabel('bottom', "time", units='s')
            curve_0.setData(data_0, _callSync='off')
            
        p1 = win.addPlot(title="Voltage vs. time")
        curve_1 = p1.plot(pen='y')
        p1.setLabel('left', "Voltage", units='V')
        p1.setLabel('bottom', "time", units='s')
        curve_1.setData(data_1, _callSync='off')

        p2 = win.addPlot(title="Current vs. time")
        curve_2 = p2.plot(pen='y')
        p2.setLabel('left', "Current", units='A')
        p2.setLabel('bottom', "time", units='s')
        curve_2.setData(data_2, _callSync='off')
        
        win.nextRow()

        p3 = win.addPlot(title="Voltage vs. Capacity*Mass")
        curve_3 = []
        p3.setLabel('left', "Voltage", units='V')
        p3.setLabel('bottom', "Capacity*Mass", units='As')
        p3.addLegend()
        curve = p3.plot(pen=(0,2),name="charge")
        curve_3.append(curve)
        curve = p3.plot(pen=(1,2),name="discharge")
        curve_3.append(curve)
        curve_3[0].setData(data_3[0], _callSync='off')
        curve_3[1].setData(data_3[1], _callSync='off')
        
        p4 = win.addPlot(title="Capacity*Mass vs. Cycle")
        curve_4 = []
        p4.setLabel('left', "Capacity*Mass", units='As')
        p4.setLabel('bottom', "Cycle", units='')
        p4.addLegend()
        curve = p4.plot(pen=(0,2),symbol='+',name="charge")
        curve_4.append(curve)
        curve = p4.plot(pen=(1,2),symbol='+',name="discharge")
        curve_4.append(curve)
        curve_4[0].setData(data_4[0], _callSync='off')
        curve_4[1].setData(data_4[1], _callSync='off')
        
        if new_row:
            win.nextRow()
    t0 = time.time() # ocv start time
    device_smu.turn_output_on()
    if ocv_measurement_time != 0:
        while time.time() - t0 < ocv_measurement_time:
            V = device_smu.get_voltage()
            timestamp = time.time()-t0
            data_0.append([V,timestamp])
            if GUI:
                curve_0.setData(x=[k[1] for k in data_0], y=[k[0] for k in data_0], _callSync='off')
    cycle_total = 1
    t0 = time.time() # measurement start time
    OCV = device_smu.get_voltage()
    for i,individual_n in enumerate(n):
        cycle = 1
        while cycle <= individual_n:
            if set_I_zero_after_cycle[i] and not cycle_total == 1:
                device_smu.turn_output_off()
                time.sleep(10)
                device_smu.set_current(current_1[i])
                #device_smu.set_compliance_voltage(target_voltage_1[i]+np.sign(target_voltage_1[i])*delta) # 10mV higher than max so that max can actually be reached
                device_smu.turn_output_on()
            else:
                device_smu.set_current(current_1[i])
                #device_smu.set_compliance_voltage(target_voltage_1[i]+np.sign(target_voltage_1[i])*delta) # 10mV higher than max so that max can actually be reached
                device_smu.turn_output_on()
            capacity_t0 = time.time()
            target_voltage_1_reached = False
            target_voltage_1_counter = 0
            target_voltage_1_far_off = False
            target_voltage_1_counter_far_off = 0
            hold_time_1_reached = False
            start_holdtime_1 = 0
            hold_current_1_reached = False
            polarity_change = False
            polarity_change_counter = 0
            data_3_array = []
            while not ((target_voltage_1_reached and hold_time_1_reached and hold_current_1_reached) or polarity_change or target_voltage_1_far_off):
                V = device_smu.get_voltage()
                I = device_smu.get_current()
                timestamp = time.time()-t0
                capacity_timestamp = time.time()-capacity_t0
                data_1.append([V,timestamp])
                data_2.append([I,timestamp])
                if charge_first:
                    data_3[0].append([V,np.absolute(I)*capacity_timestamp])
                    connected_lines_array_charge = np.append(connected_lines_array_charge,1)
                else:
                    data_3[1].append([V,np.absolute(I)*capacity_timestamp])
                    connected_lines_array_discharge = np.append(connected_lines_array_discharge,1)
                data_3_array.append([V,np.absolute(I)*capacity_timestamp])
                if GUI:
                    curve_1.setData(x=[k[1] for k in data_1], y=[k[0] for k in data_1], _callSync='off')
                    curve_2.setData(x=[k[1] for k in data_2], y=[k[0] for k in data_2], _callSync='off')
                    curve_3[0].setData(x=[k[1] for k in data_3[0]], y=[k[0] for k in data_3[0]],connect=connected_lines_array_charge, _callSync='off')
                    curve_3[1].setData(x=[k[1] for k in data_3[1]], y=[k[0] for k in data_3[1]],connect=connected_lines_array_discharge, _callSync='off')
                if np.absolute(V-target_voltage_1[i]) <= delta:
                    target_voltage_1_counter = target_voltage_1_counter+1
                    if target_voltage_1_counter >= 10: # ten measurment points need to be in the target range in order to trigger; not only on random noise
                        target_voltage_1_reached = True
                        if start_holdtime_1 == 0:
                            start_holdtime_1 = time.time()
                if (V < target_voltage_1[i] and target_voltage_1[i]<target_voltage_2[i]) or (V > target_voltage_1[i] and target_voltage_1[i]>target_voltage_2[i]):
                    target_voltage_1_counter_far_off = target_voltage_1_counter_far_off+1
                    if target_voltage_1_counter_far_off >= 20: # 20 measurment points need to be far off in order to trigger; not only on random noise
                        target_voltage_1_far_off = True
                if np.sign(V) != np.sign(target_voltage_1[i]): # we overloaded the cell and apply negative voltage to maintain the current
                    polarity_change_counter = polarity_change_counter+1
                    if polarity_change_counter >= 5: # 5 measurment points; not only on random noise
                        polarity_change = True
                if time.time()-start_holdtime_1 >= hold_time_1[i]:
                    hold_time_1_reached = True
                if hold_current_1[i] is None or np.absolute(I) < np.absolute(hold_current_1[i]): # keep V_max till I falls below this I value
                    hold_current_1_reached = True
            if charge_first:
                data_4[0].append([max([k[1] for k in data_3_array]),cycle_total])
                connected_lines_array_charge[-1] = 0 # not connected between different segments
            else:
                data_4[1].append([max([k[1] for k in data_3_array]),cycle_total])
                connected_lines_array_discharge[-1] = 0 # not connected between different segments
            if GUI:
                curve_4[0].setData(x=[k[1] for k in data_4[0]], y=[k[0] for k in data_4[0]], _callSync='off')
                curve_4[1].setData(x=[k[1] for k in data_4[1]], y=[k[0] for k in data_4[1]], _callSync='off')
            device_smu.set_current(current_2[i])
            #device_smu.set_compliance_voltage(target_voltage_2[i]+np.sign(target_voltage_2[i])*delta) # 10mV higher than max so that max can actually be reached
            capacity_t0 = time.time()
            target_voltage_2_reached = False
            target_voltage_2_counter = 0
            target_voltage_2_far_off = False
            target_voltage_2_counter_far_off = 0
            hold_time_2_reached = False
            start_holdtime_2 = 0
            hold_current_2_reached = False
            if polarity_change:
                print "WARNING: Device-under-test has been overloaded! An oposite polarity voltage had to be applied to maintain the set current"
            polarity_change = False
            polarity_change_counter = 0
            data_3_array = []
            while not ((target_voltage_2_reached and hold_time_2_reached and hold_current_2_reached) or polarity_change or target_voltage_2_far_off):
                V = device_smu.get_voltage()
                I = device_smu.get_current()
                timestamp = time.time()-t0
                capacity_timestamp = time.time()-capacity_t0
                data_1.append([V,timestamp])
                data_2.append([I,timestamp])
                if charge_first:
                    data_3[1].append([V,np.absolute(I)*capacity_timestamp])
                    connected_lines_array_discharge = np.append(connected_lines_array_discharge,1)
                else:
                    data_3[0].append([V,np.absolute(I)*capacity_timestamp])
                    connected_lines_array_charge = np.append(connected_lines_array_charge,1)
                data_3_array.append([V,np.absolute(I)*capacity_timestamp])
                if GUI:
                    curve_1.setData(x=[k[1] for k in data_1], y=[k[0] for k in data_1], _callSync='off')
                    curve_2.setData(x=[k[1] for k in data_2], y=[k[0] for k in data_2], _callSync='off')
                    curve_3[0].setData(x=[k[1] for k in data_3[0]], y=[k[0] for k in data_3[0]],connect=connected_lines_array_charge, _callSync='off')
                    curve_3[1].setData(x=[k[1] for k in data_3[1]], y=[k[0] for k in data_3[1]],connect=connected_lines_array_discharge, _callSync='off')
                if np.absolute(V-target_voltage_2[i]) <= delta:
                    target_voltage_2_counter = target_voltage_2_counter+1
                    if target_voltage_2_counter >= 10: # ten measurment points need to be in the target range in order to trigger; not only on random noise
                        target_voltage_2_reached = True
                        if start_holdtime_2 == 0:
                            start_holdtime_2 = time.time()
                if (V < target_voltage_2[i] and target_voltage_2[i]<target_voltage_1[i]) or (V > target_voltage_2[i] and target_voltage_2[i]>target_voltage_1[i]):
                    target_voltage_2_counter_far_off = target_voltage_2_counter_far_off+1
                    if target_voltage_2_counter_far_off >= 20: # 20 measurment points need to be far off in order to trigger; not only on random noise
                        target_voltage_2_far_off = True
                if np.sign(V) != np.sign(target_voltage_2[i]): # we overloaded the cell and apply negative voltage to maintain the current
                    polarity_change_counter = polarity_change_counter+1
                    if polarity_change_counter >= 5: # 5 measurment points; not only on random noise
                        polarity_change = True
                if time.time()-start_holdtime_2 >= hold_time_2[i]:
                    hold_time_2_reached = True
                if hold_current_2[i] is None or np.absolute(I) < np.absolute(hold_current_2[i]): # keep V_max till I falls below this I value
                    hold_current_2_reached = True
            if polarity_change:
                print "WARNING: Device-under-test has been overloaded! An oposite polarity voltage had to be applied to maintain the set current"
            if charge_first:
                data_4[1].append([max([k[1] for k in data_3_array]),cycle_total])
                connected_lines_array_discharge[-1] = 0 # not connected between different segments
            else:
                data_4[0].append([max([k[1] for k in data_3_array]),cycle_total])
                connected_lines_array_charge[-1] = 0 # not connected between different segments
            if GUI:
                curve_4[0].setData(x=[k[1] for k in data_4[0]], y=[k[0] for k in data_4[0]], _callSync='off')
                curve_4[1].setData(x=[k[1] for k in data_4[1]], y=[k[0] for k in data_4[1]], _callSync='off')
            cycle = cycle+1
            cycle_total = cycle_total+1
    device_smu.turn_output_off_high_impedance()
    return [data_0,data_1,data_2,data_3]
    
def galvanostatic_cycling_nano(device_voltmeter,device_current_source,current_1,target_voltage_1,hold_time_1,hold_current_1,current_2,target_voltage_2,hold_time_2,hold_current_2,n=1,ocv_measurement_time=0,set_I_zero_after_cycle=False,new_row=False,GUI=True):
    device_current_source.reset()
    device_current_source.set_triax_inner_shield_to_low()
    device_current_source.set_triax_output_low_to_earth()
    delta = 0.06 # This is the voltage accuracy for compliance mode to decide when a condition is met
    device_voltmeter.reset()
    device_voltmeter.setup_voltage_measurement()
    data_0 = []
    data_1 = []
    data_2 = []
    data_3 = [[],[]]
    data_4 = [[],[]]
    if type(current_1)==float or type(current_1)==int:
       current_1 = [current_1] # make an array
    if type(target_voltage_1)==float or type(target_voltage_1)==int:
       target_voltage_1 = [target_voltage_1] # make an array
    if type(hold_time_1)==float or type(hold_time_1)==int:
       hold_time_1 = [hold_time_1] # make an array
    if type(hold_current_1)==float or type(hold_current_1)==int or isinstance(hold_current_1,type(None)):
       hold_current_1 = [hold_current_1] # make an array
    if type(current_2)==float or type(current_2)==int:
       current_2 = [current_2] # make an array
    if type(target_voltage_2)==float or type(target_voltage_2)==int:
       target_voltage_2 = [target_voltage_2] # make an array
    if type(hold_time_2)==float or type(hold_time_2)==int:
       hold_time_2 = [hold_time_2] # make an array
    if type(hold_current_2)==float or type(hold_current_2)==int or isinstance(hold_current_2,type(None)):
       hold_current_2 = [hold_current_2] # make an array
    if type(n)==float or type(n)==int:
       n = [n] # make an array
    if type(set_I_zero_after_cycle)==bool:
       set_I_zero_after_cycle = [set_I_zero_after_cycle] # make an array
    # Compare length of arrays. Make them all the same
    maxlength = max([len(current_1),len(target_voltage_1),len(hold_time_1),len(hold_current_1),len(current_2),len(target_voltage_2),len(hold_time_2),len(hold_current_2)])
    while len(current_1) < maxlength:
        current_1.append(current_1[-1])
    while len(current_2) < maxlength:
        current_2.append(current_2[-1])
    while len(target_voltage_1) < maxlength:
        target_voltage_1.append(target_voltage_1[-1])
    while len(target_voltage_2) < maxlength:
        target_voltage_2.append(target_voltage_2[-1])
    while len(hold_time_1) < maxlength:
        hold_time_1.append(hold_time_1[-1])
    while len(hold_time_2) < maxlength:
        hold_time_2.append(hold_time_2[-1])
    while len(hold_current_1) < maxlength:
        hold_current_1.append(hold_current_1[-1])
    while len(hold_current_2) < maxlength:
        hold_current_2.append(hold_current_2[-1])
    while len(n) < maxlength:
        n.append(n[-1])
    while len(set_I_zero_after_cycle) < maxlength:
        set_I_zero_after_cycle.append(set_I_zero_after_cycle[-1])
    charge_first = True
    if target_voltage_1[0] < target_voltage_2[0]:
        charge_first = False
    if GUI:
        connected_lines_array_charge = np.array([], np.int32)
        connected_lines_array_discharge = np.array([], np.int32)
        if ocv_measurement_time != 0:
            p0 = win.addPlot(title="open circuit Voltage vs. time")
            curve_0 = p0.plot(pen='y')
            p0.setLabel('left', "OCV", units='V')
            p0.setLabel('bottom', "time", units='s')
            curve_0.setData(data_0, _callSync='off')
            
        p1 = win.addPlot(title="Voltage vs. time")
        curve_1 = p1.plot(pen='y')
        p1.setLabel('left', "Voltage", units='V')
        p1.setLabel('bottom', "time", units='s')
        curve_1.setData(data_1, _callSync='off')

        p2 = win.addPlot(title="Current vs. time")
        curve_2 = p2.plot(pen='y')
        p2.setLabel('left', "Current", units='A')
        p2.setLabel('bottom', "time", units='s')
        curve_2.setData(data_2, _callSync='off')
        
        win.nextRow()

        p3 = win.addPlot(title="Voltage vs. Capacity*Mass")
        curve_3 = []
        p3.setLabel('left', "Voltage", units='V')
        p3.setLabel('bottom', "Capacity*Mass", units='As')
        p3.addLegend()
        curve = p3.plot(pen=(0,2),name="charge")
        curve_3.append(curve)
        curve = p3.plot(pen=(1,2),name="discharge")
        curve_3.append(curve)
        curve_3[0].setData(data_3[0], _callSync='off')
        curve_3[1].setData(data_3[1], _callSync='off')
        
        p4 = win.addPlot(title="Capacity*Mass vs. Cycle")
        curve_4 = []
        p4.setLabel('left', "Capacity*Mass", units='As')
        p4.setLabel('bottom', "Cycle", units='')
        p4.addLegend()
        curve = p4.plot(pen=(0,2),symbol='+',name="charge")
        curve_4.append(curve)
        curve = p4.plot(pen=(1,2),symbol='+',name="discharge")
        curve_4.append(curve)
        curve_4[0].setData(data_4[0], _callSync='off')
        curve_4[1].setData(data_4[1], _callSync='off')
        
        if new_row:
            win.nextRow()
    t0 = time.time() # ocv start time
    if ocv_measurement_time != 0:
        device_smu.turn_output_on()
        while time.time() - t0 < ocv_measurement_time:
            V = device_voltmeter.get_voltage()
            timestamp = time.time()-t0
            data_0.append([V,timestamp])
            if GUI:
                curve_0.setData(x=[k[1] for k in data_0], y=[k[0] for k in data_0], _callSync='off')
    cycle_total = 1
    t0 = time.time() # measurement start time
    for i,individual_n in enumerate(n):
        cycle = 1
        while cycle <= individual_n:
            if set_I_zero_after_cycle[i] and not cycle_total == 1:
                device_current_source.turn_output_off()
                time.sleep(10)
                device_current_source.set_current(current_1[i])
                #device_current_source.set_compliance_voltage(target_voltage_1[i]+np.sign(target_voltage_1[i])*delta) # 10mV higher than max so that max can actually be reached
                device_current_source.turn_output_on()
            else:
                device_current_source.set_current(current_1[i])
                #device_current_source.set_compliance_voltage(target_voltage_1[i]+np.sign(target_voltage_1[i])*delta) # 10mV higher than max so that max can actually be reached
                device_current_source.turn_output_on()
            capacity_t0 = time.time()
            target_voltage_1_reached = False
            target_voltage_1_counter = 0
            hold_time_1_reached = False
            start_holdtime_1 = 0
            hold_current_1_reached = False
            polarity_change = False
            polarity_change_counter = 0
            data_3_array = []
            while not ((target_voltage_1_reached and hold_time_1_reached and hold_current_1_reached) or polarity_change):
                V = device_voltmeter.get_voltage()
                I = device_current_source.get_current()
                timestamp = time.time()-t0
                capacity_timestamp = time.time()-capacity_t0
                data_1.append([V,timestamp])
                data_2.append([I,timestamp])
                if charge_first:
                    data_3[0].append([V,np.absolute(I)*capacity_timestamp])
                    connected_lines_array_charge = np.append(connected_lines_array_charge,1)
                else:
                    data_3[1].append([V,np.absolute(I)*capacity_timestamp])
                    connected_lines_array_discharge = np.append(connected_lines_array_discharge,1)
                data_3_array.append([V,np.absolute(I)*capacity_timestamp])
                if GUI:
                    curve_1.setData(x=[k[1] for k in data_1], y=[k[0] for k in data_1], _callSync='off')
                    curve_2.setData(x=[k[1] for k in data_2], y=[k[0] for k in data_2], _callSync='off')
                    curve_3[0].setData(x=[k[1] for k in data_3[0]], y=[k[0] for k in data_3[0]],connect=connected_lines_array_charge, _callSync='off')
                    curve_3[1].setData(x=[k[1] for k in data_3[1]], y=[k[0] for k in data_3[1]],connect=connected_lines_array_discharge, _callSync='off')
                if np.absolute(V-target_voltage_1[i]) <= delta:
                    target_voltage_1_counter = target_voltage_1_counter+1
                    if target_voltage_1_counter >= 10: # ten measurment points need to be in the target range in order to trigger; not only on random noise
                        target_voltage_1_reached = True
                        if start_holdtime_1 == 0:
                            start_holdtime_1 = time.time()
                if np.sign(V) != np.sign(target_voltage_1[i]): # we overloaded the cell and apply negative voltage to maintain the current
                    polarity_change_counter = polarity_change_counter+1
                    if polarity_change_counter >= 5: # 5 measurment points; not only on random noise
                        polarity_change = True
                if time.time()-start_holdtime_1 >= hold_time_1[i]:
                    hold_time_1_reached = True
                if hold_current_1[i] is None or np.absolute(I) < np.absolute(hold_current_1[i]): # keep V_max till I falls below this I value
                    hold_current_1_reached = True
            if charge_first:
                data_4[0].append([max([k[1] for k in data_3_array]),cycle_total])
                connected_lines_array_charge[-1] = 0 # not connected between different segments
            else:
                data_4[1].append([max([k[1] for k in data_3_array]),cycle_total])
                connected_lines_array_discharge[-1] = 0 # not connected between different segments
            if GUI:
                curve_4[0].setData(x=[k[1] for k in data_4[0]], y=[k[0] for k in data_4[0]], _callSync='off')
                curve_4[1].setData(x=[k[1] for k in data_4[1]], y=[k[0] for k in data_4[1]], _callSync='off')
            device_current_source.set_current(current_2[i])
            #device_current_source.set_compliance_voltage(target_voltage_2[i]+np.sign(target_voltage_2[i])*delta) # 10mV higher than max so that max can actually be reached
            capacity_t0 = time.time()
            target_voltage_2_reached = False
            target_voltage_2_counter = 0
            hold_time_2_reached = False
            start_holdtime_2 = 0
            hold_current_2_reached = False
            if polarity_change:
                print "WARNING: Device-under-test has been overloaded! An oposite polarity voltage had to be applied to maintain the set current"
            polarity_change = False
            polarity_change_counter = 0
            data_3_array = []
            while not ((target_voltage_2_reached and hold_time_2_reached and hold_current_2_reached) or polarity_change):
                V = device_voltmeter.get_voltage()
                I = device_current_source.get_current()
                timestamp = time.time()-t0
                capacity_timestamp = time.time()-capacity_t0
                data_1.append([V,timestamp])
                data_2.append([I,timestamp])
                if charge_first:
                    data_3[1].append([V,np.absolute(I)*capacity_timestamp])
                    connected_lines_array_discharge = np.append(connected_lines_array_discharge,1)
                else:
                    data_3[0].append([V,np.absolute(I)*capacity_timestamp])
                    connected_lines_array_charge = np.append(connected_lines_array_charge,1)
                data_3_array.append([V,np.absolute(I)*capacity_timestamp])
                if GUI:
                    curve_1.setData(x=[k[1] for k in data_1], y=[k[0] for k in data_1], _callSync='off')
                    curve_2.setData(x=[k[1] for k in data_2], y=[k[0] for k in data_2], _callSync='off')
                    curve_3[0].setData(x=[k[1] for k in data_3[0]], y=[k[0] for k in data_3[0]],connect=connected_lines_array_charge, _callSync='off')
                    curve_3[1].setData(x=[k[1] for k in data_3[1]], y=[k[0] for k in data_3[1]],connect=connected_lines_array_discharge, _callSync='off')
                if np.absolute(V-target_voltage_2[i]) <= delta:
                    target_voltage_2_counter = target_voltage_2_counter+1
                    if target_voltage_2_counter >= 10: # ten measurment points need to be in the target range in order to trigger; not only on random noise
                        target_voltage_2_reached = True
                        if start_holdtime_2 == 0:
                            start_holdtime_2 = time.time()
                if np.sign(V) != np.sign(target_voltage_2[i]): # we overloaded the cell and apply negative voltage to maintain the current
                    polarity_change_counter = polarity_change_counter+1
                    if polarity_change_counter >= 5: # 5 measurment points; not only on random noise
                        polarity_change = True
                if time.time()-start_holdtime_2 >= hold_time_2[i]:
                    hold_time_2_reached = True
                if hold_current_2[i] is None or np.absolute(I) < np.absolute(hold_current_2[i]): # keep V_max till I falls below this I value
                    hold_current_2_reached = True
            if polarity_change:
                print "WARNING: Device-under-test has been overloaded! An oposite polarity voltage had to be applied to maintain the set current"
            if charge_first:
                data_4[1].append([max([k[1] for k in data_3_array]),cycle_total])
                connected_lines_array_discharge[-1] = 0 # not connected between different segments
            else:
                data_4[0].append([max([k[1] for k in data_3_array]),cycle_total])
                connected_lines_array_charge[-1] = 0 # not connected between different segments
            if GUI:
                curve_4[0].setData(x=[k[1] for k in data_4[0]], y=[k[0] for k in data_4[0]], _callSync='off')
                curve_4[1].setData(x=[k[1] for k in data_4[1]], y=[k[0] for k in data_4[1]], _callSync='off')
            cycle = cycle+1
            cycle_total = cycle_total+1
    device_current_source.turn_output_off()
    return [data_0,data_1,data_2,data_3]
    
def conductivity_switcher(a,new_row=False, GUI=True):
    keithley_7001.close_channel(1,[11,21]) # SMU
    data_1 = []
    data_2 = []
    data_3 = []
    if GUI:
        # create an empty list in the remote process
        p1 = win.addPlot(title="current vs. time battery 1")
        curve_1 = p1.plot(pen='y')
        p1.setLabel('left', "Current", units='A')
        p1.setLabel('bottom', "time", units='s')
        curve_1.setData(data_1, _callSync='off')

        p2 = win.addPlot(title="current vs. time battery 2")
        curve_2 = p2.plot(pen='y')
        p2.setLabel('left', "Current", units='A')
        p2.setLabel('bottom', "time", units='s')
        curve_2.setData(data_2, _callSync='off')

        p3 = win.addPlot(title="current vs. time battery 3")
        curve_3 = p3.plot(pen='y')
        p3.setLabel('left', "Current", units='A')
        p3.setLabel('bottom', "time", units='s')
        curve_3.setData(data_3, _callSync='off')
      
        if new_row:
            win.nextRow()
    num_measurement_points = a
    v0 = 5
    t0 = time.time() # measurement start time
    old_time = 0 # to remember the timestamp in the (t-1) cycle. You need to find out the time for each loop
    timestamp = 0
    time_at_end = 0
    keithley_2601B.set_voltage(v0)
    keithley_2601B.turn_output_on()
    for t in range(num_measurement_points):
            keithley_7001.open_channel(1,[28,18])
            keithley_7001.close_channel(1,[30,20])
            time.sleep(0.5)
            I = keithley_2601B.get_current()
            timestamp = time.time()-t0
            data_1.append([I,timestamp])
            keithley_7001.open_channel(1,[30,20])
            keithley_7001.close_channel(1,[29,19])
            time.sleep(0.5)
            I = keithley_2601B.get_current()
            timestamp = time.time()-t0
            data_2.append([I,timestamp])
            keithley_7001.open_channel(1,[29,19])
            keithley_7001.close_channel(1,[28,18])
            time.sleep(0.5)
            I = keithley_2601B.get_current()
            timestamp = time.time()-t0
            data_3.append([I,timestamp])
            if GUI:
                curve_1.setData(x=[k[1] for k in data_1], y=[k[0] for k in data_1], _callSync='off')
                curve_2.setData(x=[k[1] for k in data_2], y=[k[0] for k in data_2], _callSync='off')
                curve_3.setData(x=[k[1] for k in data_3], y=[k[0] for k in data_3], _callSync='off')
    keithley_2601B.turn_output_off()
    keithley_7001.open_channel(1,[28,18,11,21])
    return [data_1,data_2,data_3]
    
# Open plotting window
win = rpg.GraphicsWindow(title="Basic plotting")
win.resize(1300,500)
win.setWindowTitle(window_title)

### Start Qt event loop unless running in interactive mode or using pyside.
#if __name__ == '__main__':
    #if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        #QtGui.QApplication.instance().exec_()
