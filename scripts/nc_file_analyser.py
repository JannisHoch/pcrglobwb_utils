# -*- coding: utf-8 -*-

import pcrglobwb_utils
import os, sys

#TODO: create something like that with click

ncfiles_list = sys.argv[1:-1]
grdc_file = str(sys.argv[-1])

print('get info from GRDC file', grdc_file)

grdc_plot_title, grdc_props = pcrglobwb_utils.get_grdc_info.get_grdc_station_properties(grdc_file)

df_grdc = pcrglobwb_utils.get_grdc_info.get_grdc_station_values(grdc_file, 
                                                                var_name='GRDC discharge [m3/s]', 
                                                                plot=True)
print(df_grdc.head())

for file in ncfiles_list:
    print(str(file))

print(grdc_file)