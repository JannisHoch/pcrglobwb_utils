#!/usr/bin/env python
# coding: utf-8

from pcrglobwb_utils import sim_data, utils, __version__
from . import funcs
import click
import xarray as xr
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import multiprocessing as mp
from datetime import datetime
from shapely.geometry import Point
import os

@click.group()
def cli():

    return

@cli.command()
@click.argument('ncf',)
@click.argument('out',)
@click.option('-v', '--var-name', help='variable name in netCDF-file', default='discharge', type=str)
@click.option('-y', '--yaml-file', default=None, help='path to yaml-file referencing to multiple GRDC-files.', type=str)
@click.option('-f', '--folder', default=None, help='path to folder with GRDC-files.', type=click.Path())
@click.option('-gc', '--grdc-column', default=' Calculated', help='name of column in GRDC file to be read (only used with -f option)', type=str)
@click.option('-e', '--encoding', default='ISO-8859-1', help='encoding of GRDC-files.', type=str)
@click.option('-sf', '--selection-file', default=None, help='path to file produced by pcru_sel_grdc function (only used with -f option)', type=str)
@click.option('-t', '--time-scale', default=None, help='time scale at which analysis is performed if upscaling is desired: month, year, quarter', type=str)
@click.option('-N', '--number-processes', default=None, help='number of processes to be used in multiprocessing.Pool()- defaults to number of CPUs in the system.', type=int)
@click.option('--geojson/--no-geojson', default=True, help='create GeoJSON file with KGE per GRDC station.')
@click.option('--plot/--no-plot', default=False, help='simple output plots.')
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')

def GRDC(ncf, out, var_name, yaml_file, folder, grdc_column, encoding, selection_file, time_scale, geojson, plot, number_processes, verbose):
    """Uses pcrglobwb_utils to validate simulated time series (currently only discharge is supported) 
    with observations (currently only GRDC) for one or more stations. The station name and file with GRDC data
    need to be provided in a separate yml-file. Per station, it is also possible to provide lat/lon coordinates
    which will supersede those provided by GRDC.
    The script faciliates resampling to other temporal resolutions.

    Returns a csv-file with the evaluated time series (OBS and SIM), 
    a csv-file with the resulting scores (KGE, R2, RMSE, RRMSE, NSE), 
    and if specified a simple plot of the time series.
    If specified, it also returns a geojson-file containing KGE values per station evaluated.

    NCF: Path to the netCDF-file with simulations.
        
    OUT: Main output directory. Per station, a sub-directory will be created.
    """   

    t_start = datetime.now()

    click.echo(click.style('INFO -- start.', fg='green'))
    click.echo(click.style('INFO -- pcrglobwb_utils version {}.'.format(__version__), fg='green'))

    # create main output dir
    out = os.path.abspath(out)
    utils.create_out_dir(out)

    # now get started with simulated data
    click.echo(click.style('INFO -- loading simulated data from {}.'.format(ncf), fg='red'))
    pcr_ds = xr.open_dataset(ncf)

    # check if data comes via yml-file or from folder
    mode = utils.check_mode(yaml_file, folder)

    # depending on mode, data is read at different stages of this script
    if mode == 'yml':
        data, yaml_root = utils.read_yml(yaml_file)
    if mode == 'fld':
        # note that 'data' is in fact a dictionary here!
        data, files = utils.glob_folder(folder, grdc_column, verbose, encoding=encoding)
        yaml_root = None

    # if specified, getting station numbers of selected stations
    if (selection_file != None) and (mode == 'fld'):
        
        click.echo('INFO -- reading selected GRDC No.s from {}.'.format(os.path.abspath(selection_file)))
        selection_file = os.path.abspath(selection_file)

        with open(selection_file) as file:
            sel_grdc_no = file.readlines()
            sel_grdc_no = [line.rstrip() for line in sel_grdc_no]

    # otherwise, all stations in folder or yml-file are considered
    else:

        sel_grdc_no = data.keys()

    if not sel_grdc_no:
        raise Warning('WARNING: no stations selected to be evaluated!')

    if number_processes != None:

        min_number_processes = min(number_processes, len(sel_grdc_no), mp.cpu_count())
        if number_processes > min_number_processes: 
            click.echo('INFO -- number of CPUs reduced to {}'.format(min_number_processes))
        else:
            click.echo('INFO -- using {} CPUs for multiprocessing'.format(min_number_processes))
        pool = mp.Pool(processes=min_number_processes)

        results = [pool.apply_async(funcs.evaluate_stations,args=(station, pcr_ds, out, mode, yaml_root, data, var_name, time_scale, encoding, geojson, plot, verbose)) for station in sel_grdc_no]

        outputList = [p.get() for p in results]

    else:

        outputList = [funcs.evaluate_stations(station, pcr_ds, out, mode, yaml_root, data, var_name, time_scale, encoding, geojson, plot, verbose) for station in sel_grdc_no]

    funcs.write_output(outputList, time_scale, geojson, out)

    t_end = datetime.now()
    delta_t  = t_end - t_start
        
    click.echo(click.style('INFO -- done.', fg='green'))
    click.echo(click.style('INFO -- run time: {}.'.format(delta_t), fg='green'))

