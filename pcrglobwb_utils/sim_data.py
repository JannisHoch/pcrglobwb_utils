import xarray as xr
import pandas as pd
import spotpy as sp
import numpy as np
import click
import os

from . import time_funcs

## OBJECT AND METHODS
class from_nc:
    """Retrieving and working with timeseries data from a nc-file.

    Arguments:
        fo (str): path to nc-file
    """

    def __init__(self, fo):
        """Initializing class.
        """

        self.ds = xr.open_dataset(fo, engine='netcdf4')

    def get_copy(self, verbose=False):

        if verbose: click.echo('VERBOSE -- returning copy of xarray dataset')

        cp = self.ds.copy()

        return cp

    def get_indices(self, lon, lat):

        ds = self.ds
        
        idx_row, idx_col = find_indices_from_coords(ds, lon, lat)

        return idx_row, idx_col
    
    def get_values(self, idx_row, idx_col, var_name='discharge', plot=False, plot_var_name=None, plot_title=None):
        
        ds = self.ds

        df = read_at_indices(ds, idx_row, idx_col, 
                             var_name=var_name, plot=plot, plot_var_name=plot_var_name, plot_title=plot_title)
        
        self.df = df

        return self.df

    def to_monthly(self, stat_func='mean'):
        """Resampling values to monthly time scale.

        Keyword Arguments:
            stat_func (str): statistical descriptor to be used in resampling . currently supported is 'mean', 'max', and 'min' (default: mean)

        Returns:
            dataframe: dataframe containing monthly values
        """        

        df = self.df

        df = time_funcs.resample_to_month(df, stat_func=stat_func)

        return self.df

    def to_annual(self, stat_func='mean'):
        """Resampling values to annual time scale.

        Keyword Arguments:
            stat_func (str): statistical descriptor to be used in resampling . currently supported is 'mean', 'max', and 'min' (default: mean)

        Returns:
            dataframe: dataframe containing monthly annual values
        """       

        df = self.df 

        df = time_funcs.resample_to_annual(df, stat_func=stat_func)
        
        return df

    def validate(self, df_obs, out_dir, suffix=None, var_name_obs=None, var_name_sim=None, return_all_KGE=False):

        df_sim = self.df

        df_out = validate_timeseries(df_sim, df_obs, out_dir, 
                                     suffix=suffix, var_name_obs=var_name_obs, var_name_sim=var_name_sim, return_all_KGE=return_all_KGE)
        
        return df_out

## FUNCTIONS ##

def find_indices_from_coords(ds, lon, lat):
    """[summary]

    Args:
        ds ([type]): [description]
        lon ([type]): [description]
        lat ([type]): [description]

    Returns:
        [type]: [description]
    """    

    try:
        abslat = np.abs(ds.lat-lat)
        abslon = np.abs(ds.lon-lon)
    except:
        abslat = np.abs(ds.latitude-lat)
        abslon = np.abs(ds.longitude-lon)

    c = np.maximum(abslon, abslat)

    try:
        ([idx_col], [idx_row]) = np.where(c == np.min(c))
    except:
        idxs = np.where(c == np.min(c))
        idx_col, idx_row = (np.min(idxs[0]), np.min(idxs[1]))

    return idx_row, idx_col

