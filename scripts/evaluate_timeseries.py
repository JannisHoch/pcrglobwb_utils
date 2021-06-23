#!/usr/bin/env python
# coding: utf-8

import pcrglobwb_utils
import click
import pandas as pd
import matplotlib.pyplot as plt
import os

@click.group()
def cli():
    pass

@click.command()
@click.argument('ncf',)
@click.argument('out_dir',)
@click.option('-v', '--var-name', help='variable name in netCDF-file', default='discharge', type=str)
@click.option('-g', '--grdc-file', default=None, help='path to GRDC file.', type=str)
@click.option('-e', '--excel-file', default=None, help='path to Excel file.', type=str)
@click.option('-y', '--yaml-file', default=None, help='path to yaml-file referencing to multiple GRDC/Excel-files.', type=str)
@click.option('-lat', '--latitude', default=None, help='latitude in degree', type=float)
@click.option('-lon', '--longitude', default=None, help='longitude in degree', type=float)
@click.option('-t', '--time-scale', default=None, help='time scale at which analysis is performed if upscaling is desired: month, year, quarter', type=str)
@click.option('--plot/--no-plot', default=False, help='simple output plots.')
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')

def main(ncf, out_dir, var_name, grdc_file, excel_file, yaml_file, latitude, longitude, time_scale, plot, verbose):

    # get full path name of output-dir and create it if not there yet
    out_dir = os.path.abspath(out_dir)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    click.echo('INFO: saving output to folder {}'.format(out_dir))
    
    click.echo('INFO: loading GRDC data from file {}.'.format(grdc_file))
    grdc_data = pcrglobwb_utils.obs_data.grdc_data(grdc_file)

    if verbose: click.echo('VERBOSE: retrieving GRDC station properties.')
    plot_title, props = grdc_data.get_grdc_station_properties()

    if latitude != None:
        click.echo('INFO: overwriting GRDC latitude information {} with user input {}.'.format(props['latitude'], latitude))
        props['latitude'] = latitude
    if longitude != None:
        click.echo('INFO: overwriting GRDC longitude information {} with user input {}.'.format(props['longitude'], longitude))
        props['longitude'] = longitude

    df_obs, props = grdc_data.get_grdc_station_values(var_name='OBS')

    click.echo('INFO: loading simulated data from {}.'.format(ncf))
    pcr_data = pcrglobwb_utils.sim_data.from_nc(ncf)

    click.echo('INFO: getting row/column combination from longitude/latitude.')
    row, col = pcrglobwb_utils.utils.find_indices_from_coords(ncf, 
                                                              lon=props['longitude'], 
                                                              lat=props['latitude'])

    click.echo('INFO: reading variable {} at row {} and column {}.'.format(var_name, row, col))
    df_sim = pcr_data.read_values_at_indices(row, col, var_name=var_name, plot_var_name='SIM')

    if time_scale == 'month':
        click.echo('INFO: resampling data to monthly time scale')
        df_sim = df_sim.resample('M', convention='start').mean()
        df_obs = df_obs.resample('M', convention='start').mean()
    if time_scale == 'year':
        click.echo('INFO: resampling data to yearly time scale')
        df_sim = df_sim.resample('Y', convention='start').mean()
        df_obs = df_obs.resample('Y', convention='start').mean()
    if time_scale == 'quarter':
        click.echo('INFO: resampling data to quarterly time scale')
        df_sim = df_sim.resample('Q', convention='start').agg('mean')
        df_obs = df_obs.resample('Q', convention='start').agg('mean')

    click.echo('INFO: computing scores.')
    pcr_data.validate_results(df_obs, out_dir=out_dir, suffix=time_scale, return_all_KGE=False)

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
if __name__ == '__main__':
    main()

