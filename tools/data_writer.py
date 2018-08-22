#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Unified measurement software UMS
# New measurement software for the electrochemical materials group, Prof. Jennifer Rupp
#
# Copyright (c) 2016 Sören Boyn, department of materials, D-MATL, ETH Zürich
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

import os
import csv
import warnings


class DataWriterWarning(UserWarning):
    pass


class data_writer(object):
    DEFAULT_FILE_EXT            = '.csv'
    DEFAULT_FILE_NAME_SEP       = '_'       # separator between parts in filename
    DEFAULT_FILE_NAME_SUB_SEP   = '#'       # separator between items in each part of filename
    DEFAULT_FILE_ID_LEN         = 6
    
    
    def __init__(self, data_file_base_path, file_mode = 'wb', file_name_suppl_data = None, file_id = None, file_ext = None, file_name_sep = None, file_name_sub_sep = None, file_id_len = None, fieldnames = None, **formatparams):
        self.file_ext           = self.DEFAULT_FILE_EXT             if file_ext is None             else file_ext
        self.file_name_sep      = self.DEFAULT_FILE_NAME_SEP        if file_name_sep is None        else file_name_sep
        self.file_name_sub_sep  = self.DEFAULT_FILE_NAME_SUB_SEP    if file_name_sub_sep is None    else file_name_sub_sep
        self.file_id_len        = self.DEFAULT_FILE_ID_LEN          if file_id_len is None          else file_id_len
        
        data_file_base_path = os.path.normpath(data_file_base_path)
        
        self.data_file_dir       = os.path.dirname(data_file_base_path)
        self.data_file_name_base = self._remove_file_ext(os.path.basename(data_file_base_path))
        
        if file_id == None:
            # if no file_id is given, find out new one automatically
            self.file_id = self._get_next_file_id(self.data_file_dir)
        else:
            # if file_id is given, use this one
            self.file_id = file_id
        
        
        data_file_name_parts = []
        
        if not self.file_id == False:
            # incorporate file_id into the file name, unless it is set to False
            data_file_name_parts.append(self._format_file_id(self.file_id))
        
        data_file_name_parts.append(self.data_file_name_base)        
        
        if file_name_suppl_data:
            # if file_name_suppl_data is given, incorporate it into the file name
            data_file_name_parts.append(self._format_file_name_suppl_data(file_name_suppl_data))
        
        # construct final file name
        self.data_file_name = self.file_name_sep.join(data_file_name_parts) + self.file_ext
        
        self.data_file_path = os.path.join(self.data_file_dir, self.data_file_name)

        # issue a warning in case the file already exists and is going to be overwritten
        if file_mode[0].lower() == 'w' and os.path.isfile(self.data_file_path):
            warnings.warn('The data file "{}" already exists and will be overridden using filemode "{}"!'.format(self.data_file_path, file_mode), DataWriterWarning, stacklevel=2)

        # open data file
        self.data_file = open(os.path.join(self.data_file_path), file_mode)
        
        # create csv.writer instance
        self._csvwriter = csv.writer(self.data_file, **formatparams)
        
        if fieldnames:
            self._writeheader(fieldnames)
    

    def writerow(self, row):
        self._csvwriter.writerow(row)


    def writerows(self, rows):
        self._csvwriter.writerows(rows)


    def _writeheader(self, fieldnames):
        self.writerow(fieldnames)


    def _get_next_file_id(self, data_file_dir):
#        data_files_in_dir = [os.path.splitext(f)[0] for f in os.listdir(data_file_dir) if (os.path.isfile(os.path.join(data_file_dir, f)) and f.endswith(self.file_ext))]
        data_files_in_dir = [os.path.splitext(f)[0] for f in os.listdir(data_file_dir) if (f.endswith(self.file_ext))] # much faster without "isfile"
