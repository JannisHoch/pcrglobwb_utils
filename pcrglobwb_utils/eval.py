#!/usr/bin/env python
# coding: utf-8

import pcrglobwb_utils
import pandas as pd
import geopandas as gpd
import xarray as xr
import numpy as np
from shapely.geometry import Point
import multiprocessing as mp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import click
from datetime import datetime
import spotpy
import os

def evaluate_polygons(ID, ply_id, extent_gdf, obs_data, sim_data, obs_var_name, sim_var_name, obs_idx, sim_idx, obs_masks, sim_masks, time_step, anomaly, verbose):
    """[summary]

    Args:
        ID ([type]): [description]
        ply_id ([type]): [description]
        extent_gdf ([type]): [description]
        obs_d ([type]): [description]
        sim_d ([type]): [description]
        obs_var_name ([type]): [description]
        sim_var_name ([type]): [description]
        obs_idx ([type]): [description]
        sim_idx ([type]): [description]
        time_step ([type]): [description]
        ll_pickled_masks
        anomaly ([type]): [description]
        verbose ([type]): [description]

    Returns:
        [type]: [description]
    """    

    if verbose: click.echo('VERBOSE -- evaluating polygon with {} {}'.format(ply_id, ID))

    poly = extent_gdf.loc[extent_gdf[ply_id] == ID]

    poly_geom = poly['geometry'].values

    gdd = {'ID': ID, 'geometry': poly_geom}
    
    # if clip was done in preprocessing, just use these pickled masks
    if isinstance(obs_masks, pd.DataFrame) and isinstance(sim_masks, pd.DataFrame):
        
        if verbose: click.echo('VERBOSE -- using preprocessed mask.')

        # find masks corresponding to evaluated polygon
        obs_masks_ID = obs_masks.loc[obs_masks.index == ID]
        sim_masks_ID = sim_masks.loc[sim_masks.index == ID]

        # if data is found for poly ID (i.e. a non-empty df is returned) for observation and simulation data, unpickle data
        if not obs_masks_ID.empty and not sim_masks_ID.empty: 

            # unpickle these masks
            obs_mask_ID = pcrglobwb_utils.io.unpickle_object(obs_masks_ID.path.values[0])
            sim_mask_ID = pcrglobwb_utils.io.unpickle_object(sim_masks_ID.path.values[0])

            # apply masks
            obs_data_c = xr.where(obs_mask_ID == True, obs_data, np.nan)
            sim_data_c = xr.where(sim_mask_ID == True, sim_data, np.nan)

            final_df = pcrglobwb_utils.utils.concat_dataframes(obs_data_c, sim_data_c, obs_var_name, sim_var_name, obs_idx, sim_idx, time_step, anomaly, verbose)

        # if no data is found for poly ID (i.e. an empty df is returned) for observation data, then create empty dummy df for evaluation later
        elif obs_masks_ID.empty:

            click.echo('INFO -- no mask for observed data found for ID {}, pass.'.format(ID))
            obs_df = pd.DataFrame(data=[np.nan], columns=[obs_var_name])
            sim_df = pd.DataFrame(data=[np.nan], columns=[sim_var_name])
            final_df = pd.concat([obs_df, sim_df], axis=1).dropna()

        # if no data is found for poly ID (i.e. an empty df is returned) for simulation data, then create empty dummy df for evaluation later
        else:

            click.echo('INFO -- no mask for simulated data found for ID {}, pass.'.format(ID))
            obs_df = pd.DataFrame(data=[np.nan], columns=[obs_var_name])
            sim_df = pd.DataFrame(data=[np.nan], columns=[sim_var_name])
            final_df = pd.concat([obs_df, sim_df], axis=1).dropna()

    # if no file with pickled list of pickled masks is provided, clip here on-the-fly
    else:

        if verbose: click.echo('VERBOSE -- clip data to polygon.')

        # clipping data-arrays to shape extent
        obs_data_c = obs_data.rio.clip(poly.geometry, poly.crs, drop=True, all_touched=True)
        sim_data_c = sim_data.rio.clip(poly.geometry, poly.crs, drop=True, all_touched=True)

        final_df = pcrglobwb_utils.utils.concat_dataframes(obs_data_c, sim_data_c, obs_var_name, sim_var_name, obs_idx, sim_idx, time_step, anomaly, verbose)

    metrics_dict = calc_metrics(final_df, obs_var_name, sim_var_name, verbose=verbose)

    gdd['R2'] = round(metrics_dict['R2'], 3)
    gdd['MSE'] = round(metrics_dict['MSE'], 3)
    gdd['RMSE'] = round(metrics_dict['RMSE'], 3)
    gdd['RRMSE'] = round(metrics_dict['RRMSE'], 3)

    return gdd

