#!/usr/bin/env python
# coding: utf-8

import pcrglobwb_utils
from . import funcs
import click
import xarray as xr
import pandas as pd
import numpy as np
from shapely.geometry import Point
import geopandas as gpd
import matplotlib.pyplot as plt
import yaml
import spotpy
import os

@click.group()
@click.option('--version/--no-version', default=False)
@click.pass_context

def cli(ctx, version):

    ctx.ensure_object(dict)
    # ctx.obj['DATA'] = data
    # ctx.obj['NODE_NUMBER'] = node_number
    ctx.obj['VERSION'] = version

    if version: click.echo(click.style('INFO: starting evaluation with pcrglobwb_utils version {}.'.format(pcrglobwb_utils.__version__), fg='green'))

@cli.command()
@click.argument('ncf',)
@click.argument('out',)
@click.option('-v', '--var-name', help='variable name in netCDF-file', default='discharge', type=str)
@click.option('-y', '--yaml-file', default=None, help='path to yaml-file referencing to multiple GRDC-files.', type=str)
@click.option('-f', '--folder', default=None, help='path to folder with GRDC-files.', type=click.Path())
@click.option('-gc', '--grdc-column', default=' Calculated', help='name of column in GRDC file to be read (only used with -f option)', type=str)
@click.option('-t', '--time-scale', default=None, help='time scale at which analysis is performed if upscaling is desired: month, year, quarter', type=str)
@click.option('--geojson/--no-geojson', default=True, help='create GeoJSON file with KGE per GRDC station.')
@click.option('--plot/--no-plot', default=False, help='simple output plots.')
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')
@click.pass_context