#        data_files_in_dir = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(data_file_dir, '[0-9]*' + self.file_ext))]
        
        highest_file_id = 0
        
        for data_file_name in data_files_in_dir:
            file_id = self._get_file_id_from_file_name(data_file_name)
            
            if file_id is not None and file_id > highest_file_id:
                highest_file_id = file_id
        
        return highest_file_id + 1


    def _get_file_id_from_file_name(self, file_name):
        file_prefix = file_name.split(self.file_name_sep, 1)[0]
        
        try:
            file_id = int(file_prefix)
        except ValueError:
            file_id = None
        finally:       
            return file_id


    def _format_file_name_suppl_data(self, file_name_suppl_data):
        file_name_suppl_data_parts = []
        
        if self._is_iterable_no_string(file_name_suppl_data): # ex: [('I', 5e-6), ('U', 1.2, 'V'), ('d', (1.456e-4, '{:0=+6.2f}')), 'noAmp']
            
            for suppl_data_item in file_name_suppl_data:
                file_name_suppl_data_parts.append(self._format_file_name_suppl_data_item(suppl_data_item))
        else:
            file_name_suppl_data_parts.append(str(file_name_suppl_data))
        
        return self.file_name_sep.join(file_name_suppl_data_parts)


    def _format_file_name_suppl_data_item(self, suppl_data_item):
        suppl_data_item_parts = []
        
        if self._is_iterable_no_string(suppl_data_item): # ex: ('d', (1.456e-4, '{:0=+6.2f}'))
            for suppl_data_item_part in suppl_data_item:
                suppl_data_item_parts.append(self._format_file_name_suppl_data_item_part(suppl_data_item_part))
        else: # ex: 'noAmp'
            suppl_data_item_parts.append(str(suppl_data_item))
        
        return self.file_name_sub_sep.join(suppl_data_item_parts)


    def _format_file_name_suppl_data_item_part(self, suppl_data_item_part):
        if self._is_iterable_no_string(suppl_data_item_part): # ex: (1.456e-4, '{:0=+6.2f}')
            return suppl_data_item_part[1].format(suppl_data_item_part[0])
        else: # ex: 'd'
            return str(suppl_data_item_part)


    def _format_file_id(self, file_id):
        return '{:0>{}s}'.format(str(file_id), self.file_id_len) # pad file_id by zeros upto file_id_len total length (can cope with string ids, too)


    def _remove_file_ext(self, file_name):
        str_len = len(self.file_ext)
        
        if file_name[-str_len:].lower() == self.file_ext.lower():
            return file_name[:-str_len]
        
        return file_name


    def _is_iterable_no_string(self, obj):
        return hasattr(obj, '__iter__') and not isinstance(obj, basestring) # from: http://stackoverflow.com/a/19944281


    @staticmethod
    def _show_warning(message, category = DataWriterWarning, filename = '', lineno = -1, line=None):
        print('[{}] {}'.format(category.__name__, message))


    # close data_file if still open
    def close(self):
        self.data_file.close()


    # for use in "with" statement
    def __enter__(self):
        return self


    # clean up on destruction
    def __del__(self):
        self.close()


    # for use in "with" statement
    def __exit__(self, type, value, traceback):
        self.close()
        return False


warnings.simplefilter('always', DataWriterWarning)
warnings.showwarning = data_writer._show_warning



#==============================================================================
# Little demo to show how the class can be used
#==============================================================================
if __name__ == "__main__":
    import time # just needed for this demo
    
    # 1) ============= using "with" statement is "best practice": no need to close the data file in this case!
    with data_writer('X:/Soeren/_test/IvsV_cycling_1.csv') as writer:
        writer.writerow([0, 0, 0, 0]) # add a single row
        
        for i in xrange(100): # add single rows in a loop
            writer.writerow([i, time.time(), 0.841, 84.12345678e-41])
        
        writer.writerows([[1, 2, 3, 4]] * 50) # add several rows at once
    
    
    # 2) ============= classical use: better close the data file in this case (even if it should do so automatically if everything runs smoothly)
    writer = data_writer('X:/Soeren/_test/IvsV_cycling_2.csv')
    
    writer.writerow([0, 0, 0, 0]) # add a single row
    
    for i in xrange(100): # add single rows in a loop
        writer.writerow([i, time.time(), 0.841, 84.12345678e-41])
    
    writer.writerows([[1, 2, 3, 4]] * 50) # add several rows at once
    
    writer.close() # close the data file
    
    
    # 3) ============= a fancier example
    with data_writer(
            'X:/Soeren/_test/IvsV_cycling_3.csv', # base path to the data file to be written (file_id will be prepened to the file name; if given, additional information is included)
            fieldnames           = ['a', 'b', 'c', 'd'], # column header to be included in the file
            file_name_suppl_data = [('Ugate', 5e-6), ('T', 300, 'K'), ('d', (1.556e-2, '{:0.2f}')), 'noAmp'] # additional information to be included in the file name [optional]
            ) as writer:
        
        writer.writerow([0, 0, 0, 0]) # add a single row
        
        for i in xrange(100): # add single rows in a loop
            writer.writerow([i, time.time(), 0.841, 84.12345678e-41])
        
        writer.writerows([[1, 2, 3, 4]] * 50) # add several rows at once
    
    
    # 4) ============= fixing the file id.
    # ATTENTION: this may lead to a file being overwritten in case it already exists! Use only, if you know what you are doing.
    with data_writer(
            'X:/Soeren/_test/IvsV_cycling_4.csv', # base path to the data file to be written (file_id will be prepened to the file name; if given, additional information is included)
            file_id = 123, # fixing the file id will prevent it from being determined automatically
            ) as writer:
        
        writer.writerow([0, 0, 0, 0]) # add a single row
        
        for i in xrange(100): # add single rows in a loop
            writer.writerow([i, time.time(), 0.841, 84.12345678e-41])
        
        writer.writerows([[1, 2, 3, 4]] * 50) # add several rows at once
    
    
    # 5) ============= disabling the file id to recover standard csv.writer behavior.
    # ATTENTION: this may lead to a file being overwritten in case it already exists! Use only, if you know what you are doing.
    with data_writer(
            'X:/Soeren/_test/IvsV_cycling_5.csv', # base path to the data file to be written (file_id will be prepened to the file name; if given, additional information is included)
            file_id = False, # disabling the file id by setting it to "False"
            ) as writer:
        
        writer.writerow([0, 0, 0, 0]) # add a single row
        
        for i in xrange(100): # add single rows in a loop
            writer.writerow([i, time.time(), 0.841, 84.12345678e-41])
        
        writer.writerows([[1, 2, 3, 4]] * 50) # add several rows at once
