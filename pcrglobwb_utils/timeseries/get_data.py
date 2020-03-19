import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import rasterio as rio
import spotpy as sp
import os, sys

def read_nc_file_at_indices(fo, idx_row, idx_col, var_name='discharge', plot=False, plot_var_name=None, plot_title=None):
    """
    reading a nc-file and retrieving variable values at given column and row indices.
    default setting is that discharge is extracted at this point.
    resulting timeseries is stored as pandas timeframe and can be plotted with user-specified variable name and title.
    
    input:
    ------
    fo {str} = georeferenced 2D nc-file
    idx_row {float} = row index
    idx_col {float} = column index
    var_name {str} = name of variable to be retrieved in nc-file (default: 'discharge')
    plot {bool} = True/False whether timeseries is plooted
    plot_var_name {str} = user-specified alternative name of variable in plot (default: None)
    plot_tile {str} = user-specified plot title (default: None)
    
    output:
    -------
    df {dataframe} = dataframe containing variable values per time step, i.e. alrady datetime as indices
    """
    
    # open file
    ds = xr.open_dataset(fo)
    
    # read variable values at indices as xarray DataArray
    dsq = ds[var_name].isel(lat=row, lon=col)
    
    # change variable names if specified
    if plot_var_name != None:
        var_name = plot_var_name
    
    # convert DataArray to pandas dataframe
    df = pd.DataFrame(data=dsq.to_pandas(), 
                  columns=[var_name])
    
    # plot if specified
    if plot == True:
        df.plot(title=plot_title)
    
    # close file
    ds.close()
    
    return df

def calc_montly_avg(df_in, var_name=None):
    """
    calculates the monthly averages of a time series.
    
    input:
    ------
    df_in {dataframe} = dataframe containing daily values
    var_name {str} = column header in df_in containing observed values. this is handy
                            if dataframe contains more than one column with values. if 'None',
                            it is assumed that only one column with values exists (default: None).
                            
    output:
    -------
    df_out {dataframe} = dataframe containing one column only with monthly average values.
    """
    
    # if variable name is not None, then pick values from specified column
    if var_name != None:
        df = df_in[var_name]
    # else, just use the dataframe as is
    else:
        df = df_in
    
    # group values by month and then calculate mean
    df_out = df.groupby(df.index.month).mean()
    
    return df_out