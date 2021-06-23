#!/usr/bin/env python
# coding: utf-8

import pcrglobwb_utils
import click
import pandas as pd
import matplotlib.pyplot as plt
import yaml
import os

@click.command()
@click.argument('ncf',)
@click.argument('out',)
@click.option('-v', '--var-name', help='variable name in netCDF-file', default='discharge', type=str)
@click.option('-y', '--yaml-file', default=None, help='path to yaml-file referencing to multiple GRDC-files.', type=str)
@click.option('-t', '--time-scale', default=None, help='time scale at which analysis is performed if upscaling is desired: month, year, quarter', type=str)
@click.option('--plot/--no-plot', default=False, help='simple output plots.')
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')

def cli(ncf, out, var_name, yaml_file, time_scale, plot, verbose):
    """Uses pcrglobwb_utils to validate simulated time series (currently only discharge is supported) 
    with observations (currently only GRDC) for one or more stations. The station name and file with GRDC data
    need to be provided in a separate yml-file. Per station, it is also possible to provide lat/lon coordinates
    which will supersede those provided by GRDC.
    The script faciliates resampling to other temporal resolutions.

    Returns a csv-file with the evaluated time series (OBS and SIM), 
    a csv-file with the resulting scores (KGE, r, RMSE, NSE), 
    and if specified a simple plot of the time series.

    NCF: Path to the netCDF-file with simulations.
        
    OUT: Main output directory. Per station, a sub-directory will be created.
    """    

    # get path to yml-file containing GRDC station info
    yaml_file = os.path.abspath(yaml_file)
    click.echo('INFO: parsing GRDC station information from file {}'.format(yaml_file))
    # get content of yml-file
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    # get location of yml-file
    yaml_root = os.path.dirname(yaml_file)

    # validate data at each station specified in yml-file
    for station in data.keys():

        # construct path to GRDC-file for this station
        grdc_file = os.path.join(yaml_root, data[str(station)]['file'])

        # print some info at the beginning
        click.echo('\n')
        click.echo('INFO: validating station {}.'.format(station))
        click.echo('INFO: validating variable {} from file {}'.format(var_name, ncf))
        click.echo('INFO: with observations from file {}.'.format(grdc_file))
        
        # create sub-directory per station
        out_dir = os.path.abspath(out) + '/{}'.format(station)
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        click.echo('INFO: saving output to folder {}'.format(out_dir))

        click.echo('INFO: loading GRDC data.')
        grdc_data = pcrglobwb_utils.obs_data.grdc_data(grdc_file)

        if verbose: click.echo('VERBOSE: retrieving GRDC station properties.')
        plot_title, props = grdc_data.get_grdc_station_properties()

        # retrieving values from GRDC file
        df_obs, props = grdc_data.get_grdc_station_values(var_name='OBS')

        click.echo('INFO: loading simulated data from {}.'.format(ncf))
        pcr_data = pcrglobwb_utils.sim_data.from_nc(ncf)

        # if 'lat' or 'lon' are specified for a station in yml-file,
        # use this instead of GRDC coordinates
        if 'lat' in data[str(station)].keys():
            click.echo('INFO: overwriting GRDC latitude information {} with user input {}.'.format(props['latitude'], data[str(station)]['lat']))
            props['latitude'] = data[str(station)]['lat']
        if 'lon' in data[str(station)].keys():
            click.echo('INFO: overwriting GRDC longitude information {} with user input {}.'.format(props['longitude'], data[str(station)]['lon']))
            props['longitude'] = data[str(station)]['lon']

        # get row/col combination for cell corresponding to lon/lat combination
        click.echo('INFO: getting row/column combination from longitude/latitude.')
        row, col = pcrglobwb_utils.utils.find_indices_from_coords(ncf, 
                                                                  lon=props['longitude'], 
                                                                  lat=props['latitude'])

        # retrieving values at that cell
        click.echo('INFO: reading variable {} at row {} and column {}.'.format(var_name, row, col))
        df_sim = pcr_data.read_values_at_indices(row, col, var_name=var_name, plot_var_name='SIM')

        # resample if specified to other time scales
        if time_scale == 'month':
            click.echo('INFO: resampling data to monthly time scale.')
            df_sim = df_sim.resample('M', convention='start').mean()
            df_obs = df_obs.resample('M', convention='start').mean()
        if time_scale == 'year':
            click.echo('INFO: resampling data to yearly time scale.')
            df_sim = df_sim.resample('Y', convention='start').mean()
            df_obs = df_obs.resample('Y', convention='start').mean()
        if time_scale == 'quarter':
            click.echo('INFO: resampling data to quarterly time scale.')
            df_sim = df_sim.resample('Q', convention='start').agg('mean')
            df_obs = df_obs.resample('Q', convention='start').agg('mean')

        # compute scores
        click.echo('INFO: computing scores.')
        pcr_data.validate_results(df_obs, out_dir=out_dir, suffix=time_scale, return_all_KGE=False)

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
