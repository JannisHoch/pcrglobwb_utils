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

        self.props = dict()
        
        # go through lines in file
        for i, line in enumerate(f):

            split_line = line.split(":")[0]

            if 'GRDC-No.' in split_line:
                grdc_no = line.split(":")[-1].strip()
                self.props['grdc_no'] = int(grdc_no)

            if 'Station' in split_line:
                station_grdc = line.split(":")[-1].strip()
                self.props['station'] = str(station_grdc)

            if 'Latitude' in split_line:
                lat_grdc = line.split(":")[-1].strip()
                self.props['latitude'] = float(lat_grdc)

            if 'Longitude' in split_line:
                lon_grdc = line.split(":")[-1].strip()
                self.props['longitude'] = float(lon_grdc)

            if 'Catchment area' in split_line:
                cat_area = line.split(":")[-1].strip()
                if cat_area == '':
                    cat_area = 0.0
                self.props['cat_area'] = float(cat_area)

            if 'Time series' in split_line:
                ts_time = line.split(":")[-1].strip()
                ts_start = ts_time.split(" - ")[0].strip()
                ts_end = ts_time.split(" - ")[1].strip()
                self.props['ts_start'] = pd.to_datetime(ts_start)
                self.props['ts_end'] = pd.to_datetime(ts_end)

            if 'No. of years' in split_line:
                no_years = line.split(":")[-1].strip()
                self.props['no_years'] = int(no_years)

            # break loop to save time and not read all observed values   
            if i > 25:
                break
                
        # close file        
        f.close()

        if 'grdc_no' not in self.props.keys(): warnings.warn('WARNING -- no "GRDC-No." information found in file.')
        if 'station' not in self.props.keys(): warnings.warn('WARNING -- no "Station" information found in file.')
        if 'latitude' not in self.props.keys(): warnings.warn('WARNING -- no "Latitude" information found in file.')
        if 'longitude' not in self.props.keys(): warnings.warn('WARNING -- no "Longitude" information found in file.')
        if 'cat_area' not in self.props.keys(): warnings.warn('WARNING -- no "Catchment area" information found in file.')
        if 'ts_start' not in self.props.keys(): warnings.warn('WARNING -- no start date of timeseries found in file.')
        if 'ts_end' not in self.props.keys(): warnings.warn('WARNING -- no end date of timeseries found in file.')
        if 'no_years' not in self.props.keys(): warnings.warn('WARNING -- no "No. of years" information found in file.')
        
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