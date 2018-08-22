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
gamry_R600 = gamry_R600()
gamry_R600.debug = True

# Here comes your code with what you want to do:
data = impedance(gamry_R600, 10, 100000, 0.050, 10)
print data
# leave the following 2 lines unchanged. 
# Those let the window with the graph stay open after the program finished
while True: # run forever
    i=0
