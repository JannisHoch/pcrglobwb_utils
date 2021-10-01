#!/usr/bin/env python
# coding: utf-8

import pcrglobwb_utils
from . import funcs
import click
import xarray as xr
import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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
@click.option('-e', '--encoding', default='ISO-8859-1', help='encoding of GRDC-files.', type=str)
@click.option('-t', '--time-scale', default=None, help='time scale at which analysis is performed if upscaling is desired: month, year, quarter', type=str)
@click.option('--geojson/--no-geojson', default=True, help='create GeoJSON file with KGE per GRDC station.')
@click.option('--plot/--no-plot', default=False, help='simple output plots.')
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')
@click.pass_context

def GRDC(ctx, ncf, out, var_name, yaml_file, folder, grdc_column, encoding, time_scale, geojson, plot, verbose):
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
        data = funcs.glob_folder(folder, grdc_column, verbose, encoding=encoding)

    # now get started with simulated data
    click.echo('INFO: loading simulated data from {}.'.format(ncf))
    pcr_data = pcrglobwb_utils.sim_data.from_nc(ncf)

    # prepare a geojson-file for output later (if specified)
    if geojson:
        click.echo('INFO: preparing geo-dict for GeoJSON output')
        geo_dict = {'station': list(), 'KGE': list(), 'R2': list(), 'MSE': list(), 'RMSE': list(), 'geometry': list()}

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
            plot_title, props = grdc_data.get_grdc_station_properties(encoding=encoding)

            # retrieving values from GRDC file
            if 'column' in data[str(station)].keys():
                df_obs, props = grdc_data.get_grdc_station_values(col_name=data[str(station)]['column'], var_name='OBS', encoding=encoding, verbose=verbose)
            else:
                df_obs, props = grdc_data.get_grdc_station_values(var_name='OBS', verbose=verbose, encoding=encoding)
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
            geo_dict['R2'].append(scores['R2'][0])
            geo_dict['MSE'].append(scores['MSE'][0])
            geo_dict['RMSE'].append(scores['RMSE'][0])

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
            gdf.to_file(os.path.join(os.path.abspath(out), 'scores_per_location_{}.geojson'.format(time_scale)), driver='GeoJSON')
        else:
            gdf.to_file(os.path.join(os.path.abspath(out), 'scores_per_location.geojson'), driver='GeoJSON')

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
    a csv-file with the resulting scores (KGE, R2, RMSE, NSE), 
    and if specified a simple plot of the time series.
    If specified, it also returns a geojson-file containing KGE and R2 values per station evaluated.

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
        geo_dict = {'station': list(), 'KGE': list(), 'R2': list(), 'geometry': list()}

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
                if verbose: click.echo('VERBOSE: adding station validation metrics to geo-dict')
                geo_dict['KGE'].append(scores['KGE'][0])
                geo_dict['R2'].append(scores['R2'][0])

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
            gdf.to_file(os.path.join(os.path.abspath(out), 'scores_per_location_{}.geojson'.format(time_scale)), driver='GeoJSON')
        else:
            gdf.to_file(os.path.join(os.path.abspath(out), 'scores_per_location.geojson'), driver='GeoJSON')

    click.echo(click.style('INFO: done.', fg='green'))
#------------------------------