def POLY(ply, sim, obs, out, ply_id, obs_var_name, sim_var_name, obs_masks=None, sim_masks=None, time_step='monthly', number_processes=None, anomaly=False, conversion_factor=1, coordinate_system='epsg:4326', obs_log=False, sim_log=False, plot=False, verbose=False):

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
    if verbose: click.echo('VERBOSE -- applying conversion factor {} to SIM data'.format(conversion_factor))
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

    if obs_log:
        if verbose: click.echo('VERBOSE -- applying log10 to OBS data')
        obs_data = xr.ufuncs.log10(obs_data)
    if sim_log:
        if verbose: click.echo('VERBOSE -- applying log10 to SIM data')
        sim_data = xr.ufuncs.log10(sim_data)

    # if masks for observations is provided...
    if obs_masks != None:
        # ... check first if there is also one provided for simulations
        if sim_masks != None:
            # unpickle dataframe with polygons IDs and corresponding masks for observations
            obs_masks = os.path.abspath(obs_masks)
            click.echo(click.style('INFO -- reading paths to preprocessed masks from {}'.format(obs_masks), fg='red'))
            obs_masks =  pcrglobwb_utils.io.unpickle_object(obs_masks)
            # unpickle dataframe with polygons IDs and corresponding masks for simulations
            sim_masks = os.path.abspath(sim_masks)
            click.echo(click.style('INFO -- reading paths to preprocessed masks from {}'.format(sim_masks), fg='red'))
            sim_masks = pcrglobwb_utils.io.unpickle_object(sim_masks)
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
        results = [pool.apply_async(evaluate_polygons,args=(ID, ply_id, extent_gdf, obs_data, sim_data, obs_var_name, sim_var_name, obs_idx, sim_idx, obs_masks, sim_masks, time_step, anomaly, verbose)) for ID in poly_list]
        outputList = [p.get() for p in results]

    # otherwise, evaluate polygons without multiprocessing
    else:

        # apply function and retrieve list
        outputList = [evaluate_polygons(ID, ply_id, extent_gdf, obs_data, sim_data, obs_var_name, sim_var_name, obs_idx, sim_idx, obs_masks, sim_masks, time_step, anomaly, verbose) for ID in poly_list]
    
    # write output from list
    pcrglobwb_utils.io.write_output_poly(outputList, sim_var_name, obs_var_name, out, plot)

    t_end = datetime.now()
    delta_t  = t_end - t_start
    
    click.echo(click.style('INFO -- done.', fg='green'))
    click.echo(click.style('INFO -- run time: {}.'.format(delta_t), fg='green'))

