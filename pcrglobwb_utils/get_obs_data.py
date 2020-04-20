# -*- coding: utf-8 -*-

import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import rasterio as rio
import spotpy as sp
import os, sys

class grdc_data:
    """class to retrieve, re-work and visualize data from a GRDC-file.
    
    Returns:
        {object} -- python object of GRDC data source
    """

    def __init__(self, fo):
        """initiates grdc_data class.
        
        Arguments:
            fo {str} -- path to GRDC file
        """

        self.fo = fo

    def get_grdc_station_properties(self):
        """Retrieves GRDC station properties from txt-file. Creates and returns header from those properties as well as a dictionary containt station name, lat, and lon info.
        
        Returns:
            str -- plot title containing station name and lat/lon info
            dict -- dictionary containing name, lat, and lon info
        """
        
        # open file
        fp = open(self.fo)
        
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

    def get_grdc_station_values(self, var_name, remove_mv=True, mv_val=-999, print_head=False, plot=False, plot_title=None):
        """Reads (discharge-)values of GRDC station from txt-file. Creates a pandas dataframe with a user-specified column header for values instead of default ' Values' header name. Also possible to remove possible missing values in the timeseries and plot the resulting series.
        
        Arguments:
            var_name {str} -- user-specified variable name to be given to time series
        
        Keyword Arguments:
            remove_mv {bool} -- whether or not remove missing values in timeseries (default: {True})
            mv_val {int} -- missing value in timeseries (default: {-999})
            print_head {bool} -- whether or not to print the pandas dataframe head (default: {False})
            plot {bool} -- whether or not to plot the timeseries (default: {False})
            plot_title {str} -- user-specified title for plot of timeseries (default: {None})
        
        Returns:
            {dataframe} -- dataframe containing datetime objects as index and observations as column values
        """

        f = open(self.fo)

        for i, line in enumerate(f):
            if '#' in line:
                pass
            else:
                stopline = i
                break

        df = pd.read_csv(self.fo, skiprows=stopline, sep=';')
            
        df[var_name] = df[' Original'].copy()
        del df[' Original']
        
        df['date'] = pd.to_datetime(df['YYYY-MM-DD'])
        df.set_index(df['date'], inplace=True)

        df_out = pd.DataFrame(index=df.index,
                            data=df[var_name])
        
        if remove_mv == True:
            df_out.replace(mv_val, np.nan, inplace=True)
        
        if print_head == True:
            print(df_out.head())
            
        if plot == True:
            df_out.plot(title=plot_title, legend=True)
        
        return df_out

class other_data:
    """class to retrieve, re-work and visualize data from other data sources than GRDC files.
    
    Returns:
        {object} -- python object of data source
    """

    def __init__(self, fo):
        """Initializing class.
        
        Arguments:
            fo {str} -- path to other data source
        """

        self.fo = fo

    def get_values_from_csv(self, t_col, v_col, sep=';', datetime_format='%Y-%m-%d', remove_mv=True, mv_val=-999, print_head=False, plot=False, plot_title=None):
        """Reads simple csv file containing of multiple columns with at least one containing time information, and returns dataframe for dates and selected column.
        
        Arguments:
            t_col {str} -- header of column containing time information
            v_col {str} -- header of column containing values
            sep {str} -- column separator (default: {';'})
        
        Keyword Arguments:
            datetime_format {str} -- datetime format used in csv file (default: {'%Y-%m-%d'})
            remove_mv {bool} -- whether or not to remove missing values (default: {True})
            mv_val {float} -- placeholder value of missing values (default: {-999})
            print_head {bool} -- whether or not to print the header of dataframe (default: {False})
            plot {bool} -- whether or not to plot the timeseries (default: {False})
            plot_title {str} -- optional title for plot (default: {None})
        
        Returns:
            {dataframe} -- dataframe containing datetime objects as index and observations as column values
        """
        
        df = pd.read_csv(self.fo, sep=sep)
        
        df.set_index(pd.to_datetime(df[t_col], format=datetime_format), inplace=True)

        if remove_mv == True:
            df.replace(mv_val, np.nan, inplace=True)
        
        del df[t_col]
            
        if print_head == True:
            print(df.head())
            
        if plot == True:
            df[v_col].plot(title=plot_title, legend=True)
        
        return df