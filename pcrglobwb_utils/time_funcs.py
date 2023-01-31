#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import click

def resample_to_month(df: pd.DataFrame, stat_func='mean', suffix=None) -> pd.DataFrame:
    """Resamples a timeseries at sub-monthly time step to monthly values. 
    A range of monthly statistics can be chosen.
    If desired, the column name of the returned dataframe can contain a suffix for better distinguishment.
    By default, column names are unaltered.

    Args:
        df (pd.DataFrame): dataframe containing timeseries. Note, only tested with dataframes containing one column.
        stat_func (str, optional): Statistical method to be used. Either 'mean', 'max', 'min' or 'sum'. Defaults to 'mean'.
        suffix (str, optional): Suffix to be added to column of returned dataframe. Defaults to None.

    Returns:
        pd.DataFrame: dataframe containing resampled timeseries.
    """

    df = resample_time(df, 'M')

    click.echo('INFO -- resampling data to monthly time scale.')
    if stat_func == 'mean':
        df = df.mean()
    elif stat_func == 'max':
        df = df.max()
    elif stat_func == 'min':
        df = df.min()
    elif stat_func == 'sum':
        df = df.sum()
    else:
        raise ValueError('no supported statistical function provided - choose between mean, max, min or sum')

    if suffix != None:
        df = df.add_suffix(suffix)

    return df

def resample_to_annual(df: pd.DataFrame, stat_func='mean', suffix=None) -> pd.DataFrame:
    """Resamples a timeseries at sub-annual time step to annual values. 
    A range of annual statistics can be chosen.
    If desired, the column name of the returned dataframe can contain a suffix for better distinguishment.
    By default, column names are unaltered.

    Args:
        df (pd.DataFrame): dataframe containing timeseries. Note, only tested with dataframes containing one column.
        stat_func (str, optional): Statistical method to be used. Either 'mean', 'max', 'min' or 'sum'. Defaults to 'mean'.
        suffix (str, optional): Suffix to be added to column of returned dataframe. Defaults to None.

    Returns:
        pd.DataFrame: dataframe containing resampled timeseries.
    """

    df = resample_time(df, 'Y')

    click.echo('INFO -- resampling data to yearly time scale.')
    if stat_func == 'mean':
        df = df.mean()
    elif stat_func == 'max':
        df = df.max()
    elif stat_func == 'min':
        df = df.min()
    elif stat_func == 'sum':
        df = df.sum()
    else:
        raise ValueError('no supported statistical function provided - choose between mean, max, min or sum')

    if suffix != None:
        df = df.add_suffix(suffix)

    return df

def resample_time(df: pd.DataFrame, resampling_period: str) -> pd.DataFrame:
    """Resamples a dataframe in time.
    The resampling duration is set with 'time' and needs to follow pandas conventions.
    Output needs to be combined with a statistic, such as ".mean()".

    Args:
        df (pd.DataFrame): dataframe to be resampled.
        resampling_period (str): resampling duration.

    Returns:
        pd.DataFrame: actually returns a pd.core.resample.DatetimeIndexResampler
    """

    df = df.resample(resampling_period, convention='start')

    return df

def calc_monthly_climatology(df_in: pd.DataFrame, col_name=None) -> pd.DataFrame:
    """Calculates the climatological mean of each month across a timeseries at sub-monthly timestep.

    Args:
        df_in (pd.DataFrame): dataframe containing timeseries at sub-monthly timestep.
        col_name (str, optional): name of column to be considered only. Defaults to None.

    Returns:
        pd.DataFrame: dataframe containing mean of each month.
    """

    # if variable name is not None, then pick values from specified column
    if col_name != None:
        df = df_in[col_name]
    # else, just use the dataframe as is
    else:
        df = df_in
    
    # group values by month and then calculate mean
    df_out = df.groupby(df.index.month).mean()
    
    return df_out