def evaluate_stations(station, pcr_ds, out, mode, yaml_root, data, var_name, time_scale, encoding, geojson, plot, verbose):
    """[summary]

    Args:
        station ([type]): [description]
        pcr_ds ([type]): [description]
        out ([type]): [description]
        mode ([type]): [description]
        yaml_root ([type]): [description]
        data ([type]): [description]
        var_name ([type]): [description]
        time_scale ([type]): [description]
        encoding ([type]): [description]
        geojson ([type]): [description]
        plot ([type]): [description]
        verbose ([type]): [description]

    Returns:
        [type]: [description]
    """    
    
    # print some info
    click.echo(click.style('INFO -- validating station {}.'.format(station), fg='cyan'))
    
    # create sub-directory per station
    out_dir = out + '/{}'.format(station)
    pcrglobwb_utils.utils.create_out_dir(out_dir)

    # if data is via yml-file, the data is read here as well as are station properties
    if mode == 'yml': 
        df_obs, props, lat_lon_flag = pcrglobwb_utils.utils.get_data_from_yml(yaml_root, data, station, var_name, encoding, verbose)

    # if data comes from folder, it was already read and can now be retrieved from dictionary
    if mode == 'fld':
        df_obs, props = data[str(station)][1], data[str(station)][0]
        lat_lon_flag = False

    # compute mean value of observations
    df_obs_mean = np.mean(df_obs.dropna().values)

    # prepare a geojson-file for output later (if specified)
    if geojson:
        if verbose: click.echo('VERBOSE -- preparing geo-dict for GeoJSON output')
        gdd = {'station': station, 'geometry': Point(props['longitude'], props['latitude'])}

    # get row/col combination for cell corresponding to lon/lat combination
    if verbose: click.echo('VERBOSE -- getting row/column combination from longitude/latitude.')
    row, col = pcrglobwb_utils.sim_data.find_indices_from_coords(pcr_ds, df_obs_mean, props['longitude'], props['latitude'], lat_lon_flag, var_name=var_name)

    # retrieving values at that cell
    if verbose: click.echo('VERBOSE -- reading variable {} at row {} and column {}.'.format(var_name, row, col))
    df_sim = pcrglobwb_utils.sim_data.read_at_indices(pcr_ds, row, col, var_name=var_name, plot_var_name='SIM')
    df_sim.set_index(pd.to_datetime(df_sim.index), inplace=True)

    df_obs, df_sim = pcrglobwb_utils.time_funcs.resample_ts(df_obs, df_sim, time_scale)

    # compute scores
    click.echo('INFO -- computing scores.')
    df_scores = pcrglobwb_utils.sim_data.validate_timeseries(df_sim, df_obs, out_dir, station, suffix=time_scale, return_all_KGE=False)
    df_scores = df_scores.T

    # update geojson-file with KGE info
    if geojson: 
        # if verbose: click.echo('VERBOSE -- adding station KGE to geo-dict')
        gdd['KGE']   = df_scores['KGE'][0]
        gdd['R2']    = df_scores['R2'][0]
        gdd['NSE']   = df_scores['NSE'][0]
        gdd['MSE']   = df_scores['MSE'][0]
        gdd['RMSE']  = df_scores['RMSE'][0]
        gdd['RRMSE'] = df_scores['RRMSE'][0]

    # make as simple plot of time series if specified and save
    if plot:
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

    return gdd

def GRDC(ncf, out, var_name, yaml_file, folder, grdc_column='discharge', encoding='ISO-8859-1', selection_file=None, time_scale='monthly', geojson=True, plot=False, number_processes=None, verbose=False):

    t_start = datetime.now()

    click.echo(click.style('INFO -- start.', fg='green'))
    click.echo(click.style('INFO -- pcrglobwb_utils version {}.'.format(pcrglobwb_utils.__version__), fg='green'))

    # create main output dir
    out = os.path.abspath(out)
    pcrglobwb_utils.utils.create_out_dir(out)

    # now get started with simulated data
    ncf = os.path.abspath(ncf)
    click.echo(click.style('INFO -- loading simulated data from {}.'.format(ncf), fg='red'))
    pcr_ds = xr.open_dataset(ncf)

    # check if data comes via yml-file or from folder
    mode = pcrglobwb_utils.utils.check_mode(yaml_file, folder)

    # depending on mode, data is read at different stages of this script
    if mode == 'yml':
        data, yaml_root = pcrglobwb_utils.utils.read_yml(yaml_file)
    if mode == 'fld':
        # note that 'data' is in fact a dictionary here!
        data, files = pcrglobwb_utils.utils.glob_folder(folder, grdc_column, verbose, encoding=encoding)
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

        results = [pool.apply_async(evaluate_stations,args=(station, pcr_ds, out, mode, yaml_root, data, var_name, time_scale, encoding, geojson, plot, verbose)) for station in sel_grdc_no]

        outputList = [p.get() for p in results]

    else:

        outputList = [evaluate_stations(station, pcr_ds, out, mode, yaml_root, data, var_name, time_scale, encoding, geojson, plot, verbose) for station in sel_grdc_no]

    pcrglobwb_utils.io.write_output(outputList, time_scale, geojson, out)

    t_end = datetime.now()
    delta_t  = t_end - t_start
        
    click.echo(click.style('INFO -- done.', fg='green'))
    click.echo(click.style('INFO -- run time: {}.'.format(delta_t), fg='green'))

