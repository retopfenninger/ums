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


import time
import subprocess # for calling C++ functions from within python

path_to_keithley_kult_comunication_program = "keithley_kult_comunication_program.exe"

class keithley4200_device:
    def __init__(self):
        self.keithley_debug = True
        self.data = []
        self.interrupt = False # Variable which makes it possible to stop a running measurement
        return
        
    def send_string(self,gulu,data_string):
        if not self.interrupt:
            self.data = subprocess.check_call([path_to_keithley_kult_comunication_program, data_string])
        return self.data
        
    def get_data(self):
        if self.keithley_debug:
            print "Data is: ",self.data
        return self.data
        
    def get_number_of_points_measured(self):
        return len(self.data)
        
    def close(self):
        self.interrupt = True
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

        
# Little demo to show how the class can be used to acquire a simple impedance measurement
if __name__ == "__main__":
    keithley4200_device = keithley4200_device()
    print keithley4200_device.send_string("DE")
    keithley4200_device.close()


