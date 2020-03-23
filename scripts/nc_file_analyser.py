# -*- coding: utf-8 -*-

import pcrglobwb_utils
import matplotlib.pyplot as plt
import os, sys

#TODO: create something like that with click

ncfiles_list = sys.argv[1:-1]
grdc_file = str(sys.argv[-1])

new_var_name_obs = 'Q$obs$ GRDC [m3/s]'
new_var_name_sim = 'Q$sim$ PCR-GLOBWB [m3/s]'

cwd = os.getcwd()
grdc_file = os.path.join(cwd, grdc_file)

print('get info from GRDC file', grdc_file)

grdc_plot_title, grdc_props = pcrglobwb_utils.get_grdc_info.get_grdc_station_properties(grdc_file)

df_grdc = pcrglobwb_utils.get_grdc_info.get_grdc_station_values(grdc_file, 
                                                                var_name=new_var_name_obs,
                                                                plot=False)

for file in ncfiles_list:

    nc_file = os.path.join(cwd, file)

    print('reading from nc-file', nc_file)

    row, col = pcrglobwb_utils.utils.find_indices_from_coords(nc_file, 
                                                              grdc_props['longitude'], 
                                                              grdc_props['latitude'])
    
    q_sim = pcrglobwb_utils.timeseries.read_nc_file_at_indices(nc_file, 
                                                               row, 
                                                               col, 
                                                               plot_var_name=new_var_name_sim)

    eval_dic = pcrglobwb_utils.timeseries.validate_results(df_grdc, q_sim, new_var_name_obs, new_var_name_sim, plot=True)
    print(eval_dic)

