import pandas as pd


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


def daily2monthly(df_in, averaging=True, volumetric=False, volumetric_factor=86400, plot=False):
    """Aggregates daily values to monthly values. Note that the unit is not changed (m3/s) unless volumetric is True.

    Arguments:
        df_in (dataframe): dataframe containing daily values

    Keyword Arguments:
        averaging (bool) : whether or not to compute monthly average or not; if False, the monthly aggregate is computed (default: True)
        volumetric (bool): whether flux is converted to volume (e.g. m3/s to m3) (default: False)
        volumetric_factor (int): factor to convert flux to volume if specified (default: 86400)
        plot (bool): whether or not to plot the monthly timeseries (default: False)

    Returns:
        dataframe: dataframe containing monthly values
    """

    if averaging:
        df_out = df_in.resample('M').mean()
    else:
        df_out = df_in.resample('M').sum()

    if volumetric: df_out = df_out*volumetric_factor

    if plot: df_out.plot()

    return df_out

def daily2yearly(df_in, averaging=True, volumetric=False, volumetric_factor=86400, plot=False):
    """Aggregates daily values to yearly values. Note that the unit is not changed (m3/s) unless volumetric is True.

    Arguments:
        df_in (dataframe): dataframe containing daily values

    Keyword Arguments:
        averaging (bool) : whether or not to compute monthly average or not; if False, the monthly aggregate is computed (default: True)
        volumetric (bool): whether flux is converted to volume (e.g. m3/s to m3) (default: False)
        volumetric_factor (int): factor to convert flux to volume if specified (default: 86400)
        plot (bool): whether or not to plot the monthly timeseries (default: False)

    Returns:
        dataframe: dataframe containing yearly values
    """

    df_out = df_in.resample('Y').sum()

    if volumetric: df_out = df_out*86400

    if plot: df_out.plot()

    return df_out