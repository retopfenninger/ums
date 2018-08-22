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
keithley_2601B = keithley_2601B(keithley_2601B_ip_address)
keithley_2601B.open()
keithley_2000 = keithley_2000(GPIB_USB_adapter,4)
eurotherm_2416 = eurotherm_2416('/dev/ttyS0', 1)

# Here comes your code with what you want to do:
arrhenius_dc(keithley_2000,keithley_2601B,eurotherm_2416,temperature_values=[100,150],ramp_rates=[5,10],stabilization_times=[600,1200],voltage_values=1.2,continuous_voltage=True)


# leave the following 2 lines unchanged. 
# Those let the window with the graph stay open after the program finished
while True: # run forever
    i=0
