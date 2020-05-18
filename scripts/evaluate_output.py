# -*- coding: utf-8 -*-

import pcrglobwb_utils
import matplotlib.pyplot as plt
import datetime
import os, sys

#TODO: create something like that with click

# parsing arguments and checking whether provided paths are absolute or relative
ncfiles_list = sys.argv[1:-2] # list of nc-files to be evaluated

grdc_file = str(sys.argv[-2]) # file with grdc info
if os.path.isabs(grdc_file):
    pass
else:
    grdc_file = os.path.join(os.getcwd(), grdc_file)

grdc_data = pcrglobwb_utils.obs_data.grdc_data(grdc_file)

out_dir = str(sys.argv[-1]) # path to output_dir

# check whether path provided is absolute or relative
if os.path.isabs(out_dir):
    pass
else:
    out_dir = os.path.join(os.getcwd(), out_dir)

# check whether out_dir already exists, if not make a new folder
if os.path.exists(out_dir):
    pass
else:
    os.mkdir(out_dir)

# create default validation out folder
out_dir = os.path.join(out_dir, '_validation_out')

# check whether out_dir already exists, if not make a new folder
if os.path.exists(out_dir):
    pass
else:
    os.mkdir(out_dir)

# provding plot names 
#TODO: make this more interactive and less hard-coded
new_var_name_obs = 'Qobs GRDC [m3/s]'
new_var_name_sim = 'Qsim PCR-GLOBWB [m3/s]'

# initiate logging
sys.stdout = open(os.path.join(out_dir, 'logfile.log'), 'w')

print(datetime.datetime.now())
print('')

print('get info from GRDC file', os.path.abspath(grdc_file))
print('')

# get GRDC station properties
grdc_plot_title, grdc_props = grdc_data.get_grdc_station_properties()
print('GRDC station properties are:')
print(grdc_props)
print('')

# get GRDC timeseries
df_grdc = grdc_data.get_grdc_station_values(var_name=new_var_name_obs,
                                            plot=False)

# go throuh all provided nc-files
#NOTE: tested with 1 file so far only
#TODO: think about how to do this with multiple nc-files
for file in ncfiles_list:

    if os.path.isabs(file):
        pass
    else:
        nc_file = os.path.join(os.getcwd(), file)

    print('reading from nc-file', os.path.abspath(nc_file))
    print('')

    row, col = pcrglobwb_utils.utils.find_indices_from_coords(nc_file, 
                                                              grdc_props['longitude'], 
                                                              grdc_props['latitude'])

    pcr_data = pcrglobwb_utils.sim_data.from_nc(nc_file)

    q_sim = pcr_data.read_values_at_indices(row,
                                            col,
                                            plot_var_name=new_var_name_sim)

    df_eval, eval_dic = pcr_data.validate_results(df_grdc,
                                                  out_dir,
                                                  new_var_name_obs,
                                                  new_var_name_sim,
                                                  plot=False,
                                                  save_fig=True)
    
    print('head of evaluated dataframe columns')
    print(df_eval.head())
    print('')
    
    print('timeseries validation results are:')
    print(eval_dic)

df_eval.to_csv(os.path.join(out_dir, 'dataframe.csv'), sep=';')

