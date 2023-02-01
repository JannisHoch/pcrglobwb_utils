# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import warnings

from . import time_funcs

class grdc_data:
    """Retrieve, re-work and visualize data from a GRDC-file.

    Args:
        fo (str): path to file with GRDC data
    """

    def __init__(self, fo):
        """Initiates grdc_data object.
        """

        self.fo = fo
        
    def get_grdc_station_properties(self, encoding='ISO-8859-1') -> dict:
        """Retrieves GRDC station properties from txt-file. Creates and returns header from those properties as well as a dictionary containt station name, lat, and lon info.

        Args:
            encoding (str, optional): encoding of GDRC files. Defaults to 'ISO-8859-1'.

        Returns:
            dict: dictionary containing properties.
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

        return self.props

    def get_grdc_station_values(self, var_name=None, col_name=' Value', remove_mv=True, mv_val=-999, encoding='ISO-8859-1', verbose=False) -> pd.DataFrame:
        """Reads (discharge-)values of GRDC station from txt-file and returns them as dataframe. 
        Creates a pandas dataframe with a user-specified column header for values instead of default ' Values' header name. 
        Possible to remove possible missing values in the timeseries and plot the resulting series.

        Args:
            var_name (str): user-specified variable name to be given to column. If None, col_name is used. Default to 'None'.
            col_name (str, optional): name of column in GRDC-file to be read. Defaults to ' Value'.
            remove_mv (bool, optional): whether or not remove missing values in timeseries. Defaults to True.
            mv_val (int, optional): missing value in timeseries. Defaults to -999.
            encoding (str, optional): encoding of GDRC files. Defaults to 'ISO-8859-1'.
            verbose (bool, optional): whether or not to show more info. Defaults to False.

        Returns:
            pd.DataFrame: dataframe containing observational data.
        """

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

        # if var_name is specified, use it
        if var_name != None:
            var_name = var_name
        else:
            var_name = str(col_name)

        try: 
            if verbose: print('VERBOSE -- reading column {}'.format(col_name))
            df[var_name] = df[str(col_name)].copy()
            # del df[str(col_name)]
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

        return self.df 
        
    def to_monthly(self, stat_func='mean', suffix=None) -> pd.DataFrame:
        """Resampling values to monthly time scale.

        Args:
            stat_func (str, optional): statistical descriptor to be used in resampling. Currently supported is 'mean', 'max', and 'min'. Defaults to 'mean'.
            suffix (str, optional): suffix to be added to column name. Defaults to None.

        Returns:
            pd.DataFrame: dataframe containing monthly average values
        """
     
        df = self.df

        df = time_funcs.resample_to_month(df, stat_func=stat_func, suffix=suffix)

        return df

    def to_annual(self, stat_func='mean', suffix=None) -> pd.DataFrame:
        """Resampling values to annual time scale.

        Args:
            stat_func (str, optional): statistical descriptor to be used in resampling. Currently supported is 'mean', 'max', and 'min'. Defaults to 'mean'.
            suffix (str, optional): suffix to be added to column name. Defaults to None.

        Returns:
            pd.DataFrame: dataframe containing annual average values
        """      

        df = self.df 

        df = time_funcs.resample_to_annual(df, stat_func=stat_func, suffix=suffix)
        
        return df

class other_data:

    """Retrieve, re-work and visualize data from other data sources than GRDC files

    Arguments:
        fo (str): path to text file containing data
    """

    def __init__(self, fo):
        """Initializing class.
        """        

        self.fo = fo

    def get_values_from_csv(self, var_name=None, remove_mv=True, mv_val=-999) -> pd.DataFrame:
        """Reads simple two-column csv file and returns dataframe for dates and selected column.

        Args:
            var_name (str, optional): _description_. Defaults to None.
            remove_mv (bool, optional): whether or not to remove missing values. Defaults to True.
            mv_val (int, optional): placeholder value of missing values. Defaults to -999.

        Returns:
            pd.DataFrame: _description_
        """
        
        df = pd.read_csv(self.fo, sep=None, engine='python', parse_dates=[0], index_col=0)

        if var_name != None:
            df = df.rename(columns={df.columns.values[0]: var_name})

        if remove_mv == True:
            df.replace(mv_val, np.nan, inplace=True)
        
        self.df = df

        return self.df

    def get_values_from_excel(self, var_name=None, remove_mv=True, mv_val=-999) -> pd.DataFrame:
        """Retrieves observational values from an Excel file.
        The file should have two columns: one with timestamps, the second with values.
        The second column should ideally have a meaningful name, if not it can be set with 'var_name'.

        Args:
            var_name (str, optional): user-specified variable name to be given to column. If None, use name in Excel sheet. Defaults to None.
            remove_mv (bool, optional): whether or not remove missing values in timeseries. Defaults to True.
            mv_val (int, optional): missing value in timeseries. Defaults to -999.

        Returns:
            pd.DataFrame: dataframe containing observational values.
        """

        df = pd.read_excel(self.fo, index_col=0)

        if var_name != None:
            df = df.rename(columns={df.columns.values[0]: var_name})

        if remove_mv == True:
            df.replace(mv_val, np.nan, inplace=True)

        self.df = df

        return self.df

    def to_monthly(self, stat_func='mean', suffix=None) -> pd.DataFrame:
        """Resampling values to monthly time scale.

        Args:
            stat_func (str, optional): statistical descriptor to be used in resampling. Currently supported is 'mean', 'max', and 'min'. Defaults to 'mean'.
            suffix (str, optional): suffix to be added to column name. Defaults to None.

        Returns:
            pd.DataFrame: dataframe containing monthly average values
        """
        
        df = self.df

        df = time_funcs.resample_to_month(df, stat_func=stat_func, suffix=suffix)

        return df

    def to_annual(self, stat_func='mean', suffix=None) -> pd.DataFrame:
        """Resampling values to annual time scale.

        Args:
            stat_func (str, optional): statistical descriptor to be used in resampling. Currently supported is 'mean', 'max', and 'min'. Defaults to 'mean'.
            suffix (str, optional): suffix to be added to column name. Defaults to None.

        Returns:
            pd.DataFrame: dataframe containing annual average values
        """      

        df = self.df 

        df = time_funcs.resample_to_annual(df, stat_func=stat_func, suffix=suffix)
        
        return df