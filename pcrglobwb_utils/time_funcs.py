import pandas as pd


def calc_montly_avg(df_in, var_name=None):
    """Calculates the monthly averages of a timeseries.

    Parameters
    ---------
    df_in: dataframe
        pandas dataframe containing timeseries
    var_name: str, optional 
        header of column in df_in from which monthly averages are to be computed (default: {None})
    
    Returns
    -------
    dataframe
        pandas dataframe containing timeseries with monthly averages
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


def daily2monthly(df_in, plot=False):

    df_out = df_in.resample('M').sum()

    if plot: df_out.plot()

    return df_out

def daily2yearly(df_in, plot=False):

    df_out = df_in.resample('Y').sum()

    if plot: df_out.plot()

    return df_out