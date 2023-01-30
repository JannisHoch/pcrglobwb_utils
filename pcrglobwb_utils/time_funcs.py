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

    click.echo('INFO -- resampling data to monthly {}.'.format(stat_func))
    if stat_func == 'mean':
        df = df.resample('M', convention='start').mean()
    elif stat_func == 'max':
        df = df.resample('M', convention='start').max()
    elif stat_func == 'min':
        df = df.resample('M', convention='start').min()
    elif stat_func == 'sum':
        df = df.resample('M', convention='start').sum()
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

    click.echo('INFO -- resampling data to yearly time scale.')
    if stat_func == 'mean':
        df = df.resample('Y', convention='start').mean()
    elif stat_func == 'max':
        df = df.resample('Y', convention='start').max()
    elif stat_func == 'min':
        df = df.resample('Y', convention='start').min()
    elif stat_func == 'sum':
        df = df.resample('Y', convention='start').sum()
    else:
        raise ValueError('no supported statistical function provided - choose between mean, max, min or sum')

    if suffix != None:
        df = df.add_suffix(suffix)

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