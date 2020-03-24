# -*- coding: utf-8 -*-

import pcrglobwb_utils
import matplotlib.pyplot as plt
import datetime
import pandas as pd
import os, sys

#TODO: create something like that with click

# parsing arguments and checking whether provided paths are absolute or relative
ncfiles_list = sys.argv[1:-3] # list of nc-files to be evaluated

lon = float(sys.argv[-3]) #lon/lat
lat = float(sys.argv[-2])

out_dir = str(sys.argv[-1]) # path to output_dir
if os.path.isabs(out_dir):
    pass
else:
    out_dir = os.path.join(os.getcwd(), out_dir)

# check whether out_dir already exists, if not make a new folder
if os.path.exists(out_dir):
    pass
else:
    os.mkdir(out_dir)

# initiate logging
sys.stdout = open(os.path.join(out_dir, 'logfile.log'), 'w')

print(datetime.datetime.now())
print('')

df_out = pd.DataFrame()

# go throuh all provided nc-files
for i, file in enumerate(ncfiles_list):

    # loop through provided filenames and check whether path is absolute or relative
    if os.path.isabs(ncfiles_list[i]):
        pass
    else:
        nc_file = os.path.join(os.getcwd(), file)

    print('reading from nc-file', os.path.abspath(nc_file))
    print('')

    # get row/col from lon/lat
    row, col = pcrglobwb_utils.utils.find_indices_from_coords(nc_file, lon, lat)
    
    # extract information at a certain row/col
    q_sim = pcrglobwb_utils.timeseries.read_nc_file_at_indices(nc_file, 
                                                               row, 
                                                               col, 
                                                               plot_var_name='discharge'+str(i+1))

    # concatenate all extracted timeseries to one output dataframe
    df_out = pd.concat([df_out, q_sim], axis=1)
    df_out = df_out.dropna()

# save output dataframe to csv
df_out.to_csv(os.path.join(out_dir, 'dataframe.csv'), sep=';')

# plot timeseries and save to file
df_out.plot()
plt.savefig(os.path.join(out_dir, 'benchmark.png'), dpi=300)
    

