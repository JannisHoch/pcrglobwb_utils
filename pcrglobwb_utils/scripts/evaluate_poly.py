#!/usr/bin/env python
# coding: utf-8

import pcrglobwb_utils
from . import funcs
import click
import xarray as xr
import pandas as pd
import geopandas as gpd
import multiprocessing as mp
import matplotlib
matplotlib.use('Agg')
from datetime import datetime
import os

@click.command()
@click.argument('ply',)
@click.argument('sim',)
@click.argument('obs',)
@click.argument('out',)
@click.option('-id', '--ply-id', help='unique identifier in file containing polygons.', type=str)
@click.option('-o', '--obs_var_name', help='variable name in observations.', type=str)
@click.option('-s', '--sim_var_name', help='variable name in simulations.', type=str)
@click.option('-cf', '--conversion-factor', default=1, help='conversion factor applied to simulated values to align variable units.', type=int)
@click.option('-crs', '--coordinate-system', default='epsg:4326', help='coordinate system.', type=str)
@click.option('--time-step', '-tstep', help='timestep of data - either "monthly" or "annual". Note that both observed and simualted data must be annual average if the latter option is chosen.', default='monthly', type=str)
@click.option('-N', '--number-processes', default=None, help='number of processes to be used in multiprocessing.Pool()- defaults to number of CPUs in the system.', type=int)
@click.option('-om', '--obs-masks', default=None, help='path to file with pickled paths to preprocessed masks per polygon for observations.', type=str)
@click.option('-sm', '--sim-masks', default=None, help='path to file with pickled paths to preprocessed masks per polygon for simulations.', type=str)
@click.option('--anomaly/--no-anomaly', default=False, help='whether or not to compute anomalies.')
@click.option('--plot/--no-plot', default=False, help='whether or not to save a simple plot of results.')
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')

def main(ply, sim, obs, out, ply_id, obs_var_name, sim_var_name, obs_masks, sim_masks, time_step, number_processes, anomaly, conversion_factor, coordinate_system, plot, verbose):
    """

    Computes r, MSE, and RMSE for multiple polygons as provided by a shape-file between simulated and observed data.
    Each polygon needs to have a unique ID.pickled_masks
    Contains multiple options to align function settings with data and evaluation properties.

    Returns a GeoJSON-file of r, MSE, and RMSE per polygon, and if specified as simple plot. 
    Also returns scores of r, MSE, RMSE, and RRMSE per polygon as dataframe.
    
    PLY: path to shp-file or geojson-file with one or more polygons.

    SIM: path to netCDF-file with simulated data.

    OBS: path to netCDF-file with observed data.

    OUT: Path to output folder. Will be created if not there yet.

    """  

    t_start = datetime.now()

    click.echo(click.style('INFO -- start.', fg='green'))
    click.echo(click.style('INFO -- pcrglobwb_utils version {}.'.format(pcrglobwb_utils.__version__), fg='green'))

    # get full path name of output-dir and create it if not there yet
    out = os.path.abspath(out)
    pcrglobwb_utils.utils.create_out_dir(out)

    # read nc-files with xarray to datasets
    click.echo(click.style('INFO -- reading observed variable {} from {}'.format(obs_var_name, obs), fg='red'))
    obs_ds = xr.open_dataset(obs)
    click.echo(click.style('INFO -- reading simulated variable {} from {}'.format(sim_var_name, sim), fg='red'))
    sim_ds = xr.open_dataset(sim)

    # extract variable data from datasets
    if verbose: click.echo('VERBOSE -- extract data from files')
    obs_data = obs_ds[obs_var_name]
    if verbose: click.echo('VERBOSE -- applying conversion factor {} to simulated data'.format(conversion_factor))
    sim_data = sim_ds[sim_var_name] * conversion_factor

    # retrieve time indices
    obs_idx = pd.to_datetime(pd.to_datetime(obs_ds.time.values).strftime('%Y-%m'))
    sim_idx = pd.to_datetime(pd.to_datetime(sim_ds.time.values).strftime('%Y-%m'))

    # read shapefile with one or more polygons
    click.echo(click.style('INFO -- reading polygons from {}'.format(os.path.abspath(ply)), fg='red'))
    extent_gdf = gpd.read_file(ply, crs=coordinate_system, driver='GeoJSON')

    # align spatial settings of nc-files to be compatible with geosjon-file or ply-file
    if verbose: click.echo('VERBOSE -- setting spatial dimensions and crs of nc-files')
    try:
        obs_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
    except:
        obs_data.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)
    obs_data.rio.write_crs(coordinate_system, inplace=True)

    try:
        sim_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
    except:
        sim_data.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)
    sim_data.rio.write_crs(coordinate_system, inplace=True)

    # if masks for observations is provided...
    if obs_masks != None:
        # ... check first if there is also one provided for simulations
        if sim_masks != None:
            # unpickle dataframe with polygons IDs and corresponding masks for observations
            obs_masks = os.path.abspath(obs_masks)
            click.echo(click.style('INFO -- reading paths to preprocessed masks from {}'.format(obs_masks), fg='red'))
            obs_masks = funcs.unpickle_object(obs_masks)
            # unpickle dataframe with polygons IDs and corresponding masks for simulations
            sim_masks = os.path.abspath(sim_masks)
            click.echo(click.style('INFO -- reading paths to preprocessed masks from {}'.format(sim_masks), fg='red'))
            sim_masks = funcs.unpickle_object(sim_masks)
            # reduce polgyons to be evaluated to those for which a mask is provided
            poly_list = obs_masks.index.values

        # if not, raise error
        else:
            raise ValueError('ERROR -- if providing -om/--obs-masks, also provide -sm/--sim-masks!')
    # otherwise, set masks to None and use all polygon IDs in geojson-file
    else:
        obs_masks = None
        sim_masks = None
        poly_list = extent_gdf[ply_id].unique()

    click.echo('INFO -- evaluating each polygon')
    # if a number of processes for parallelization are provided, set up multiprocessing and evalute polygons
    if number_processes != None:

        # derive actually available and sensible number of cores to use for application
        min_number_processes = min(number_processes, len(extent_gdf), mp.cpu_count())
        # if required, reduce provided number of processes
        if number_processes > min_number_processes: 
            click.echo('INFO -- number of CPUs reduced to {}'.format(min_number_processes))
        else:
            click.echo('INFO -- using {} CPUs for multiprocessing'.format(min_number_processes))
        # set up multiprocessing
        pool = mp.Pool(processes=min_number_processes)

        # apply function and convert returned data to list
        results = [pool.apply_async(funcs.evaluate_polygons,args=(ID, ply_id, extent_gdf, obs_data, sim_data, obs_var_name, sim_var_name, obs_idx, sim_idx, obs_masks, sim_masks, time_step, anomaly, verbose)) for ID in poly_list]
        outputList = [p.get() for p in results]

    # otherwise, evaluate polygons without multiprocessing
    else:

        # apply function and retrieve list
        outputList = [funcs.evaluate_polygons(ID, ply_id, extent_gdf, obs_data, sim_data, obs_var_name, sim_var_name, obs_idx, sim_idx, obs_masks, sim_masks, time_step, anomaly, verbose) for ID in poly_list]
    
    # write output from list
    funcs.write_output_poly(outputList, sim_var_name, obs_var_name, out, plot)

    t_end = datetime.now()
    delta_t  = t_end - t_start
    
    click.echo(click.style('INFO -- done.', fg='green'))
    click.echo(click.style('INFO -- run time: {}.'.format(delta_t), fg='green'))