def GRDC(ctx, ncf, out, var_name, yaml_file, folder, grdc_column, time_scale, geojson, plot, verbose):
    """Uses pcrglobwb_utils to validate simulated time series (currently only discharge is supported) 
    with observations (currently only GRDC) for one or more stations. The station name and file with GRDC data
    need to be provided in a separate yml-file. Per station, it is also possible to provide lat/lon coordinates
    which will supersede those provided by GRDC.
    The script faciliates resampling to other temporal resolutions.

    Returns a csv-file with the evaluated time series (OBS and SIM), 
    a csv-file with the resulting scores (KGE, r, RMSE, NSE), 
    and if specified a simple plot of the time series.
    If specified, it also returns a geojson-file containing KGE values per station evaluated.

    NCF: Path to the netCDF-file with simulations.
        
    OUT: Main output directory. Per station, a sub-directory will be created.
    """   

    click.echo(click.style('INFO: start.', fg='green'))

    # check if data comes via yml-file or from folder
    mode = funcs.check_mode(yaml_file, folder)

    # depending on mode, data is read at different stages of this script
    if mode == 'yml':
        data, yaml_root = funcs.read_yml(yaml_file)
    if mode == 'fld':
        # note that 'data' is in fact a dictionary here!
        data = funcs.glob_folder(folder, grdc_column, verbose)

    # now get started with simulated data
    click.echo('INFO: loading simulated data from {}.'.format(ncf))
    pcr_data = pcrglobwb_utils.sim_data.from_nc(ncf)

    # prepare a geojson-file for output later (if specified)
    if geojson:
        click.echo('INFO: preparing geo-dict for GeoJSON output')
        geo_dict = {'station': list(), 'KGE': list(), 'geometry': list()}

    all_scores = pd.DataFrame()

    # validate data at each station specified in yml-file
    # or as returned from the all files in folder
    for station in data.keys():

        # print some info
        click.echo(click.style('INFO: validating station {}.'.format(station), fg='cyan'))

        # create sub-directory per station
        out_dir = os.path.abspath(out) + '/{}'.format(station)
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        click.echo('INFO: saving output to folder {}'.format(out_dir))

        # update geojson-file with station info
        if geojson: 
            if verbose: click.echo('VERBOSE: adding station name to geo-dict')
            geo_dict['station'].append(station)

        # if data is via yml-file, the data is read here as well as are station properties
        if mode == 'yml': 

            # construct path to GRDC-file
            grdc_file = os.path.join(yaml_root, data[str(station)]['file'])           
            click.echo('INFO: validating variable {} from file {}'.format(var_name, ncf))
            click.echo('INFO: with observations from file {}.'.format(grdc_file))
        
            click.echo('INFO: loading GRDC data.')
            grdc_data = pcrglobwb_utils.obs_data.grdc_data(grdc_file)

            if verbose: click.echo('VERBOSE: retrieving GRDC station properties.')
            plot_title, props = grdc_data.get_grdc_station_properties()

            # retrieving values from GRDC file
            if 'column' in data[str(station)].keys():
                df_obs, props = grdc_data.get_grdc_station_values(col_name=data[str(station)]['column'], var_name='OBS', verbose=verbose)
            else:
                df_obs, props = grdc_data.get_grdc_station_values(var_name='OBS', verbose=verbose)
            df_obs.set_index(pd.to_datetime(df_obs.index), inplace=True)

            # if 'lat' or 'lon' are specified for a station in yml-file,
            # use this instead of GRDC coordinates
            if 'lat' in data[str(station)].keys():
                click.echo('INFO: overwriting GRDC latitude information {} with user input {}.'.format(props['latitude'], data[str(station)]['lat']))
                props['latitude'] = data[str(station)]['lat']
            if 'lon' in data[str(station)].keys():
                click.echo('INFO: overwriting GRDC longitude information {} with user input {}.'.format(props['longitude'], data[str(station)]['lon']))
                props['longitude'] = data[str(station)]['lon']

        # if data comes from folder, it was already read and can now be retrieved from dictionary
        if mode == 'fld':
            df_obs, props = data[str(station)][1], data[str(station)][0]

        # update geojson-file with geometry info
        if geojson: 
            if verbose: click.echo('VERBOSE: adding station coordinates to geo-dict')
            geo_dict['geometry'].append(Point(props['longitude'], props['latitude']))

        # get row/col combination for cell corresponding to lon/lat combination
        click.echo('INFO: getting row/column combination from longitude/latitude.')
        row, col = pcr_data.find_indices_from_coords(props['longitude'], props['latitude'])

        # retrieving values at that cell
        click.echo('INFO: reading variable {} at row {} and column {}.'.format(var_name, row, col))
        df_sim = pcr_data.read_values_at_indices(row, col, var_name=var_name, plot_var_name='SIM')
        df_sim.set_index(pd.to_datetime(df_sim.index), inplace=True)

        # resample if specified to other time scales
        if time_scale == 'month':
            click.echo('INFO: resampling observed data to monthly time scale.')
            df_obs = df_obs.resample('M', convention='start').mean()
            df_sim = pcr_data.resample2monthly()
        elif time_scale == 'year':
            click.echo('INFO: resampling observed data to yearly time scale.')
            df_obs = df_obs.resample('Y', convention='start').mean()
            df_sim = pcr_data.resample2yearly()
        elif time_scale == 'quarter':
            click.echo('INFO: resampling observed data to quarterly time scale.')
            df_obs = df_obs.resample('Q', convention='start').agg('mean')
            df_sim = pcr_data.resample2quarterly()

        # compute scores
        click.echo('INFO: computing scores.')
        scores = pcr_data.validate_results(df_obs, out_dir=out_dir, suffix=time_scale, return_all_KGE=False)

        # create one dataframe with scores from all stations
        scores.index = [station]
        all_scores = pd.concat([all_scores, scores], axis=0)
        
        # update geojson-file with KGE info
        if geojson: 
            if verbose: click.echo('VERBOSE: adding station KGE to geo-dict')
            geo_dict['KGE'].append(scores['KGE'][0])

        # make as simple plot of time series if specified and save
        if plot:
            if verbose: click.echo('VERBOSE: plotting.')
            fig, ax = plt.subplots(1, 1, figsize=(20,10))
            df_sim.plot(ax=ax, c='r')
            df_obs.plot(ax=ax, c='k')
            ax.set_ylabel('discharge [m3/s]')
            ax.set_xlabel(None)
            plt.legend()
            if time_scale != None:
                plt.savefig(os.path.join(out_dir, 'timeseries_{}.png'.format(time_scale)), bbox_inches='tight', dpi=300)
            else:
                plt.savefig(os.path.join(out_dir, 'timeseries.png'), bbox_inches='tight', dpi=300)

    if time_scale != None:
        click.echo('INFO: saving all scores to {}.'.format(os.path.join(out, 'all_scores_{}.csv'.format(time_scale))))
        all_scores.to_csv(os.path.join(out, 'all_scores_{}.csv'.format(time_scale)))
    else:
        click.echo('INFO: saving all scores to {}.'.format(os.path.join(out, 'all_scores.csv')))
        all_scores.to_csv(os.path.join(out, 'all_scores.csv'))

    # write geojson-file to disc
    if geojson:
        click.echo('INFO: creating geo-dataframe')
        gdf = gpd.GeoDataFrame(geo_dict, crs="EPSG:4326")
        if time_scale != None:
            gdf.to_file(os.path.join(os.path.abspath(out), 'KGE_per_location_{}.geojson'.format(time_scale)), driver='GeoJSON')
        else:
            gdf.to_file(os.path.join(os.path.abspath(out), 'KGE_per_location.geojson'), driver='GeoJSON')

    click.echo(click.style('INFO: done.', fg='green'))

