# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import warnings
import os
import click

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
            if verbose: click.echo('VERBOSE -- reading column {}'.format(col_name))
            df[var_name] = df[str(col_name)].copy()

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

class gsim_data:
    """Retrieve, re-work and visualize data from a GSIM-file.

    Args:
        fo (str): path to file with GSIM data
    """

    def __init__(self, fo):
        """Initiates grdc_data object.
        """

        self.fo = fo

    def get_gsim_station_properties(self) -> dict:
        """Retrieves GSIM station properties from txt-file. 
        Creates and returns header from those properties as well as a dictionary containt station name, lat, and lon info.

        Returns:
            dict: dictionary containing properties.
        """

        # open file
        f = open(self.fo)

        self.props = dict()
        
        # go through lines in file
        for i, line in enumerate(f):

            split_line = line.split(":")[0]

            if 'gsim.no' in split_line:
                gsim_no = line.split(":")[-2].strip()
                self.props['gsim_no'] = gsim_no

            if 'station' in split_line:
                station_gsim = line.split(":")[-2].strip()
                self.props['station'] = station_gsim

            if 'latitude' in split_line:
                lat_gsim = line.split(":")[-2].strip()
                self.props['latitude'] = float(lat_gsim)

            if 'longitude' in split_line:
                lon_gsim = line.split(":")[-2].strip()
                self.props['longitude'] = float(lon_gsim)

            if 'area' in split_line:
                cat_area = line.split(":")[-2].strip()
                if cat_area == '':
                    cat_area = 'N/A'
                self.props['cat_area'] = cat_area

            if 'altitude' in split_line:
                alt_gsim = line.split(":")[-2].strip()
                try:                
                    self.props['altitude'] = float(alt_gsim)
                except:
                    self.props['altitude'] = np.nan

            if 'river' in split_line:
                river = line.split(":")[-2].strip()
                self.props['river'] = river

            # break loop to save time and not read all observed values   
            if i > 20:
                break
                
        # close file        
        f.close()

        if 'gsim_no' not in self.props.keys(): warnings.warn('WARNING -- no "gsim.no" information found in file {}.'.format(os.path.abspath(self.fo)))
        if 'station' not in self.props.keys(): warnings.warn('WARNING -- no "station" information found in file {}.'.format(os.path.abspath(self.fo)))
        if 'latitude' not in self.props.keys(): warnings.warn('WARNING -- no "latitude" information found in file {}.'.format(os.path.abspath(self.fo)))
        if 'longitude' not in self.props.keys(): warnings.warn('WARNING -- no "longitude" information found in file {}.'.format(os.path.abspath(self.fo)))
        if 'cat_area' not in self.props.keys(): warnings.warn('WARNING -- no "area" information found in file {}.'.format(os.path.abspath(self.fo)))
        if 'altitude' not in self.props.keys(): warnings.warn('WARNING -- no "altitude" information found in file {}.'.format(os.path.abspath(self.fo)))
        if 'river' not in self.props.keys(): warnings.warn('WARNING -- no "river" information found in file {}.'.format(os.path.abspath(self.fo)))

        return self.props

    def get_gsim_station_values(self, var_name='GSIM', col_name='"MEAN"', remove_mv=True, mv_val=-999, verbose=False) -> tuple[pd.DataFrame, dict]:
        """Reads (discharge-)values of GSIM station from txt-file and returns them as dataframe. 
        Creates a pandas dataframe with a user-specified column header for values instead of default ' Values' header name. 
        Possible to remove possible missing values in the timeseries and plot the resulting series.

        Args:
            var_name (str): user-specified variable name to be given to column. If None, col_name is used. Default to 'GSIM'.
            col_name (str, optional): name of column in GSIM-file to be read. Defaults to '	"MEAN"'.
            remove_mv (bool, optional): whether or not remove missing values in timeseries. Defaults to True.
            mv_val (int, optional): missing value in timeseries. Defaults to -999.
            verbose (bool, optional): whether or not to show more info. Defaults to False.

        Returns:
            [pd.DataFrame, dict]: dataframe containing observational data; updated station properties dictionary
        """

        # open file
        f = open(self.fo)

        # find line in file in which meta-data starts and observational record starts
        for i, line in enumerate(f):
            if '#' in line:
                pass
            else:
                stopline = i
                break

        df = pd.read_csv(self.fo, skiprows=stopline, sep=',\t', skipinitialspace=True, na_values='NA', engine='python')

        # if var_name is specified, use it
        if var_name != None:
            var_name = var_name
        else:
            var_name = str(col_name)

        try: 
            if verbose: click.echo('VERBOSE -- reading column {}'.format(col_name))
            df[var_name] = df[str(col_name)].copy()

        except:
            if col_name == "MEAN":
                raise ValueError('ERROR: column "{}" - which is also the fall back option - cannot be found in file {}'.format(col_name, self.fo))
            else:
                warnings.warn('WARNING: column {} not found, falling back to column Value'.format(col_name))
                df[var_name] = df[' Value'].copy()
                del df[' Value']

        df.rename(columns={'"date"': 'date'}, inplace=True)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index(df['date'], inplace=True)

        df_out = pd.DataFrame(index=df.index,
                            data=df[var_name])
        
        if remove_mv == True:
            df_out.replace(mv_val, np.nan, inplace=True)

        mean_val = df_out[var_name].mean()
        ts_start = df_out.index.values[0]
        ts_end = df_out.index.values[-1]

        self.props['mean'] = round(mean_val, 3)
        self.props['ts_start'] = pd.to_datetime(ts_start, format='%Y-%m-%d')
        self.props['ts_end'] = pd.to_datetime(ts_end, format='%Y-%m-%d')

        self.df = df_out

        return self.df, self.props

    def update_props_from_file(self, fo: str) -> dict:
        """Updates station properties longitude, latitude, and area with data from a user-defined file.

        Args:
            fo (str): path to file containing data.

        Returns:
            dict: dictionary with updated station properties.
        """

        click.echo('INFO -- Updating station properties for station {}.'.format(self.props['gsim_no']))

        df = pd.read_csv(fo, delimiter=',', index_col=0, low_memory=False)

        df_station = df[df['gsim.no'].isin([self.props['gsim_no']])]

        if not df_station.empty:
            self.props['longitude'] = df_station['lon_snapped'].values[0]
            self.props['latitude'] = df_station['lat_snapped'].values[0]
            self.props['area'] = df_station['area_snapped'].values[0]

        else:
            warnings.warn('WARNING -- No data for station {} found in file {}.'.format(self.props['gsim_no'], fo))

        return self.props

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

