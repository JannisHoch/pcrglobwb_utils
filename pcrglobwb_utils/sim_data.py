import xarray as xr
import pandas as pd
import numpy as np
import click
import os
import warnings
from pathlib import Path

from . import time_funcs
from . import eval

## OBJECT AND METHODS
class from_nc:
    """Retrieving and working with timeseries data from a nc-file.

    Arguments:
        fo (str): path to nc-file
    """

    def __init__(self, fo: str) -> xr.Dataset:
        """Initializing class.
        Loads netCDF-file as xarray dataset.
        """

        self.ds = xr.open_dataset(fo, engine='netcdf4')

    def get_copy(self) -> xr.Dataset:
        """Returns a copy of the xarray dataset.

        Returns:
            xr.Dataset: dataset of netCDF-file.
        """

        cp = self.ds.copy()

        return cp

    def get_indices(self, lon: float, lat: float) -> tuple[int, int]:
        """Gets row,col indices in 2D-dataset corresponding to lat,lon values of a point.

        Args:
            lon (float): longitude of point.
            lat (float): latitude of point.

        Returns:
            tuple[int, int]: row, col of point.
        """

        idx_row, idx_col = find_indices_from_coords(self.ds, lon, lat)

        return idx_row, idx_col
    
    def get_values_from_indices(self, idx_row: int, idx_col: int, var_name='discharge') -> pd.DataFrame:
        """Extracts timeseries from dataset for a given location.
        Location defined by its row and col indices in 2D-dataset.
        Timeseries is returned as a dataframe.

        Args:
            idx_row (int): row index of point.
            idx_col (int): col index of point.
            var_name (str, optional): name of variable to be extracted from dataset. Defaults to 'discharge'.

        Returns:
            pd.DataFrame: dataframe containing timeseries.
        """

        df = read_at_indices(self.ds, idx_row, idx_col, var_name=var_name)
        
        self.df = df

        return self.df

    def get_values_from_coords(self, lon: float, lat: float, var_name='discharge') -> pd.DataFrame:
        """Extracts timeseries from dataset for a given location.
        Location defined by its lon and lat values.
        Timeseries is returned as a dataframe.

        Args:
            lon (float): longitude of point.
            lat (float): latitude of point.
            var_name (str, optional): name of variable to be extracted from dataset. Defaults to 'discharge'.

        Returns:
            pd.DataFrame: dataframe containing timeseries.
        """

        df = read_at_coords(self.ds, lon, lat, var_name=var_name)
        
        self.df = df

        return self.df

    def to_monthly(self, stat_func='mean', suffix=None) -> pd.DataFrame:
        """Resampling values to monthly time scale.

        Args:
            stat_func (str): statistical descriptor to be used in resampling. Currently supported is 'mean', 'max', and 'min' (default: mean)

        Returns:
            pd.DataFrame: dataframe containing monthly values
        """        

        df = self.df

        df = time_funcs.resample_to_month(df, stat_func=stat_func, suffix=suffix)

        return df

    def to_annual(self, stat_func='mean') -> pd.DataFrame:
        """Resampling values to annual time scale.

        Keyword Arguments:
            stat_func (str): statistical descriptor to be used in resampling . currently supported is 'mean', 'max', and 'min' (default: mean)

        Returns:
            pd.DataFrame: dataframe containing monthly annual values
        """       

        df = self.df 

        df = time_funcs.resample_to_annual(df, stat_func=stat_func)
        
        return df

    def validate(self, df_obs: pd.DataFrame, out_dir: str, station: str, suffix=None, var_name_obs=None, var_name_sim=None, time_scale=None, return_all_KGE=False) -> pd.DataFrame:
        """Validates simulated data with observed data.
        Metric values are stored to a dictionary and returned as dataframe.

        Args:
            df_obs (pd.DataFrame): dataframe containing observed data.
            out_dir (str): location to store metrics as dictionary.
            station (str): name of station or other ID.
            suffix (str, optional): suffix to be added to output. Defaults to None.
            var_name_obs (str, optional): column name of observed data. Defaults to None.
            var_name_sim (str, optional): column name of simulated data. Defaults to None.
            time_scale (str, optional): 
            return_all_KGE (bool, optional): whether or not to return all KGE components. Defaults to False.

        Returns:
            pd.DataFrame: dataframe containing metric values.
        """

        df_sim = self.df

        df_out = validate_timeseries(df_sim, df_obs, out_dir, station,
                                     suffix=suffix, var_name_obs=var_name_obs, var_name_sim=var_name_sim, time_scale=time_scale, return_all_KGE=return_all_KGE)
        
        return df_out

