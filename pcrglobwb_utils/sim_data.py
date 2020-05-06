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
    """

    def __init__(self, fo):
        """Initializing class.

        Arguments:
            fo (str): path to nc-file
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

    def validate_results(self, df_obs, out_dir, var_name_obs=None, var_name_sim=None, plot=False, save_fig=True):
        """Validates simulated values with observations. Computes KGE, NSE, RMSE, and R^2. Concatenates the two dataframes and drops all NaNs to achieve dataframe with common time period.

        Arguments:
            df_obs (dataframe): pandas dataframe containing observed values
            out_dir (str): user-specified output directory for validation output

        Keyword Arguments:
            var_name_obs (str): header name of column in df_obs whose values are to be used (default: None)
            var_name_sim (str): header name of column in df_sim whose values are to be used (default: None)
            plot (bool): whether or not to show the figure (default: False)
            save_fig (bool): whether or not to save the figure (default: True)

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
        both = pd.concat([df_obs, df_sim], axis=1)
        # drop all entries where any of the dataframes contains NaNs
        # this yields a dataframe containing values only for common time period
        both = both.dropna()
        
        # raise error if there is no common time period
        if both.empty:
            os.sys.exit('no common time period of observed and simulated values found in dataframes!')

        if save_fig == True:
            if os.path.isdir(out_dir) == True:
                pass
            else:
                os.mkdir(out_dir)
        
        # plot if specified
        if plot == True:
            both.plot()
            plt.show()
            if save_fig == True:
                plt.savefig(os.path.join(out_dir, 'evaluated_timeseries.png'), dpi=300)
        if save_fig == True:
            both.plot()
            plt.savefig(os.path.join(out_dir, 'evaluated_timeseries.png'), dpi=300)
        
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

        # save dict to csv
        out_fo = os.path.join(out_dir, 'evaluation.csv')
        w = csv.writer(open(out_fo, "w"))
        for key, val in evaluation.items():
            w.writerow([key, val])
        
        return both, evaluation

    def calc_stats(self, plot=False):
        """Calculates statistics for nc-data object.

        Keyword Arguments:
            plot (bool): whether or not to plot the histogram (default: False)

        Returns:
            dict: dictionary containing statistical values
        """        

        stats = {'mean': int(self.df.mean()),
                 'median': int(self.df.median()),
                 'max': int(self.df.max()),
                 'min': int(self.df.min()),
                 'q10': int(self.df.quantile(q=0.1)),
                 'q50': int(self.df.quantile(q=0.5)),
                 'q90': int(self.df.quantile(q=0.9))}

        if plot: self.df.plot.hist()

        return stats

class ensembles():

    def __init__(self, dfs):     

        self.df = pd.concat([dfs], axis=1)

    def calc_stats(self):

        self.df_stats = self.df.copy()

        self.df_stats['mean'] = self.df_stats.mean()
        self.df_stats['max'] = self.df_stats.max()
        self.df_stats['min'] = self.df_stats.min()

        return self.df_stats

    def plot_bounds(self, **kwargs):     

        figsize = kwargs.get('figsize', (20,10))

        ax = self.df_stats['mean'].plot(figsize=figsize,
                                        color='r',
                                        legend=True)
        self.df_stats['max'].plot(ax=ax,
                                  color='r',
                                  style=':',
                                  alpha=0.5)
        self.df_stats['min'].plot(ax=ax,
                                  color='r',
                                  style=':',
                                  alpha=0.5)

    def plot_monthly_avgs(self):

        pass
