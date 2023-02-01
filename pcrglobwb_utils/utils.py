#!/usr/bin/env python
# coding: utf-8

import pcrglobwb_utils
import xarray as xr
import pandas as pd
import numpy as np
import geopandas as gpd
import rioxarray as rio
import rasterio
import yaml
import click
import glob
import os
import shutil

def print_versions():

    print('pcrglobwb_utils version {}'.format(pcrglobwb_utils.__version__))
    print('pandas version {}'.format(pd.__version__))
    print('xarray version {}'.format(xr.__version__))
    print('numpy version {}'.format(np.__version__))
    print('geopandas version {}'.format(gpd.__version__))
    print('rasterio version {}'.format(rasterio.__version__))
    print('rioxarray version {}'.format(rio.__version__))

def get_idx_as_strftime(df, strftime_format='%Y-%m-%d'):

    idx = df.index.strftime(strftime_format)

    return idx

def check_mode(data_loc: str) -> str:
    """Checks whether GRDC data is read via a yml-file or all files within a folder are used.

    Args:
        data_loc (str): path to yml-file or folder.

    Returns:
        str: mode of evaluation, either 'yml' or 'fld'.
    """

    if os.path.isfile(data_loc):
        mode = 'yml'
    elif os.path.isdir(data_loc):
        mode = 'fld'
    else:
        raise ValueError('Neither a file or a folder are specified.')

    return mode

def read_yml(yaml_file: str) -> dict:
    """Loads and parses a yaml-file and returns its content as a dictionary.

    Args:
        yaml_file (str): path to yaml-file.

    Returns:
        dict: dictionary containing content of yaml-file.
    """

    # get path to yml-file containing GRDC station info
    yaml_file = os.path.abspath(yaml_file)
    click.echo(click.style('INFO -- parsing GRDC station information from file {}'.format(yaml_file), fg='red'))
    # get content of yml-file
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)

    return data

def glob_folder(folder: str, col_name: str, verbose=False, encoding='ISO-8859-1') -> dict:
    """Collects and reads all files within a folder.
    Assumes all files are GRDC files and retrieves station properties and values from file.
    Returns all of this info as dictionary.
    In this dictionary, GRDC stations are keys and per key a list with GRDC properties and values is stored.

    Args:
        folder (str): path to folder where GRDC files are stored. Note that no other files should be stored here.
        col_name (str): column name in GRDC files to be read from.
        verbose (bool, optional): whether or not to print more info. Defaults to False.
        encoding (str, optional): encoding of GRDC files.. Defaults to 'ISO-8859-1'.

    Returns:
        dict: dictionary containing properties and values for all GRDC stations found in 'folder'.
    """

    folder = os.path.abspath(folder)
    click.echo('INFO -- folder with GRDC data is {}'.format(folder))
    files = sorted(glob.glob(os.path.join(folder,'*')))

    dd = dict()

    for f in files:

        if verbose: click.echo('VERBOSE -- loading GRDC file {} with encoding {}.'.format(f, encoding))

        grdc_data = pcrglobwb_utils.obs_data.grdc_data(f)
        props = grdc_data.get_grdc_station_properties(encoding=encoding)

        # retrieving values from GRDC file
        df_obs = grdc_data.get_grdc_station_values(col_name=col_name, var_name='OBS', encoding=encoding, verbose=verbose)
        # not sure if that's needed, but better be safe than sorry
        df_obs.set_index(pd.to_datetime(df_obs.index), inplace=True)

        dd[str(props['station'])] = [props, df_obs]

    return dd

def create_out_dir(out_dir: str) -> None:
    """Creates output directory.
    If directory already exists, it is recreated.

    Args:
        out_dir (str): path of output directory.
    """

    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    
    os.makedirs(out_dir)
    click.echo('INFO -- saving output to folder {}'.format(out_dir))