def EXCEL(ncf, xls, loc, out, var_name, location_id, time_scale, plot, geojson, verbose):

    t_start = datetime.now()

    click.echo(click.style('INFO -- start.', fg='green'))
    click.echo(click.style('INFO -- pcrglobwb_utils version {}.'.format(pcrglobwb_utils.__version__), fg='green'))
    click.echo(click.style('INFO -- validating variable {} from file {}'.format(var_name, ncf), fg='red'))
    click.echo(click.style('INFO -- with data from file {}'.format(xls), fg='red'))
    click.echo(click.style('INFO -- using locations from file {}'.format(loc), fg='red'))

    df_obs = pd.read_excel(xls, index_col=0)
    df_obs.set_index(pd.to_datetime(df_obs.index), inplace=True)

    locs = gpd.read_file(loc, driver='GeoJSON')

    # now get started with simulated data
    ncf = os.path.abspath(ncf)
    click.echo('INFO -- loading simulated data from {}.'.format(ncf))
    pcr_data = pcrglobwb_utils.sim_data.from_nc(ncf)

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

def calc_metrics(df: pd.DataFrame, obs_var_name: str, sim_var_name: str, verbose=False, return_all=False) -> dict:
    """Calculates a range of evaluation metrics.
    Both timeseries (i.e., simulation and observation) need to be stored in df.
    Returns metric values as dictionary.

    Args:
        df (pd.DataFrame): dataframe containing simulated and observed values.
        obs_var_name (str): column name of observed values.
        sim_var_name (str): column name of simulated values.
        verbose (bool, optional): whether or not to print more info. Defaults to False.
        return_all (bool, optional): whether or not return all KGE components. Defaults to False.

    Returns:
        dict: dictionary containing metrics with their values.
    """

    # computing evaluation metrics
    kge = spotpy.objectivefunctions.kge(df[obs_var_name].values, df[sim_var_name].values, return_all=return_all)
    kge_np = spotpy.objectivefunctions.kge_non_parametric(df[obs_var_name].values, df[sim_var_name].values, return_all=return_all)
    nse = spotpy.objectivefunctions.nashsutcliffe(df[obs_var_name].values, df[sim_var_name].values)
    r2 = spotpy.objectivefunctions.rsquared(df[obs_var_name].values, df[sim_var_name].values)
    mse = spotpy.objectivefunctions.mse(df[obs_var_name].values, df[sim_var_name].values)
    rmse = spotpy.objectivefunctions.rmse(df[obs_var_name].values, df[sim_var_name].values)
    # rrmse = spotpy.objectivefunctions.rrmse(final_df[obs_var_name].values, final_df[sim_var_name].values) # this RRMSE divides RMSE with mean(eval)
    rrmse = rmse / df[obs_var_name].std()

    if verbose: 
        click.echo('VERBOSE -- KGE is {}'.format(kge))
        click.echo('VERBOSE -- KGE non-parametric is {}'.format(kge_np))
        click.echo('VERBOSE -- NSE is {}'.format(nse))
        click.echo('VERBOSE -- R2 is {}'.format(r2))
        click.echo('VERBOSE -- MSE is {}'.format(mse))
        click.echo('VERBOSE -- RMSE is {}'.format(rmse))
        click.echo('VERBOSE -- RRMSE is {}'.format(rrmse))

    dd = {'KGE': kge, 'KGE_NP': kge_np,'NSE': nse, 'R2': r2, 'MSE': mse, 'RMSE': rmse, 'RRMSE': rrmse}

    dd = {key : round(dd[key], 3) for key in dd}

    return dd
