#!/usr/bin/env python
# coding: utf-8

import pcrglobwb_utils
import click

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

    pcrglobwb_utils.eval.POLY(ply, sim, obs, out, ply_id, obs_var_name, sim_var_name, obs_masks, sim_masks, time_step, number_processes, anomaly, conversion_factor, coordinate_system, plot, verbose)