#------------------------------

@cli.command()
@click.argument('ncf',)
@click.argument('xls',)
@click.argument('loc',)
@click.argument('out',)
@click.option('-v', '--var-name', help='variable name in netCDF-file', default='discharge', type=str)
@click.option('-id', '--location-id', help='unique identifier in locations file.', default='name', type=str)
@click.option('-t', '--time-scale', default=None, help='time scale at which analysis is performed if upscaling is desired: month, year, quarter', type=str)
@click.option('--plot/--no-plot', default=False, help='simple output plots.')
@click.option('--geojson/--no-geojson', default=True, help='create GeoJSON file with KGE per GRDC station.')
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')
@click.pass_context

def EXCEL(ctx, ncf, xls, loc, out, var_name, location_id, time_scale, plot, geojson, verbose):
    """Uses pcrglobwb_utils to validate simulated time series
    with observations for one or more stations. The station names and their locations need to be provided via geojson-file.
    Observations are read from Excel-file and analysis will be performed for all stations with matching names in Excel-file columns and geojson-file.
    The Excel-file must have only one sheet with first column being time stamps of observed values, and all other columns are observed values per station.
    These columns must have a header with the station name.
    The script faciliates resampling to other temporal resolutions.

    Returns a csv-file with the evaluated time series (OBS and SIM), 
    a csv-file with the resulting scores (KGE, r, RMSE, NSE), 
    and if specified a simple plot of the time series.
    If specified, it also returns a geojson-file containing KGE values per station evaluated.

    NCF: Path to the netCDF-file with simulations.

    XLS: Path to Excel-file containing dates and values per station.

    LOC: Path to geojson-file containing location and names of stations.
        
    OUT: Main output directory. Per station, a sub-directory will be created.
    """    

    click.echo(click.style('INFO: start.', fg='green'))
    click.echo(click.style('INFO: validating variable {} from file {}'.format(var_name, ncf), fg='red'))
    click.echo(click.style('INFO: with data from file {}'.format(xls), fg='red'))
    click.echo(click.style('INFO: using locations from file {}'.format(loc), fg='red'))

    sim = xr.open_dataset(ncf)

    df_obs = pd.read_excel(xls, index_col=0)
    df_obs.set_index(pd.to_datetime(df_obs.index), inplace=True)

    locs = gpd.read_file(loc, driver='GeoJSON')

    # now get started with simulated data
    click.echo('INFO: loading simulated data from {}.'.format(ncf))
    pcr_data = pcrglobwb_utils.sim_data.from_nc(ncf)

    # prepare a geojson-file for output later (if specified)
    if geojson:
        click.echo('INFO: preparing geo-dict for GeoJSON output')
        geo_dict = {'station': list(), 'KGE': list(), 'geometry': list()}

    all_scores = pd.DataFrame()
    
    for name, i in zip(locs[location_id].unique(), range(len(locs))):

        if name not in df_obs.columns:

            click.echo('WARNING: station not found in Excel-file')

        else:
        
            if verbose: click.echo('VERBOSE: evaluating station with name {}'.format(name))

            # update geojson-file with station info
            if geojson: 
                if verbose: click.echo('VERBOSE: adding station name to geo-dict')
                geo_dict['station'].append(name)

            # create sub-directory per station
            out_dir = os.path.abspath(out) + '/{}'.format(name)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            click.echo('INFO: saving output to folder {}'.format(out_dir))

            click.echo('INFO: retrieving data from Excel-file for column with name of station')
            station_obs = df_obs[str(name)]

            lon = locs[locs[location_id] == name].geometry.x[i]
            lat = locs[locs[location_id] == name].geometry.y[i]
            click.echo('INFO: from geojson-file, retrieved lon/lat combination {}/{}'.format(lon, lat))

            # update geojson-file with geometry info
            if geojson: 
                if verbose: click.echo('VERBOSE: adding station coordinates to geo-dict')
                geo_dict['geometry'].append(Point(lon, lat))

            # get row/col combination for cell corresponding to lon/lat combination
            click.echo('INFO: getting row/column combination from longitude/latitude.')
            row, col = pcr_data.find_indices_from_coords(lon, lat)

            # retrieving values at that cell
            click.echo('INFO: reading variable {} at row {} and column {}.'.format(var_name, row, col))
            df_sim = pcr_data.read_values_at_indices(row, col, var_name=var_name, plot_var_name='SIM')
            df_sim.set_index(pd.to_datetime(df_sim.index), inplace=True)

            # resample if specified to other time scales
            if time_scale == 'month':
                click.echo('INFO: resampling observed data to monthly time scale.')
                station_obs = station_obs.resample('M', convention='start').mean()
                df_sim = pcr_data.resample2monthly()
            elif time_scale == 'year':
                click.echo('INFO: resampling observed data to yearly time scale.')
                station_obs = station_obs.resample('Y', convention='start').mean()
                df_sim = pcr_data.resample2yearly()
            elif time_scale == 'quarter':
                click.echo('INFO: resampling observed data to quarterly time scale.')
                station_obs = station_obs.resample('Q', convention='start').agg('mean')
                df_sim = pcr_data.resample2quarterly()

            # compute scores
            click.echo('INFO: computing scores.')
            scores = pcr_data.validate_results(station_obs, out_dir=out_dir, suffix=time_scale, return_all_KGE=False)

            # create one dataframe with scores from all stations
            scores.index = [name]
            all_scores = pd.concat([all_scores, scores], axis=0)

            # update geojson-file with KGE info
            if geojson: 
                if verbose: click.echo('VERBOSE: adding station KGE to geo-dict')
                geo_dict['KGE'].append(scores['KGE'][0])

            # make as simple plot of time series if specified and save
            if plot:
                if verbose: click.echo('VERBOSE: plotting.')
                fig, ax = plt.subplots(1, 1, figsize=(20,10))
                df_sim.plot(ax=ax, c='r')
                station_obs.plot(ax=ax, c='k')
                ax.set_ylabel('discharge [m3/s]')
                ax.set_xlabel(None)
                plt.legend()
                if time_scale != None:
                    plt.savefig(os.path.join(out_dir, 'timeseries_{}.png'.format(time_scale)), bbox_inches='tight', dpi=300)
                else:
                    plt.savefig(os.path.join(out_dir, 'timeseries.png'), bbox_inches='tight', dpi=300)

    click.echo('INFO: saving all scores to {}.'.format(os.path.join(out, 'all_scores.csv')))
    if time_scale != None:
        all_scores.to_csv(os.path.join(out, 'all_scores_{}.csv'.format(time_scale)))
    else:
        all_scores.to_csv(os.path.join(out, 'all_scores.csv'))

    if geojson:
        click.echo('INFO: creating geo-dataframe')
        gdf = gpd.GeoDataFrame(geo_dict, crs="EPSG:4326")
        if time_scale != None:
            gdf.to_file(os.path.join(os.path.abspath(out), 'KGE_per_location_{}.geojson'.format(time_scale)), driver='GeoJSON')
        else:
            gdf.to_file(os.path.join(os.path.abspath(out), 'KGE_per_location.geojson'), driver='GeoJSON')

    click.echo(click.style('INFO: done.', fg='green'))
