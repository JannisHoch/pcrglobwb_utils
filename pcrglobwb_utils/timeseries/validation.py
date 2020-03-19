import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import rasterio as rio
import spotpy as sp
import os, sys

def validate_results(df_obs, df_sim, var_name_obs=None, var_name_sim=None, plot=False):
    """
    validates observed and simulated values in a timeseries. 
    computes KGE, NSE, RMSE, and R^2.
    concatenates the two dataframes and drops all NaNs to achieve dataframe with common
    time period.
    
    input:
    ------
    df_obs {dataframe} = dataframe containing observed values
    df_sim {dataframe} = dataframe containing simulated values
    var_name_obs {str} = column header in df_obs containing observed values. this is handy
                            if dataframe contains more than one column with values. if 'None',
                            it is assumed that only one column with values exists (default: None).
    var_name_sim {str} = column header in df_sim containing simulated values. this is handy
                            if dataframe contains more than one column with values. if 'None',
                            it is assumed that only one column with values exists (default: None).
    plot {bool} = True/False whether data of common time period is plotted (default: False)
    
    output:
    -------
    evaluation {dict} = dictionary containing computed values per objective function    
    
    """
    
    # if variable name is not None, then pick values from specified column
    if var_name_obs != None:
        df_obs = df_obs[var_name_obs]
    # else, just use the dataframe as is
    else:
        df_obs = df_obs
        
    # idem  
    if var_name_sim != None:
        df_sim = df_sim[var_name_sim]
    else:
        df_sim = df_sim
    
    # concatenate both dataframes
    both = pd.concat([df_obs, df_sim], axis=1)
    # drop all entries where any of the dataframes contains NaNs
    # this yields a dataframe containing values only for common time period
    both = both.dropna()
    
    # raise error if there is no common time period
    if both.empty:
        os.sys.exit('no common time period of observed and simulated values found in dataframes!')
    
    # plot if specified
    if plot == True:
        both.plot()
    
    # convert to np-arrays
    obs = both[both.columns[0]].to_numpy()
    sim = both[both.columns[1]].to_numpy()
    
    # apply objective functions
    kge = sp.objectivefunctions.kge(obs, sim)
    nse = sp.objectivefunctions.nashsutcliffe(obs, sim)
    rmse = sp.objectivefunctions.rmse(obs, sim)
    r2 = sp.objectivefunctions.rsquared(obs, sim)
    
    # fill dict
    evaluation = {'KGE': kge,
                  'NSE': nse,
                  'RMSE': rmse,
                  'R2': r2}
    
    return evaluation