import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import rasterio as rio
import spotpy as sp
import csv
import os, sys

class from_nc:
    """Retrieving and working with timeseries data from a nc-file.

    Arguments:
        fo (str): path to nc-file
    """

    def __init__(self, fo):
        """Initializing class.
        """

        self.ds = fo
    
    def read_values_at_indices(self, idx_row, idx_col, var_name='discharge', plot=False, plot_var_name=None, plot_title=None):
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

        # open file
        ds = xr.open_dataset(self.ds)
        
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
        
        # close file
        ds.close()

        self.df = df
        
        return self.df

    def resample2monthly(self, stat_func='mean', suffix='_monthly'):
        """Resampling values to monthly time scale.

        Keyword Arguments:
            stat_func (str): statistical descriptor to be used in resampling . currently supported is 'mean', 'max', and 'min' (default: mean)
            suffix (str): suffix to be added to column name (default: _monthly)

        Returns:
            dataframe: dataframe containing monthly average values
        """        

        if stat_func == 'mean':
            self.df_monthly = self.df.resample('M').mean()
        elif stat_func == 'max':
            self.df_monthly = self.df.resample('M').max()
        elif stat_func == 'min':
            self.df_monthly = self.df.resample('M').min()
        else:
            raise ValueError('no supported statistical function provided - choose between mean, max, and min')

        self.df_monthly = self.df_monthly.rename(columns={self.df_monthly.columns.values[0]: self.df_monthly.columns.values[0] + suffix + '_' + stat_func})

        return self.df_monthly

    def resample2yearly(self, stat_func='mean', suffix='_yearly'):
        """Resampling values to monthly time scale.

        Keyword Arguments:
            stat_func (str): statistical descriptor to be used in resampling . currently supported is 'mean', 'max', and 'min' (default: mean)
            suffix (str): suffix to be added to column name (default: _monthly)

        Returns:
            dataframe: dataframe containing monthly average values
        """        

        if stat_func == 'mean':
            self.df_yearly = self.df.resample('Y').mean()
        elif stat_func == 'max':
            self.df_yearly = self.df.resample('Y').max()
        elif stat_func == 'min':
            self.df_yearly = self.df.resample('Y').min()
        else:
            raise ValueError('no supported statistical function provided - choose between mean, max, and min')

        self.df_yearly = self.df_yearly.rename(columns={self.df_yearly.columns.values[0]: self.df_yearly.columns.values[0] + suffix + '_' + stat_func})

        return self.df_yearly

    def validate_results(self, df_obs, out_dir, var_name_obs=None, var_name_sim=None, return_all_KGE=False):
        """Validates simulated values with observations. Computes KGE, NSE, RMSE, and R^2. Concatenates the two dataframes and drops all NaNs to achieve dataframe with common time period.

        Arguments:
            df_obs (dataframe): pandas dataframe containing observed values
            out_dir (str): user-specified output directory for validation output

        Keyword Arguments:
            var_name_obs (str): header name of column in df_obs whose values are to be used (default: None)
            var_name_sim (str): header name of column in df_sim whose values are to be used (default: None)
            return_all_KGE (bool): whether or not to return all KGE components (default: False)

        Raises:
            error: if df_obs and df_sim do not overlap in time, an error is thrown.

        Returns:
            dataframe: pandas dataframe containing evaluated values for overlapping time period
            dict: dictionary containing results of objective functions KGE, RMSE, NSE and R2
        """ 

        # if variable name is not None, then pick values from specified column
        if var_name_obs != None:
            df_obs = df_obs[var_name_obs]
        # else, just use the dataframe as is
        else:
            df_obs = df_obs
            
        # idem  
        if var_name_sim != None:
            df_sim = self.df[var_name_sim]
        else:
            df_sim = self.df
        
        # concatenate both dataframes
        self.both = pd.concat([df_obs, df_sim], axis=1)
        # drop all entries where any of the dataframes contains NaNs
        # this yields a dataframe containing values only for common time period
        both_noMV = self.both.dropna()

        # raise error if there is no common time period
        if self.both.empty:
            os.sys.exit('no common time period of observed and simulated values found in dataframes!')
        
        # convert to np-arrays
        obs = both_noMV[both_noMV.columns[0]].to_numpy()
        sim = both_noMV[both_noMV.columns[1]].to_numpy()
        
        # apply objective functions
        kge = sp.objectivefunctions.kge(obs, sim, return_all=return_all_KGE)
        nse = sp.objectivefunctions.nashsutcliffe(obs, sim)
        rmse = sp.objectivefunctions.rmse(obs, sim)
        r2 = sp.objectivefunctions.rsquared(obs, sim)
        
        # fill dict
        evaluation = {'KGE': kge,
                    'NSE': nse,
                    'RMSE': rmse,
                    'R2': r2}

        # save dict to csv
        out_fo = os.path.join(out_dir, 'evaluation.csv')
        w = csv.writer(open(out_fo, "w"))
        for key, val in evaluation.items():
            w.writerow([key, val])
        
        return self.both, evaluation

    def calc_stats(self, out_dir, add_obs=False):
        """Calculates statistics for both observed and simulated timeseries using the pandas describe function.

        Keyword Arguments:
            plot (bool): whether or not to plot the histogram (default: False)

        Returns:
            dataframe: dataframe containing statistical values
        """        
        if not add_obs:
            stats = self.df.describe()
        if add_obs:
            stats = self.both.describe()

        # save dict to csv
        stats.to_csv(os.path.join(out_dir, 'stats.csv'))

        return stats