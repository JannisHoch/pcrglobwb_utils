# -*- coding: utf-8 -*-

import pcrglobwb_utils
import matplotlib.pyplot as plt
import datetime
import os, sys

#TODO: create something like that with click

# parsing arguments
ncfiles_list = sys.argv[1:-2]
grdc_file = str(sys.argv[-2])
out_dir = str(sys.argv[-1])

# provding plot names 
#TODO: make this more interactive and less hard-coded
new_var_name_obs = 'Q$obs$ GRDC [m3/s]'
new_var_name_sim = 'Q$sim$ PCR-GLOBWB [m3/s]'

# get current working directory
cwd = os.getcwd()

# initiate logging
sys.stdout = open(os.path.join(out_dir, 'logfile.log'), 'w')

print(datetime.datetime.now())
print('')

# get absolute path to GRDC file
grdc_file = os.path.join(cwd, grdc_file)

print('get info from GRDC file', os.path.abspath(grdc_file))
print('')

# get GRDC station properties
grdc_plot_title, grdc_props = pcrglobwb_utils.get_grdc_info.get_grdc_station_properties(grdc_file)
print('GRDC station properties are:')
print(grdc_props)
print('')

# get GRDC timeseries
df_grdc = pcrglobwb_utils.get_grdc_info.get_grdc_station_values(grdc_file, 
                                                                var_name=new_var_name_obs,
                                                                plot=False)

# go throuh all provided nc-files
#NOTE: tested with 1 file so far only
for file in ncfiles_list:

    nc_file = os.path.join(cwd, file)

    print('reading from nc-file', os.path.abspath(nc_file))
    print('')

    row, col = pcrglobwb_utils.utils.find_indices_from_coords(nc_file, 
                                                              grdc_props['longitude'], 
                                                              grdc_props['latitude'])
    
    q_sim = pcrglobwb_utils.timeseries.read_nc_file_at_indices(nc_file, 
                                                               row, 
                                                               col, 
                                                               plot_var_name=new_var_name_sim)

    df_eval, eval_dic = pcrglobwb_utils.timeseries.validate_results(df_grdc, 
                                                           q_sim, 
                                                           out_dir, 
                                                           new_var_name_obs, 
                                                           new_var_name_sim, 
                                                           plot=False,
                                                           save_fig=True)
    
    print('head and tail of evaluated dataframe columns')
    print(df_eval.head())
    print(df_eval.tail())
    print('')
    
    print('timeseries validation results are:')
    print(eval_dic)