## FUNCTIONS ##

def find_indices_from_coords(ds: xr.Dataset, lon: float, lat: float, window_search=False, obs_mean=None, var_name='discharge', window=5) -> tuple[int, int]:  
    """Gets row,col indices in 2D-dataset corresponding to lat,lon values of a point.
    If needed, a search window can be applied around this point to determine the indices where mean observed and mean simulated values match best. 
    This can be useful if the lat/lon values of the point are not accurate enough, and to avoid extracting data from a 'wrong' point in general.

    Args:
        ds (xr.Dataset): dataset containing simulated data.
        lon (float): longitude of point.
        lat (float): latitude of point.
        window_search (bool, optional): whether or not to apply a window search for indices which match best between mean simulated and mean observed values. Defaults to False.
        obs_mean (float, optional): mean of observed values, needed to find best matching indices. Defaults to None.
        var_name (str, optional): variable name of simulated data in 'ds'. Defaults to 'discharge'.
        window (int, optional): size of seach window around point. Defaults to 5.

    Returns:
        tuple[int, int]: row, col indices of point.
    """

    # if a window search for best matching indices is to be applied
    if window_search:

        if obs_mean == None:
            raise ValueError('"obs_mean" needs to be set, should not be None.')

        new_lat, new_lon = apply_window_search(ds, lon, lat, obs_mean=obs_mean, var_name=var_name, window=window)

    # else, find indices closest to specified lat/lon values
    else:

        new_lat = lat
        new_lon = lon

    try:
        abslat = np.abs(ds.lat-new_lat)
        abslon = np.abs(ds.lon-new_lon)
    except:
        abslat = np.abs(ds.latitude-new_lat)
        abslon = np.abs(ds.longitude-new_lon)

    c = np.maximum(abslon, abslat)

    try:
        ([idx_col], [idx_row]) = np.where(c == np.min(c))
    except:
        idxs = np.where(c == np.min(c))
        idx_col, idx_row = (np.min(idxs[0]), np.min(idxs[1]))

    return idx_row, idx_col