def read_at_indices(ds, idx_row, idx_col, var_name='discharge', plot=False, plot_var_name=None, plot_title=None):
    """Reading a nc-file and retrieving variable values at given column and row indices. Default setting is that discharge is extracted at this point. Resulting timeseries is stored as pandas timeframe and can be plotted with user-specified variable name and title.

    Arguments:
        idx_row (float): row index from which to read the data
        idx_col (float): column index from which to read the data

    Keyword Arguments:
        var_name (str): variable in nc-file whose data is to be read (default: 'discharge')
        plot (bool): whether or not to plot the timeseries (default: False)
        plot_var_name (str): user-specified name to be used for plot legend (default: None)
        plot_title (str): user-specified plot title (default: None)

    Returns:
        dataframe: dataframe containing values
    """

    # read variable values at indices as xarray DataArray
    try:
        dsq = ds[var_name].isel(lat=idx_row, lon=idx_col)
    except:
        dsq = ds[var_name].isel(latitude=idx_row, longitude=idx_col)
    
    # change variable names if specified
    if plot_var_name != None:
        var_name = plot_var_name
    
    # convert DataArray to pandas dataframe
    df = pd.DataFrame(data=dsq.to_pandas(), 
                columns=[var_name])
    
    # plot if specified
    if plot == True:
        df.plot(title=plot_title)

    if (pd.infer_freq(df.index) == 'M') or (pd.infer_freq(df.index) == 'MS'):
        print('changing index strftime to %Y-%m')
        df.index = df.index.strftime('%Y-%m')
    
    return df

def validate_timeseries(df_sim, df_obs, out_dir, suffix=None, var_name_obs=None, var_name_sim=None, return_all_KGE=False):
    """Validates simulated values with observations. Computes KGE, NSE, MSE, RMSE, RRMSE, and R2. Concatenates the two dataframes and drops all NaNs to achieve dataframe with common time period.

    Arguments:
        df_obs (dataframe): pandas dataframe containing observed values
        out_dir (str): user-specified output directory for validation output

    Keyword Arguments:
        suffix (str): suffix to be added at end of output files. Defaults to 'None'.
        var_name_obs (str): header name of column in df_obs whose values are to be used (default: None)
        var_name_sim (str): header name of column in df_sim whose values are to be used (default: None)
        return_all_KGE (bool): whether or not to return all KGE components (default: False)

    Raises:
        ValueError: if df_obs and df_sim do not overlap in time, an error is thrown.

    Returns:
        dataframes: dataframe containing scores.
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
    try:
        both = pd.concat([df_obs, df_sim], axis=1, join="inner", verify_integrity=True)
    except:
        click.echo('WARNING: concatenation did not succeed, now trying to resolve by removing duplicate indices.')
        df_obs = df_obs[~df_obs.index.duplicated(keep='first')]
        df_sim = df_sim[~df_sim.index.duplicated(keep='first')]
        both = pd.concat([df_obs, df_sim], axis=1, join="inner", verify_integrity=True)

    if suffix != None:
        both.to_csv(os.path.join(out_dir, 'evaluated_timeseries_{}.csv'.format(suffix)))
    else:
        both.to_csv(os.path.join(out_dir, 'evaluated_timeseries.csv'))

    # drop all entries where any of the dataframes contains NaNs
    # this yields a dataframe containing values only for common time period
    both_noMV = both.dropna()

    # raise error if there is no common time period
    if both.empty:
        click.echo('WARNING: no common time period of observed and simulated values found in dataframes!')
    
    # convert to np-arrays
    obs = both_noMV[both_noMV.columns[0]].to_numpy()
    sim = both_noMV[both_noMV.columns[1]].to_numpy()
    
    # apply objective functions
    kge = sp.objectivefunctions.kge(obs, sim, return_all=return_all_KGE)
    nse = sp.objectivefunctions.nashsutcliffe(obs, sim)
    mse = sp.objectivefunctions.mse(obs, sim)
    rmse = sp.objectivefunctions.rmse(obs, sim)
    rrmse = sp.objectivefunctions.rrmse(obs, sim)
    r2 = sp.objectivefunctions.rsquared(obs, sim)
    
    # fill dict
    evaluation = {'KGE': [kge],
                'NSE': nse,
                'MSE': mse,
                'RMSE': rmse,
                'RRMSE': rrmse,
                'R2': r2}

    # save dict to csv
    try:
        df_out = pd.DataFrame().from_dict(evaluation, orient='index')
    except:
        df_out = pd.DataFrame().from_dict(evaluation)

    if suffix != None:
        df_out.to_csv(os.path.join(out_dir, 'evaluation_{}.csv'.format(suffix)))
    else:
        df_out.to_csv(os.path.join(out_dir, 'evaluation.csv'))

    return df_out