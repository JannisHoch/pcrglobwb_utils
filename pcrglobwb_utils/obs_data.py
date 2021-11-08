# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import warnings
import os

class grdc_data:
    """Retrieve, re-work and visualize data from a GRDC-file.

    Arguments:
        fo (str): path to file with GRDC data
    """

    def __init__(self, fo):
        """Initiates grdc_data object.
        """

        self.fo = fo
        
    def get_grdc_station_properties(self, encoding='ISO-8859-1'):
        """Retrieves GRDC station properties from txt-file. Creates and returns header from those properties as well as a dictionary containt station name, lat, and lon info.

        Returns:
            str: plot title containing station name and lat/lon info
            dict: dictionary containing name, lat, and lon info
        """
        
        # open file
        f = open(self.fo, encoding=encoding)
        
        # go through lines in file
        for i, line in enumerate(f):

            # GRDC-No normally in line 9 of GRDC file
            if i == 8:
                grdc_no = line
                # check whether line contains station information
                if 'GRDC-No.' not in grdc_no.split(":")[0]:
                    warnings.warn('WARNING: GRDC-No. should be in line 9 but not found - please check if input txt-file is original GRDC format!')
                # split and strip string
                grdc_no = grdc_no.split(":")[-1].strip()  
            
            # station name normally in line 11 of GRDC file
            if i == 10:
                station_grdc = line
                # check whether line contains station information
                if 'Station' not in station_grdc.split(":")[0]:
                    warnings.warn('WARNING: Station name should be in line 11 but not found - please check if input txt-file is original GRDC format!')
                # split and strip string
                station_grdc = station_grdc.split(":")[-1].strip()  
            
            # latitude normally in line 13 of GRDC file
            if i == 12:
                lat_grdc = line
                if 'Latitude'not in lat_grdc.split(":")[0]:
                    warnings.warn('WARNING: Latitude should be in line 13 but not found - please check if input txt-file is original GRDC format!')
                lat_grdc = lat_grdc.split(":")[-1].strip()
                
            # longitude normally in line 14 of GRDC file
            if i == 13:
                lon_grdc = line
                if 'Longitude' not in lon_grdc.split(":")[0]:
                    warnings.warn('WARNING: Longitude should be in line 14 but not found - please check if input txt-file is original GRDC format!')
                lon_grdc = lon_grdc.split(":")[-1].strip()

            # catchment area normally in line 15 of GRDC file
            if i == 14:
                cat_area = line
                if 'Catchment area (km2)' not in cat_area.split(":")[0]:
                    warnings.warn('WARNING: Catchment area should be in line 15 but not found - please check if input txt-file is original GRDC format!')
                cat_area = cat_area.split(":")[-1].strip()
                if cat_area == '':
                    cat_area = 0.0

           # start and end year of observations normally in line 15 of GRDC file
            if i == 24:
                ts_time = line
                if 'Time series' not in ts_time.split(":")[0]:
                    warnings.warn('WARNING: Time series should be in line 25 but not found - please check if input txt-file is original GRDC format!')
                ts_time = ts_time.split(":")[-1].strip()
                ts_start = ts_time.split(" - ")[0].strip()
                ts_end = ts_time.split(" - ")[1].strip()
    
            # No. of years normally in line 26 of GRDC file
            if i == 25:
                no_years = line
                if 'No. of years' not in no_years.split(":")[0]:
                    warnings.warn('WARNING: No. of years should be in line 26 but not found - please check if input txt-file is original GRDC format!')
                no_years = no_years.split(":")[-1].strip()
                
            # break loop to save time    
            elif i > 25:
                break
                
        # close file        
        f.close()
        
        # write station name, latitude, and longitude to dic
        self.props = dict(grdc_no=int(grdc_no),
                          station=str(station_grdc), 
                          latitude=float(lat_grdc), 
                          longitude=float(lon_grdc),
                          cat_area=float(cat_area),
                          no_years=int(no_years),
                          ts_start=pd.to_datetime(ts_start),
                          ts_end=pd.to_datetime(ts_end))
        
        # create simple title for plots
        plot_title = 'station ' + str(station_grdc) + ' at latitude/longitude ' + str(lat_grdc) + '/' + str(lon_grdc)

        return plot_title, self.props

    def get_grdc_station_values(self, var_name, col_name=' Value', remove_mv=True, mv_val=-999, encoding='ISO-8859-1', verbose=False):
        """Reads (discharge-)values of GRDC station from txt-file. Creates a pandas dataframe with a user-specified column header for values instead of default ' Values' header name. Also possible to remove possible missing values in the timeseries and plot the resulting series.

        Arguments:
            var_name (str): user-specified variable name to be given to time series

        Keyword Arguments:
            col_name (str): name of column in GRDC-file to be read. Defaults to ' Value'.
            remove_mv (bool): whether or not remove missing values in timeseries (default: True).
            mv_val (int): missing value in timeseries (default: -999).
            verbose (bool): verbose mode on or off. Defaults to False.

        Returns:
            dataframe: dataframe containing datetime objects as index and observations as column values
        """

        #TODO: this function should also work if get_grdc_station_properties() was not executed before;
        #TODO: because, if not executed before, self.props is no attribute yet and function exists with error

        # open file
        f = open(self.fo, encoding=encoding)

        # find line in file in which meta-data starts and observational record starts
        for i, line in enumerate(f):
            if '#' in line:
                pass
            else:
                stopline = i
                break

        df = pd.read_csv(self.fo, skiprows=stopline, sep=';', encoding=encoding)

        try: 
            if verbose: print('VERBOSE -- reading column {}'.format(col_name))
            df[var_name] = df[str(col_name)].copy()
            del df[str(col_name)]
        except:
            if col_name == ' Value':
                raise ValueError('ERROR: column "{}" - which is also the fall back option - cannot be found in file {}'.format(col_name, self.fo))
            else:
                warnings.warn('WARNING: column {} not found, falling back to column Value'.format(col_name))
                df[var_name] = df[' Value'].copy()
                del df[' Value']

        df['date'] = pd.to_datetime(df['YYYY-MM-DD'])
        df.set_index(df['date'], inplace=True)

        df_out = pd.DataFrame(index=df.index,
                            data=df[var_name])
        
        if remove_mv == True:
            df_out.replace(mv_val, np.nan, inplace=True)

        if (pd.infer_freq(df_out.index) == 'M') or (pd.infer_freq(df_out.index) == 'MS'):
            # if verbose: print('changing index strftime to %Y-%m')
            df_out.index = df_out.index.strftime('%Y-%m')

        self.df = df_out

        # self.props['start_data_obs'] = self.df.index.strftime('%m/%d/%Y').values[0]
        # self.props['end_data_obs'] = self.df.index.strftime('%m/%d/%Y').values[-1]

        return self.df, self.props
        
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

    """Retrieve, re-work and visualize data from other data sources than GRDC files

    Arguments:
        fo (str): path to text file containing data
    """

    def __init__(self, fo):
        """Initializing class.
        """        

        self.fo = fo

    def get_values_from_csv(self, var_name, remove_mv=True, mv_val=-999, print_head=False, plot=False, plot_title=None):
        """Reads simple two-column csv file and returns dataframe for dates and selected column.

        Arguments:
            var_name (str): user-specified column name

        Keyword Arguments:
            remove_mv (bool): whether or not to remove missing values (default: True)
            mv_val (int): placeholder value of missing values (default: -999)
            print_head (bool): whether or not to print the header of dataframe (default: False)
            plot (bool): whether or not to plot the timeseries (default: False)
            plot_title (str): optional title for plot (default: None)

        Returns:
            dataframe: dataframe containing datetime objects as index and observations as column values
        """
        
        df = pd.read_csv(self.fo, sep=None, engine='python', parse_dates=[0], index_col=0)

        df = df.rename(columns={df.columns.values[0]: var_name})

        if remove_mv == True:
            df.replace(mv_val, np.nan, inplace=True)
            
        if print_head == True:
            print(df.head())
            
        if plot == True:
            df.plot(title=plot_title, legend=True)
        
        self.df = df

        return self.df

    def get_values_from_excel(self, var_name, remove_mv=True, mv_val=-999, plot=False, plot_title=None):

        df = pd.read_excel(self.fo, index_col=0)

        df = df.rename(columns={df.columns.values[0]: var_name})

        if remove_mv == True:
            df.replace(mv_val, np.nan, inplace=True)

        if plot == True:
            df.plot(title=plot_title, legend=True)

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