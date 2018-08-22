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
keithley_2000 = keithley_2000("electrochem-m26",1)
eurotherm_2416 = eurotherm_2416("/dev/ttyS0",1)
zahner_IM6 = zahner_IM6()

# Here comes your code with what you want to do:
arrhenius_ac(keithley_2000,eurotherm_2416,zahner_IM6,temperature_values=[200,250,300],ramp_rates=5,stabilization_times=3600,ac_amplitude=0.1,path="/home/electrochem/umdata/Chucknorris/impedance")


# leave the following 2 lines unchanged.
# Those let the window with the graph stay open after the program finished
while True: # run forever
    i=0
