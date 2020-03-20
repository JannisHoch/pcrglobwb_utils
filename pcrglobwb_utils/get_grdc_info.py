import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import rasterio as rio
import spotpy as sp
import os, sys

def get_grdc_station_properties(fo):
    """
    gets GRDC station properties from txt-file.
    creates and returns header from those properties as well as dictionary.
    
    input:
    -------
    fo {string} = path to txt-file
    
    output:
    -------
    plot_title {string} = header
    props {dict} = dictionary with GRDC station name, latitude, and longitude
    """
    
    # open file
    fp = open(fo)
    
    # go through lines in file
    for i, line in enumerate(fp):
        
        # station name normally in line 11 of GRDC file
        if i == 10:
            station_grdc = line
            # check whether line contains station information
            if 'Station'not in station_grdc.split(":")[0]:
                os.sys.exit('Station name should be in line 11 but not found - please check if input txt-file is original GRDC format!')
            # split and strip string
            station_grdc = station_grdc.split(":")[-1].strip()  
        
        # latitude normally in line 13 of GRDC file
        if i == 12:
            lat_grdc = line
            if 'Latitude'not in lat_grdc.split(":")[0]:
                os.sys.exit('Latitude should be in line 13 but not found - please check if input txt-file is original GRDC format!')
            lat_grdc = lat_grdc.split(":")[-1].strip()
            
        # longitude normally in line 14 of GRDC file
        elif i == 13:
            lon_grdc = line
            if 'Longitude'not in lon_grdc.split(":")[0]:
                os.sys.exit('Latitude should be in line 13 but not found - please check if input txt-file is original GRDC format!')
            lon_grdc = lon_grdc.split(":")[-1].strip()
            
        # break loop to save time    
        elif i > 13:
            break
            
    # close file        
    fp.close()
    
    # write station name, latitude, and longitude to dic
    props = dict(station=str(station_grdc), latitude=float(lat_grdc), longitude=float(lon_grdc))
    
    # create simple title for plots
    plot_title = 'station ' + str(station_grdc) + ' at latitude/longitude ' + str(lat_grdc) + '/' + str(lon_grdc)
    
    return plot_title, props


# In[4]:


def get_grdc_station_values(fo, var_name='GRDC discharge', remove_mv=True, mv_val=-999, print_head=False, plot=False, plot_title=None):
    """
    reads (discharge) values of GRDC station from txt-file.
    creates a pandas dataframe with a user-specified column header for values instead of default ' Values' header name.
    also possible to remove possible missing values in the timeseries and plot the resulting series.
    
    input:
    -------
    fo {string} = path to txt-file
    var_name {string} = user-specified column header name (default: 'GRDC discharge')
    remove_mv {bool} = True/False whether missing values should be removed (default: True)
    mv_val {int} = integer value corresponding to missing value in timeseries (default: -999)
    print_head {bool} = True/False whether df.head() is printed (default: False)
    plot {bool} = True/False whether dataframe should be plotted (default: False)
    plot_title {str} = title of dataframe plot (default: None)
    
    output:
    -------
    df {dataframe} = dataframe containing GRDC values per time step
    """
    
    #TODO: the number of rows to be skipped seem to change between files
    # appraoch: make it generic by scanning until lines do not start with # anymore
    df = pd.read_csv(fo, skiprows=35, sep=';')
        
    df[val_name] = df[' Value'].copy()
    del df[' Value']
    
    df['date'] = pd.to_datetime(df['YYYY-MM-DD'])
    df.set_index(df['date'], inplace=True)
    
    if remove_mv == True:
        df[val_name].replace(mv_val, np.nan, inplace=True)
    
    if print_head == True:
        print(df.head())
        
    if plot == True:
        df[val_name].plot(title=plot_title, legend=True)
    
    return df