def apply_window_search(ds: xr.Dataset, lon: float, lat: float, obs_mean=None, var_name='discharge', window=5) -> tuple[float, float]:
    """Applies a window search around a point.
    Within this window, it searches for the location where mean observed and mean simulated discharge matches best.
    To that end, the mean observed value needs to be provided.
    The mean simulated discharge is calculated on-the-fly for variable 'var_name'.

    Args:
        ds (xr.Dataset): dataset containing simulated data.
        lon (float): longitude of point
        lat (float): latitude of point
        obs_mean (float, optional): mean of observed values. Defaults to None.
        var_name (str, optional): variable name of simulated data in 'ds'. Defaults to 'discharge'.
        window (int, optional): size of seach window around point. Defaults to 5.

    Returns:
        tuple[float, float]: updated lat/lon values.
    """

    click.echo('INFO -- Applying search within {} km window for finding cell with best matching discharge.'.format(window))
    
    # find lat/lon coords for cell in window which matches observation mean best
    # define search window of 5 km in all direction
    min_lon = lon - window * 0.008333333
    max_lon = lon + window * 0.008333333
    min_lat = lat - window * 0.008333333
    max_lat = lat + window * 0.008333333

    # create mask for search window
    try:
        mask_lon = (ds.lon >= min_lon) & (ds.lon <= max_lon)
        mask_lat = (ds.lat >= min_lat) & (ds.lat <= max_lat)
    except:
        mask_lon = (ds.longitude >= min_lon) & (ds.longitude <= max_lon)
        mask_lat = (ds.latitude >= min_lat) & (ds.latitude <= max_lat)

    # mask initial array and determine mean over time, if possible
    # reasons why not possible: GRDC station coords not found in nc-file
    try:
        cropped_ds = ds.where(mask_lon & mask_lat, drop=True)
        cropped_ds = cropped_ds.mean('time')

        # determine match between simulation and observation
        dev_ds = cropped_ds.assign(deviation = cropped_ds[var_name] / obs_mean)
        # where deviation is the smallest, assign True
        dev_mask_ds = xr.where(dev_ds == np.max(dev_ds.deviation.values), True, False)
        # mask out all other cells
        out = dev_ds.where(dev_mask_ds.deviation, drop=True)

        # retrieve new lat/lon coords
        try:
            new_lon = out.lon.values[0]
            new_lat = out.lat.values[0]
        except:
            new_lon = out.longitude.values[0]
            new_lat = out.latitude.values[0]

        if (lat, lon) != (new_lat, new_lon):
            click.echo('INFO -- Original lat/lon coords {}/{} were replaced by {}/{}.'.format(lat, lon, new_lat, new_lon))
        else:
            click.echo('INFO -- Original lat/lon coords remain unchanged after window search')

    # if not possible, do not apply masks and continue
    except:
        click.echo('INFO -- Window search not possible.')
        new_lat = lat
        new_lon = lon

    return new_lat, new_lon

def read_at_indices(ds_obs: xr.Dataset, idx_row: int, idx_col: int, var_name='discharge') -> pd.DataFrame:
    """Extracts time series from a point (cell) in a 2D-dataset defined by its row/col indices.
    The variable from which data to extract can be defined with 'var_name'.
    Stores time series to dataframe with datetime index.

    .. note:: 
        In fact it is a 3D-dataset with data in two dimensions plus time as third dimension.

    Args:
        ds_obs (xr.Dataset): dataset from which to extract the timeseries.
        idx_row (int): row index of point.
        idx_col (int): column index of point.
        var_name (str, optional): name of variable to be extracted from dataset. Defaults to 'discharge'.

    Returns:
        pd.DataFrame: dataframe containing timeseries with datetime index.
    """

    # read variable values at indices as xarray DataArray
    try:
        dsq = ds_obs[var_name].isel(lat=idx_row, lon=idx_col)
    except:
        dsq = ds_obs[var_name].isel(latitude=idx_row, longitude=idx_col)

    df = pd.DataFrame(data=dsq.to_pandas(), columns=[var_name])

    # if data is at monthly time step, we drop day from timestemp
    # as montlhy data may not be set to same day within a month
    if (pd.infer_freq(df.index) == 'M') or (pd.infer_freq(df.index) == 'MS'):
        print('changing index strftime to %Y-%m')
        df.index = df.index.strftime('%Y-%m')
    
    return df

def read_at_coords(ds_obs: xr.Dataset, lon: float, lat: float, var_name='discharge') -> pd.DataFrame:
    """Extracts time series from a point (cell) in a 2D-dataset defined by its longitude and latitude.
    The variable from which data to extract can be defined with 'var_name'.
    Stores time series to dataframe with datetime index.

    .. note:: 
        In fact it is a 3D-dataset with data in two dimensions plus time as third dimension.

    Args:
        ds_obs (xr.Dataset): dataset from which to extract the timeseries.
        lon (float): longitude of point.
        lat (float): latitude of point.
        var_name (str, optional): name of variable to be extracted from dataset. Defaults to 'discharge'.

    Returns:
        pd.DataFrame: _dataframe containing timeseries with datetime index.
    """

    # read variable values at indices as xarray DataArray
    try:
        dsq = ds_obs[var_name].sel(lat=lat, lon=lon, method='nearest')
    except:
        dsq = ds_obs[var_name].sel(latitude=lat, longitude=lon, method='nearest')

    df = pd.DataFrame(data=dsq.to_pandas(), columns=[var_name])

    if df.isnull().values.all():
        warnings.warn('WARNING -- Only NaN found for this location')

    # if data is at monthly time step, we drop day from timestemp
    # as montlhy data may not be set to same day within a month
    if (pd.infer_freq(df.index) == 'M') or (pd.infer_freq(df.index) == 'MS'):
        print('changing index strftime to %Y-%m')
        df.index = df.index.strftime('%Y-%m')

    return df

