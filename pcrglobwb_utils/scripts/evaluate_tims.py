#!/usr/bin/env python
# coding: utf-8

import pcrglobwb_utils
import click

@click.group()
def cli():

    return

@cli.command()
@click.argument('ncf',)
@click.argument('data_loc')
@click.argument('out',)
@click.option('-v', '--var-name', help='variable name in netCDF-file', default='discharge', type=str)
@click.option('-gc', '--grdc-column', default=' Calculated', help='name of column in GRDC file to be read (only used with -f option)', type=str)
@click.option('-w', '--window', default=5, help='size of search window to be applied.', type=int)
@click.option('-e', '--encoding', default='ISO-8859-1', help='encoding of GRDC-files.', type=str)
@click.option('-sf', '--selection-file', default=None, help='path to file produced by pcru_sel_grdc function (only used with -f option)', type=str)
@click.option('-t', '--time-scale', default=None, help='time scale at which analysis is performed if resampling is desired. String needs to follow pandas conventions.', type=str)
@click.option('-N', '--number-processes', default=None, help='number of processes to be used in multiprocessing.Pool()- defaults to number of CPUs in the system.', type=int)
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')

def GRDC(ncf, var_name, out, data_loc, grdc_column, window, encoding, selection_file, time_scale, number_processes, verbose):
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

    DATA_LOC: either yaml-file or folder with GRDC files.
        
    OUT: Main output directory. Per station, a sub-directory will be created.
    """   

    pcrglobwb_utils.eval.GRDC(ncf, out, var_name, data_loc, grdc_column=grdc_column, search_window=window, encoding=encoding, selection_file=selection_file, time_scale=time_scale, number_processes=number_processes, verbose=verbose)

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

    pcrglobwb_utils.eval.EXCEL(ncf, xls, loc, out, var_name, location_id, time_scale, plot, geojson, verbose)
#------------------------------