#------------------------------

@cli.command()
@click.argument('ncf',)
@click.argument('xls',)
@click.argument('loc',)
@click.argument('out',)
@click.option('-v', '--var-name', help='variable name in netCDF-file', default='discharge', type=str)
@click.option('-id', '--location-id', help='unique identifier in locations file.', default='name', type=str)
@click.option('-t', '--time-scale', default=None, help='time scale at which analysis is performed if upscaling is desired: month, year', type=str)
@click.option('--plot/--no-plot', default=False, help='simple output plots.')
@click.option('--geojson/--no-geojson', default=True, help='create GeoJSON file with KGE per GRDC station.')
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')
@click.pass_context

def EXCEL(ncf, xls, loc, out, var_name, location_id, time_scale, plot, geojson, verbose):
    """Uses pcrglobwb_utils to validate simulated time series
    with observations for one or more stations. The station names and their locations need to be provided via geojson-file.
    Observations are read from Excel-file and analysis will be performed for all stations with matching names in Excel-file columns and geojson-file.
    The Excel-file must have only one sheet with first column being time stamps of observed values, and all other columns are observed values per station.
    These columns must have a header with the station name.
    The script faciliates resampling to other temporal resolutions.

    Returns a csv-file with the evaluated time series (OBS and SIM), 
    a csv-file with the resulting scores (KGE, R2, RMSE, RRMSE, NSE), 
    and if specified a simple plot of the time series.
    If specified, it also returns a geojson-file containing KGE and R2 values per station evaluated.

    NCF: Path to the netCDF-file with simulations.

    XLS: Path to Excel-file containing dates and values per station.

    LOC: Path to geojson-file containing location and names of stations.
        
    OUT: Main output directory. Per station, a sub-directory will be created.
    """    

    t_start = datetime.now()

    click.echo(click.style('INFO -- start.', fg='green'))
    click.echo(click.style('INFO -- validating variable {} from file {}'.format(var_name, ncf), fg='red'))
    click.echo(click.style('INFO -- with data from file {}'.format(xls), fg='red'))
    click.echo(click.style('INFO -- using locations from file {}'.format(loc), fg='red'))

    df_obs = pd.read_excel(xls, index_col=0)
    df_obs.set_index(pd.to_datetime(df_obs.index), inplace=True)

    locs = gpd.read_file(loc, driver='GeoJSON')

    # now get started with simulated data
    click.echo('INFO -- loading simulated data from {}.'.format(ncf))
    pcr_data = sim_data.from_nc(ncf)

    # prepare a geojson-file for output later (if specified)
    if geojson:
        click.echo('INFO -- preparing geo-dict for GeoJSON output')
        geo_dict = {'station': list(), 'KGE': list(), 'R2': list(), 'NSE': list(), 'MSE': list(), 'RMSE': list(), 'RRMSE': list(), 'geometry': list()}

    all_scores = pd.DataFrame()
    
    for name, i in zip(locs[location_id].unique(), range(len(locs))):

        if name not in df_obs.columns:

            click.echo('WARNING: station not found in Excel-file')

        else:
        
            if verbose: click.echo('VERBOSE -- evaluating station with name {}'.format(name))

            # update geojson-file with station info
            if geojson: 
                if verbose: click.echo('VERBOSE -- adding station name to geo-dict')
                geo_dict['station'].append(name)

            # create sub-directory per station
            out_dir = os.path.abspath(out) + '/{}'.format(name)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            click.echo('INFO -- saving output to folder {}'.format(out_dir))

            click.echo('INFO -- retrieving data from Excel-file for column with name of station')
            station_obs = df_obs[str(name)]

            lon = locs[locs[location_id] == name].geometry.x[i]
            lat = locs[locs[location_id] == name].geometry.y[i]
            click.echo('INFO -- from geojson-file, retrieved lon/lat combination {}/{}'.format(lon, lat))

            # update geojson-file with geometry info
            if geojson: 
                if verbose: click.echo('VERBOSE -- adding station coordinates to geo-dict')
                geo_dict['geometry'].append(Point(lon, lat))

            # get row/col combination for cell corresponding to lon/lat combination
            click.echo('INFO -- getting row/column combination from longitude/latitude.')
            row, col = pcr_data.get_indices(lon, lat)

            # retrieving values at that cell
            click.echo('INFO -- reading variable {} at row {} and column {}.'.format(var_name, row, col))
            df_sim = pcr_data.get_values(row, col, var_name=var_name, plot_var_name='SIM')
            df_sim.set_index(pd.to_datetime(df_sim.index), inplace=True)

            # resample if specified to other time scales
            if time_scale == 'month':
                click.echo('INFO -- resampling observed data to monthly time scale.')
                station_obs = station_obs.resample('M', convention='start').mean()
                df_sim = pcr_data.resample2monthly()
            elif time_scale == 'year':
                click.echo('INFO -- resampling observed data to yearly time scale.')
                station_obs = station_obs.resample('Y', convention='start').mean()
                df_sim = pcr_data.resample2yearly()
            elif time_scale == 'quarter':
                click.echo('INFO -- resampling observed data to quarterly time scale.')
                station_obs = station_obs.resample('Q', convention='start').agg('mean')
                df_sim = pcr_data.resample2quarterly()

            # compute scores
            click.echo('INFO -- computing scores.')
            scores = pcr_data.validate(station_obs, out_dir=out_dir, suffix=time_scale, return_all_KGE=False)

            # create one dataframe with scores from all stations
            scores.index = [name]
            all_scores = pd.concat([all_scores, scores], axis=0)

            # update geojson-file with KGE info
            if geojson: 
                if verbose: click.echo('VERBOSE -- adding station validation metrics to geo-dict')
                geo_dict['KGE'].append(scores['KGE'][0])
                geo_dict['R2'].append(scores['R2'][0])
                geo_dict['NSE'].append(scores['NSE'][0])
                geo_dict['MSE'].append(scores['MSE'][0])
                geo_dict['RMSE'].append(scores['RMSE'][0])
                geo_dict['RRMSE'].append(scores['RRMSE'][0])

            # make as simple plot of time series if specified and save
            if plot:
                if verbose: click.echo('VERBOSE -- plotting.')
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

    click.echo('INFO -- saving all scores to {}.'.format(os.path.join(out, 'all_scores.csv')))
    if time_scale != None:
        all_scores.to_csv(os.path.join(out, 'all_scores_{}.csv'.format(time_scale)))
    else:
        all_scores.to_csv(os.path.join(out, 'all_scores.csv'))

    if geojson:
        click.echo('INFO -- creating geo-dataframe')
        gdf = gpd.GeoDataFrame(geo_dict, crs="EPSG:4326")
        if time_scale != None:
            gdf.to_file(os.path.join(os.path.abspath(out), 'scores_per_location_{}.geojson'.format(time_scale)), driver='GeoJSON')
        else:
            gdf.to_file(os.path.join(os.path.abspath(out), 'scores_per_location.geojson'), driver='GeoJSON')

    t_end = datetime.now()
    delta_t  = t_end - t_start

    click.echo(click.style('INFO -- done.', fg='green'))
    click.echo(click.style('INFO -- run time: {}.'.format(delta_t), fg='green'))
#------------------------------