def validate_timeseries(df_sim: pd.DataFrame, df_obs: pd.DataFrame, out_dir: str, station: str, suffix=None, var_name_obs=None, var_name_sim=None, time_scale=None,return_all_KGE=False) -> dict:
    """Validates two timeseries with each other, i.e., observations with simulations.
    Timeseries are stored in dataframes.
    If dataframes containg multiple columns, a column can be specified with 'var_name_obs' and 'var_name_sim', respectively.
    Obviously, both timeseries should have a common time period.
    Both the evaluated timeseries and the resulting evaluation metric values are stored as csv-files.

    Args:
        df_sim (pd.DataFrame): dataframe containing simulated timeseries.
        df_obs (pd.DataFrame): dataframe containing observed timeseries.
        out_dir (str): directory where to store csv-files of timeseries and metrics.
        station (str): name of station or location where simulation is evaluated. Can also be any form of unique ID.
        suffix (str, optional): suffix to be added to csv-files. Defaults to None.
        var_name_obs (str, optional): column name in 'df_obs' containing timeseries. Defaults to None.
        var_name_sim (str, optional): column name in 'df_sim' containing timeseries. Defaults to None.
        time_scale (str, optional):
        return_all_KGE (bool, optional): whether or not to return all components of the KGE. Defaults to False.

    Returns:
        dict: dictionary containing evaluation metric values.
    """

    # create output folder, if needed
    Path(out_dir).mkdir(parents=True, exist_ok=True)

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

    if time_scale != None:
        click.echo('INFO -- Resampling timeseries to period {}'.format(time_scale))
        df_obs = time_funcs.resample_time(df_obs, resampling_period=time_scale).mean()
        df_sim = time_funcs.resample_time(df_sim, resampling_period=time_scale).mean()
    
    # concatenate both dataframes
    try:
        both = pd.concat([df_obs, df_sim], axis=1, join="inner", verify_integrity=True)
    except:
        warnings.warn('WARNING: concatenation did not succeed, now trying to resolve by removing duplicate indices.')
        df_obs = df_obs[~df_obs.index.duplicated(keep='first')]
        df_sim = df_sim[~df_sim.index.duplicated(keep='first')]
        both = pd.concat([df_obs, df_sim], axis=1, join="inner", verify_integrity=True)

    # raise error if there is no common time period
    if both.empty:
        warnings.warn('WARNING: no common time period of observed and simulated values found in dataframes!')

    if suffix != None:
        both.to_csv(os.path.join(out_dir, 'evaluated_timeseries_{}.csv'.format(suffix)))
    else:
        both.to_csv(os.path.join(out_dir, 'evaluated_timeseries.csv'))

    # drop all entries where any of the dataframes contains NaNs
    # this yields a dataframe containing values only for common time period
    # which is needed to applying objective functions
    both_noMV = both.dropna()

    assert both_noMV.columns.size == 2, 'More than two columns with data found at station {}, please check why. It is not working...'.format(station)

    # # apply objective functions
    metrics_dict = eval.calc_metrics(both_noMV, both_noMV.columns[0], both_noMV.columns[1], return_all=return_all_KGE)

    # save dict to csv
    try:
        df_out = pd.DataFrame().from_dict(metrics_dict, columns=[station], orient='index')
    except:
        df_out = pd.DataFrame().from_dict(metrics_dict, columns=[station])

    if suffix != None:
        df_out.to_csv(os.path.join(out_dir, 'evaluation_{}.csv'.format(suffix)))
    else:
        df_out.to_csv(os.path.join(out_dir, 'evaluation.csv'))

    return metrics_dict