import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import rasterio as rio
import spotpy as sp
import csv
import os, sys

class ensemble_data():
    """Analyzing and visualizing ensemble time series.

    Arguments:
        *arg: list of pandas dataframe with matching datetime index
    """

    def __init__(self, *arg):
        """Creates object based on an ensemble of input dataframes.
        """        

        temp = []
        for argument in arg:
            temp.append(argument)
        
        self.df_ens = pd.concat(temp, axis=1)

    def calc_stats(self):
        """Calculates mean, max, and min from ensemble object.

        Returns:
            dataframe: dataframe containing the input dataframes as well as columsn with mean, max, and min
        """        

        self.df_stats = self.df_ens.copy()

        self.df_stats['mean'] = self.df_stats.mean(axis=1)
        self.df_stats['max'] = self.df_stats.max(axis=1)
        self.df_stats['min'] = self.df_stats.min(axis=1)

        return self.df_stats

    def plot_bounds(self, **kwargs):   
        """Plots the mean, max, and min columns of the time series to visualize the range of values.

        Keyword Arguments:
            **kwargs: additional keyword arguments for plotting
        """          

        figsize = kwargs.get('figsize', (20,10))
        title = kwargs.get('title', 'Ensemble plot')

        fig, ax = plt.subplots(1, 1)
        self.df_stats['mean'].plot(figsize=figsize,
                                   color='r',
                                   legend=True,
                                   ax=ax)
        self.df_stats['max'].plot(ax=ax,
                                  color='r',
                                  style=':',
                                  alpha=0.5)
        self.df_stats['min'].plot(ax=ax,
                                  color='r',
                                  style=':',
                                  alpha=0.5)
        ax.set_title(title)
        ax.set_xlabel(None)
        ax.set_ylabel('discharge [m3/s]')

        return

    def climatology(self, plot=False, **kwargs):
        """Calculates the long-term average per month as well as mean, max, and min thereof.

        Keyword Arguments:
            plot (bool): whether or not to plot mean, max, min (default: False)

        Returns:
            dataframe: dataframe containing the long-term monthly averages as well as their mean, max, and min
        """        

        figsize = kwargs.get('figsize', (20,10))
        title = kwargs.get('title', 'Climatology')

        df_out = self.df_ens.groupby(self.df_ens.index.month).mean()
        df_out['mean'] = df_out.mean(axis=1)
        df_out['max'] = df_out.max(axis=1)
        df_out['min'] = df_out.min(axis=1)

        if plot:

            ax = df_out['mean'].plot(figsize=figsize,
                                            color='r',
                                            legend=True)
            df_out['max'].plot(ax=ax,
                                    color='r',
                                    style=':',
                                    alpha=0.5)
            df_out['min'].plot(ax=ax,
                                    color='r',
                                    style=':',
                                    alpha=0.5)
            ax.set_title(title)
            ax.set_xlabel('month')
            ax.set_ylabel('discharge [m3/s]')

        return df_out
