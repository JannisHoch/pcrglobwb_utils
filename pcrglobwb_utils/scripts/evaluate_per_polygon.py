#!/usr/bin/env python
# coding: utf-8

import click
import pandas as pd
import xarray as xr
import numpy as np
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import spotpy
import os

@click.command()
@click.argument('shp',)
@click.argument('sim',)
@click.argument('obs',)
@click.argument('out',)
@click.option('-id', '--shp-id', help='unique identifier in shp-file.', type=str)
@click.option('-o', '--obs_var_name', help='variable name in observations.', type=str)
@click.option('-s', '--sim_var_name', help='variable name in simulations.', type=str)
@click.option('-cf', '--conversion-factor', default=1, help='conversion factor applied to simulated values to align variable units.', type=int)
@click.option('-crs', '--coordinate-system', default='epsg:4326', help='coordinate system.', type=str)
@click.option('--anomaly/--no-anomaly', default=False, help='whether or not to compute anomalies.')
@click.option('--sum/--no-sum', default=False, help='whether or not the simulated values or monthly totals or not.')
@click.option('--plot/--no-plot', default=False, help='whether or not to save a simple plot fo results.')
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')

def cli(shp, sim, obs, out, shp_id, obs_var_name, sim_var_name, sum, anomaly, conversion_factor, coordinate_system, plot, verbose):
    """

    Computes r and RMSE for multiple polygons as provided by a shape-file between simulated and observed data.
    Each polygon needs to have a unique ID.
    Contains multiple options to align function settings with data and evaluation properties.

    Returns a GeoJSON-file of r and RMSE per polygon, and if specified as simple plot. 
    Also returns scores of r and RMSE as dataframe.
    
    SHP: path to shp-file with one or more polygons.

    SIM: path to netCDF-file with simulated data.

    OBS: path to netCDF-file with observed data.

    OUT: Path to output folder. Will be created if not there yet.

    """    

    # print some info at the beginning
    click.echo('\n')
    click.echo('INFO: validating variable {} from file {}'.format(sim_var_name, sim))
    click.echo('INFO: with variable {} from file {}\n'.format(obs_var_name, obs))

    # get full path name of output-dir and create it if not there yet
    out = os.path.abspath(out)
    if not os.path.isdir(out):
        os.makedirs(out)
    print('INFO:saving output to folder {}'.format(out))

    # read nc-files with xarray to datasets
    print('INFO: reading file {}'.format(os.path.abspath(obs)))
    obs_ds = xr.open_dataset(obs)
    print('INFO: reading file {}'.format(os.path.abspath(sim)))
    sim_ds = xr.open_dataset(sim)

    # extract variable data from datasets
    print('INFO: extract data from files')
    obs_data = obs_ds[obs_var_name]
    click.echo('INFO: applying conversion factor of {} to simulated data'.format(conversion_factor))
    sim_data = sim_ds[sim_var_name] * conversion_factor

    obs_idx = pd.to_datetime(pd.to_datetime(obs_ds.time.values).strftime('%Y-%m'))
    sim_idx = pd.to_datetime(pd.to_datetime(sim_ds.time.values).strftime('%Y-%m'))

    if sum:
        click.echo('INFO: converting monthly sum to monthly mean.')
        obs_daysinmonth = obs_idx.daysinmonth.values
        sim_daysinmonth = sim_idx.daysinmonth.values

    # read shapefile with one or more polygons
    print('INFO: reading shp-file {}'.format(os.path.abspath(shp)))
    extent_gdf = gpd.read_file(shp, crs=coordinate_system)

    # align spatial settings of nc-files to be compatible with shp-file
    click.echo('INFO: setting spatial dimensions and crs of nc-files')
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

    # initializing 'master' dictionary to store metrics per polygon
    out_dict = {}

    click.echo('INFO: evaluating each polygon')
    # go through all polygons in the shp-file as identfied by a unique ID
    for ID in extent_gdf[shp_id].unique():

        if verbose: click.echo('VERBOSE: computing R and RMSE for polygon with key identifier {}'.format(ID))
        poly = extent_gdf.loc[extent_gdf[shp_id] == ID]

        # clipping obs data-array to shape extent
        obs_data_c = obs_data.rio.clip(poly.geometry, poly.crs, drop=True)
        # clipping sim data-array to shape extent
        sim_data_c = sim_data.rio.clip(poly.geometry, poly.crs, drop=True)

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
            if verbose: click.echo('VERBOSE: determine anomalies.')
            mean_val_timestep_obs = mean_val_timestep_obs - np.mean(mean_val_timestep_obs)
            mean_val_timestep_sim = mean_val_timestep_sim - np.mean(mean_val_timestep_sim)

        if sum:
            
            if verbose: click.echo('VERBOSE: computing average daily values from monthly sum by dividing sum with days in month.')
            
            obs_tuples = list(zip(mean_val_timestep_obs, obs_daysinmonth))
            obs_df = pd.DataFrame(obs_tuples, index=obs_idx, columns=[obs_var_name, 'obs_daysinmonth'])
            obs_df[obs_var_name] = obs_df[obs_var_name].divide(obs_df['obs_daysinmonth'])
            del obs_df['obs_daysinmonth']

            sim_tuples = list(zip(mean_val_timestep_sim, sim_daysinmonth))
            sim_df = pd.DataFrame(data=sim_tuples, index=sim_idx, columns=[sim_var_name, 'sim_daysinmonth'])
            sim_df[sim_var_name] = sim_df[sim_var_name].divide(sim_df['sim_daysinmonth'])
            del sim_df['sim_daysinmonth']

        else:

            obs_df = pd.DataFrame(data=mean_val_timestep_obs, index=obs_idx, columns=[obs_var_name])
            sim_df = pd.DataFrame(data=mean_val_timestep_sim, index=obs_idx, columns=[sim_var_name])

        # accounting for missing values in time series (and thus missing index values!)
        if verbose: click.echo('VERBOSE: covering missing months in observation or simulation data.')
        obs_df = obs_df.resample('D').mean().fillna(np.nan).resample('M').mean()
        sim_df = sim_df.resample('D').mean().fillna(np.nan).resample('M').mean()  

        # concatenating both dataframes to drop rows with missing values in one of the columns
        # dropping rows with missing values is import because time extents of both files probably do not match
        if verbose: click.echo('VEROBSE: concatenating observed and simulated data.')
        final_df = pd.concat([obs_df, sim_df], axis=1).dropna()

        # computing evaluation metrics
        r = spotpy.objectivefunctions.correlationcoefficient(final_df[obs_var_name].values, final_df[sim_var_name].values)
        rmse = spotpy.objectivefunctions.rmse(final_df[obs_var_name].values, final_df[sim_var_name].values)
        if verbose: click.echo('INFO: correlation coefficient is {}'.format(r))
        if verbose: click.echo('INFO: RMSE is {}'.format(rmse))

        # save metrics to polygon-specific dict
        poly_skill_dict = {'R':round(r, 3),
                           'RMSE': round(rmse, 0)}

        # add polygon-specific dict to 'master' dict
        out_dict[ID] = poly_skill_dict

    # convert 'master' dict to dataframe and store to file
    out_df = pd.DataFrame().from_dict(out_dict).T
    out_df.index.name = shp_id
    click.echo('INFO: storing dictionary to {}.'.format(os.path.join(out, 'output_dict.csv')))
    out_df.to_csv(os.path.join(out, '{}_vs_{}.csv'.format(sim_var_name, obs_var_name)))

    # assign evaluation metrics per polygon to geometry and store to file
    gdf_out = extent_gdf.merge(out_df, on=shp_id)
    click.echo('INFO: storing polygons to {}.'.format(os.path.join(out, 'output_polygons.geojson')))
    gdf_out.to_file(os.path.join(out, '{}_vs_{}.geojson'.format(sim_var_name, obs_var_name)), driver='GeoJSON')

    # plot if specified
    if plot:
        click.echo('INFO: plotting evaluation metrics per polygon.')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 10))
        gdf_out.plot(ax=ax1, column='R', legend=True)
        ax1.set_title('R')
        gdf_out.plot(ax=ax2, column='RMSE', legend=True)
        ax2.set_title('RMSE')
        plt.savefig(os.path.join(out, '{}_vs_{}.png'.format(sim_var_name, obs_var_name)), dpi=300, bbox_inches='tight')

    click.echo('INFO: finished.')





