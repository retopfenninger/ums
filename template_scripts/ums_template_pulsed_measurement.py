#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Unified measurement software UMS
# New measurement software for the electrochemical materials group, Prof. Jennifer Rupp
#
# Copyright (c) 2013 Reto Pfenninger, D-MATL ETH Zürich
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.

from source.ums import *

# Open the corresponding device you want to use for measurement
keithley_2602B = keithley_2602B(keithley_2602B_ip_address)
keithley_2602B.open()

tektronix_AFG3021C = tektronix_AFG3021C(tektronix_AFG3021C_ip_address)
tektronix_AFG3021C.open()

# Here comes your code with what you want to do:
increasing_voltage_pulse_sweep(keithley_2602B,tektronix_AFG3021C,delta_V = 0.5, V0 = 0, V_peak= 1.0, const_pulse_width = 0.5, num_measurement_points = 300)



# leave the following 2 lines unchanged. 
# Those let the window with the graph stay open after the program finished
while True: # run forever
    i=0