def get_data_from_yml(yaml_root: str, grdc_data_dict: dict, station: str, var_name: str, encoding='ISO-8859-1', verbose=False) -> tuple[pd.DataFrame, dict, bool]: 
    """Extracting data from yaml-file for one station.
    This data contains of a dataframe with a timeseries and a dictionary with station properties.
    Additionally, a flag is returned whether or not to apply a window search.
    This is done automatically if the yaml-file should not contain lat/lon coordinates for a station.

    Args:
        yaml_root (str): location where yaml-file is stored.
        grdc_data_dict (dict): dictionary containing data of all GRDC stations to be evaluated.
        station (str): name of station to be evaluated.
        var_name (str): user-specified column name for returned dataframe.
        encoding (str, optional): encoding of GRDC file. Defaults to 'ISO-8859-1'.
        verbose (bool, optional): whether or not to print more info. Defaults to False.

    Returns:
        tuple[pd.DataFrame, dict, bool]: dataframe containing timeseries; dictionary containing station properties; flag wheter or not to execute window search
    """

    # each station in the yaml-file has data stored as a dictionary
    station_dict = grdc_data_dict[str(station)] 

    # if path to GRDC-file in yaml-file is relative, construct absolute path
    if not os.path.isabs(station_dict['file']):
        grdc_file = os.path.join(yaml_root, station_dict['file'])

    else:
        grdc_file = station_dict['file']           
    click.echo('INFO -- reading observations from file {}.'.format(grdc_file))

    grdc_data = pcrglobwb_utils.obs_data.grdc_data(grdc_file)

    if verbose: click.echo('VERBOSE -- retrieving GRDC station properties.')
    grdc_props = grdc_data.get_grdc_station_properties(encoding=encoding)

    # retrieving values from GRDC file
    # either use a specific column name for the GRDC file
    if 'column' in station_dict.keys():
        df_obs = grdc_data.get_grdc_station_values(col_name=station_dict['column'], var_name=var_name, encoding=encoding, verbose=verbose)
    
    # or use the default name
    else:
        df_obs = grdc_data.get_grdc_station_values(var_name=var_name, verbose=verbose, encoding=encoding)

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

def align_geo(ds, crs_system='epgs:4326', verbose=False):

    # align spatial settings of nc-files to be compatible with geosjon-file or ply-file
    if verbose: click.echo('VERBOSE -- setting spatial dimensions and crs of nc-files')
    
    try:
        ds.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
    except:
        ds.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)

    ds.rio.write_crs(crs_system, inplace=True)

    return ds

def concat_dataframes(obs_data_c, sim_data_c, obs_var_name, sim_var_name, obs_idx, sim_idx, time_step, anomaly, verbose):

    # initiate output lists
    mean_val_timestep_obs = list()
    mean_val_timestep_sim = list()

    # compute mean per time step in clipped data-array and append to array
    for i in range(len(obs_data_c.time.values)):
        time = obs_data_c.time[i]
        t = pd.to_datetime(time.values)
        mean = float(obs_data_c.sel(time=t).mean(skipna=True))
        mean_val_timestep_obs.append(mean)
    for i in range(len(sim_data_c.time.values)):
        time = sim_data_c.time[i]
        t = pd.to_datetime(time.values)
        mean = float(sim_data_c.sel(time=t).mean(skipna=True))
        mean_val_timestep_sim.append(mean)

    # determine anomalies is specified
    if anomaly:
        if verbose: click.echo('VERBOSE -- determine anomalies of SIM data.')
        # mean_val_timestep_obs = mean_val_timestep_obs - np.mean(mean_val_timestep_obs)
        mean_val_timestep_sim = mean_val_timestep_sim - np.mean(mean_val_timestep_sim)

    obs_df = pd.DataFrame(data=mean_val_timestep_obs, index=obs_idx, columns=[obs_var_name])
    sim_df = pd.DataFrame(data=mean_val_timestep_sim, index=sim_idx, columns=[sim_var_name])

    # accounting for missing values in time series (and thus missing index values!)
    if time_step == 'monthly':
        if verbose: click.echo('VERBOSE -- covering missing months in observation or simulation data.')
        obs_df = obs_df.resample('D').mean().fillna(np.nan).resample('M').mean()
        sim_df = sim_df.resample('D').mean().fillna(np.nan).resample('M').mean()  
    if time_step == 'annual':
        if verbose: click.echo('VERBOSE -- covering missing years in observation or simulation data.')
        obs_df = obs_df.resample('D').mean().fillna(np.nan).resample('Y').mean()
        sim_df = sim_df.resample('D').mean().fillna(np.nan).resample('Y').mean()  

    # concatenating both dataframes to drop rows with missing values in one of the columns
    # dropping rows with missing values is import because time extents of both files probably do not match
    if verbose: click.echo('VERBOSE -- concatenating observed and simulated data.')
    final_df = pd.concat([obs_df, sim_df], axis=1).dropna()

    return final_df