## FUNCTIONS

def get_data_from_yml(yaml_root: str, data_dict: dict, station: str, var_name: str, encoding='ISO-8859-1', verbose=False) -> tuple[pd.DataFrame, dict, bool]: 
    """Extracting data from yaml-file for one station.
    This data contains of a dataframe with a timeseries and a dictionary with station properties.
    Additionally, a flag is returned whether or not to apply a window search.
    This is done automatically if the yaml-file should not contain lat/lon coordinates for a station.

    Args:
        yaml_root (str): location where yaml-file is stored.
        data_dict (dict): dictionary containing data of all GRDC stations to be evaluated.
        station (str): name of station to be evaluated.
        var_name (str): user-specified column name for returned dataframe.
        encoding (str, optional): encoding of GRDC file. Defaults to 'ISO-8859-1'.
        verbose (bool, optional): whether or not to print more info. Defaults to False.

    Returns:
        tuple[pd.DataFrame, dict, bool]: dataframe containing timeseries; dictionary containing station properties; flag wheter or not to execute window search
    """

    # each station in the yaml-file has data stored as a dictionary
    station_dict = data_dict[str(station)] 

    # if path to GRDC-file in yaml-file is relative, construct absolute path
    if not os.path.isabs(station_dict['file']):
        grdc_file = os.path.join(yaml_root, station_dict['file'])

    else:
        grdc_file = station_dict['file']           
    click.echo('INFO -- reading observations from file {}.'.format(grdc_file))

    grdc_obj = grdc_data(grdc_file)

    if verbose: click.echo('VERBOSE -- retrieving GRDC station properties.')
    grdc_props = grdc_obj.get_grdc_station_properties(encoding=encoding)

    # retrieving values from GRDC file
    # either use a specific column name for the GRDC file
    if 'column' in station_dict.keys():
        df_obs = grdc_obj.get_grdc_station_values(col_name=station_dict['column'], var_name=var_name, encoding=encoding, verbose=verbose)
    
    # or use the default name
    else:
        df_obs = grdc_obj.get_grdc_station_values(var_name=var_name, verbose=verbose, encoding=encoding)

    df_obs.set_index(pd.to_datetime(df_obs.index), inplace=True)

    # if 'lat' or 'lon' are specified for a station in the yaml-file,
    # use this instead of GRDC coordinates
    if 'lat' in station_dict.keys():
        if verbose: click.echo('VERBOSE -- overwriting GRDC latitude information {} with user input {}.'.format(grdc_props['latitude'], station_dict['lat']))
        grdc_props['latitude'] = station_dict['lat']

    if 'lon' in station_dict.keys():
        if verbose: click.echo('VERBOSE -- overwriting GRDC longitude information {} with user input {}.'.format(grdc_props['longitude'], station_dict['lon']))
        grdc_props['longitude'] = station_dict['lon']

    # if 'lat' and 'lon' are not specified for a station in the yaml-file,
    # apply window search to avoid mismatch of default GRDC coords
    if ('lon' in station_dict.keys()) and ('lat' in station_dict.keys()):
        apply_window_search = False

    else:
        apply_window_search = True

    return df_obs, grdc_props, apply_window_search