#------------------------------

@cli.command()
@click.argument('ply',)
@click.argument('sim',)
@click.argument('obs',)
@click.argument('out',)
@click.option('-id', '--ply-id', help='unique identifier in file containing polygons.', type=str)
@click.option('-o', '--obs_var_name', help='variable name in observations.', type=str)
@click.option('-s', '--sim_var_name', help='variable name in simulations.', type=str)
@click.option('-cf', '--conversion-factor', default=1, help='conversion factor applied to simulated values to align variable units.', type=int)
@click.option('-crs', '--coordinate-system', default='epsg:4326', help='coordinate system.', type=str)
@click.option('--anomaly/--no-anomaly', default=False, help='whether or not to compute anomalies.')
@click.option('--sum/--no-sum', default=False, help='whether or not the simulated values or monthly totals or not.')
@click.option('--plot/--no-plot', default=False, help='whether or not to save a simple plot of results.')
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')
@click.pass_context

def POLY(ctx, ply, sim, obs, out, ply_id, obs_var_name, sim_var_name, sum, anomaly, conversion_factor, coordinate_system, plot, verbose):
    """

    Computes r, MSE, and RMSE for multiple polygons as provided by a shape-file between simulated and observed data.
    Each polygon needs to have a unique ID.
    Contains multiple options to align function settings with data and evaluation properties.

    Returns a GeoJSON-file of r, MSE, and RMSE per polygon, and if specified as simple plot. 
    Also returns scores of r, MSE, and RMSE per polygon as dataframe.
    
    PLY: path to shp-file or geojson-file with one or more polygons.

    SIM: path to netCDF-file with simulated data.

    OBS: path to netCDF-file with observed data.

    OUT: Path to output folder. Will be created if not there yet.

    """    

    click.echo(click.style('INFO: start.', fg='green'))

    # print some info at the beginning
    click.echo(click.style('INFO: validating variable {} from file {}'.format(sim_var_name, sim), fg='red'))
    click.echo(click.style('INFO: with variable {} from file {}'.format(obs_var_name, obs), fg='red'))

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
    print('INFO: reading polygons from file {}'.format(os.path.abspath(ply)))
    try:
        extent_gdf = gpd.read_file(ply, crs=coordinate_system)
    except:
        extent_gdf = gpd.read_file(ply, crs=coordinate_system, driver='GeoJSON')

    # align spatial settings of nc-files to be compatible with geosjon-file or ply-file
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
    # go through all polygons in the ply-file as identfied by a unique ID
    for ID in extent_gdf[ply_id].unique():

        if verbose: click.echo('VERBOSE: computing R and RMSE for polygon with key identifier {}'.format(ID))
        poly = extent_gdf.loc[extent_gdf[ply_id] == ID]

        # clipping obs data-array to shape extent
        obs_data_c = obs_data.rio.clip(poly.geometry, poly.crs, drop=True, all_touched=True)
        # clipping sim data-array to shape extent
        sim_data_c = sim_data.rio.clip(poly.geometry, poly.crs, drop=True, all_touched=True)

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
            sim_df = pd.DataFrame(data=mean_val_timestep_sim, index=sim_idx, columns=[sim_var_name])

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
        mse = spotpy.objectivefunctions.mse(final_df[obs_var_name].values, final_df[sim_var_name].values)
        rmse = spotpy.objectivefunctions.rmse(final_df[obs_var_name].values, final_df[sim_var_name].values)
        if verbose: click.echo('INFO: correlation coefficient is {}'.format(r))
        if verbose: click.echo('INFO: Mean Squared Error is {}'.format(mse))
        if verbose: click.echo('INFO: Root Mean Squared Error is {}'.format(rmse))

        # save metrics to polygon-specific dict
        poly_skill_dict = {'R': round(r, 3),
                           'MSE': round(mse, 1),
                           'RMSE': round(rmse, 1)}

        # add polygon-specific dict to 'master' dict
        out_dict[ID] = poly_skill_dict

    # convert 'master' dict to dataframe and store to file
    out_df = pd.DataFrame().from_dict(out_dict).T
    out_df.index.name = ply_id
    click.echo('INFO: storing dictionary to {}.'.format(os.path.join(out, 'output_dict.csv')))
    out_df.to_csv(os.path.join(out, '{}_vs_{}.csv'.format(sim_var_name, obs_var_name)))

    # assign evaluation metrics per polygon to geometry and store to file
    gdf_out = extent_gdf.merge(out_df, on=ply_id)
    click.echo('INFO: storing polygons to {}.'.format(os.path.join(out, 'output_polygons.geojson')))
    gdf_out.to_file(os.path.join(out, '{}_vs_{}.geojson'.format(sim_var_name, obs_var_name)), driver='GeoJSON')

    # plot if specified
    if plot:
        click.echo('INFO: plotting evaluation metrics per polygon.')
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 10))
        gdf_out.plot(ax=ax1, column='R', legend=True)
        ax1.set_title('R')
        gdf_out.plot(ax=ax2, column='MSE', legend=True)
        ax2.set_title('MSE')
        gdf_out.plot(ax=ax3, column='RMSE', legend=True)
        ax3.set_title('RMSE')
        plt.savefig(os.path.join(out, '{}_vs_{}.png'.format(sim_var_name, obs_var_name)), dpi=300, bbox_inches='tight')

    click.echo(click.style('INFO: done.', fg='green'))

#------------------------------