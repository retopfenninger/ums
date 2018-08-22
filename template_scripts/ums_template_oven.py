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
#keithley_2700 = keithley_2700("electrochem-m27",18)
#keithley_2000 = keithley_2000(USB,4)
eurotherm_2416 = eurotherm_2416('/dev/ttyS0', 1)

#keithley_2000.debug = True

# Here comes your code with what you want to do:
sintering(None,eurotherm_2416,temperature_values=840,ramp_rates=5.0,stabilization_times=43200) # 12 hours


# leave the following 2 lines unchanged. 
# Those let the window with the graph stay open after the program finished
while True: # run forever
    i=0
