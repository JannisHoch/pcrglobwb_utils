import pandas as pd
import click


def calc_montly_avg(df_in, var_name=None):
    """Calculates the monthly averages of a timeseries.

    Arguments:
        df_in (dataframe): pandas dataframe containing timeseries

    Keyword Arguments:
        var_name (str): header of column in df_in from which monthly averages are to be computed (default: None)

    Returns:
        dataframe: pandas dataframe containing timeseries with monthly averages
    """ 

    # if variable name is not None, then pick values from specified column
    if var_name != None:
        df = df_in[var_name]
    # else, just use the dataframe as is
    else:
        df = df_in
    
    # group values by month and then calculate mean
    df_out = df.groupby(df.index.month).mean()
    
    return df_out


def resample_to_month(df, stat_func='mean'):
    """[summary]

    Args:
        df ([type]): [description]
        stat_func (str, optional): [description]. Defaults to 'mean'.

    Raises:
        ValueError: [description]

    Returns:
        [type]: [description]
    """    

    click.echo('INFO -- resampling data to monthly time scale.')
    if stat_func == 'mean':
        df = df.resample('M', convention='start').mean()
    elif stat_func == 'max':
        df = df.resample('M', convention='start').max()
    elif stat_func == 'min':
        df = df.resample('M', convention='start').min()
    elif stat_func == 'sum':
        df = df.resample('M', convention='start').sum()
    else:
        raise ValueError('no supported statistical function provided - choose between mean, max, and min')

    return df

def resample_to_annual(df, stat_func='mean'):
    """[summary]

    Args:
        df ([type]): [description]
        stat_func (str, optional): [description]. Defaults to 'mean'.

    Raises:
        ValueError: [description]

    Returns:
        [type]: [description]
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
        raise ValueError('no supported statistical function provided - choose between mean, max, and min')

    return df