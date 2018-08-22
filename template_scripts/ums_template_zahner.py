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
zahner_IM6 = zahner_IM6()

# Here comes your code with what you want to do:
#data = impedance(zahner_IM6, 0.1, 0.1e6, 0.1)
#data = impedance(zahner_IM6, 100, 5e6, 0.001)
#data = impedance(zahner_IM6, 1, 1.0e6, 0.05)

data = impedance(zahner_IM6, 0.01, 1.0e6, 0.2,bias=0, num_points_per_decade=10)
write_file_zview(data,"/home/retopf/Documents/ETH/MATL/PhD/data/test")

# leave the following 2 lines unchanged. 
# Those let the window with the graph stay open after the program finished
while True: # run forever
    i=0