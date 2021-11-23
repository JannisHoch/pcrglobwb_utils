
from pcrglobwb_utils import sim_data, obs_data, time_funcs, utils
import pandas as pd
import xarray as xr
import geopandas as gpd
import numpy as np
from shapely.geometry import Point
import matplotlib.pyplot as plt
import click
import rioxarray
import pickle
import spotpy
import os

def evaluate_polygons(ID, ply_id, extent_gdf, obs_d, sim_d, obs_var_name, sim_var_name, obs_idx, sim_idx, obs_masks, sim_masks, time_step, anomaly, verbose):
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

    if verbose: click.echo('VERBOSE -- preparing geo-dict for GeoJSON output')
    gdd = {'ID': ID, 'geometry': poly_geom}
    
    # if clip was done in preprocessing, just use these pickled masks
    if isinstance(obs_masks, pd.DataFrame) and isinstance(sim_masks, pd.DataFrame):
        
        if verbose: click.echo('VERBOSE -- using preprocessed mask.')

        # find masks corresponding to evaluated polygon
        obs_masks_ID = obs_masks.loc[obs_masks.index == ID]
        sim_masks_ID = sim_masks.loc[sim_masks.index == ID]

        # unpickle these masks
        obs_mask_ID = unpickle_object(obs_masks_ID.path.values[0])
        sim_mask_ID = unpickle_object(sim_masks_ID.path.values[0])

        # apply masks
        obs_data_c = xr.where(obs_mask_ID == True, obs_d, np.nan)
        sim_data_c = xr.where(sim_mask_ID == True, sim_d, np.nan)

    # if no file with pickled list of pickled masks is provided, clip here on-the-fly
    else:

        if verbose: click.echo('VERBOSE -- clip data to polygon.')

        # clipping data-arrays to shape extent
        obs_data_c = obs_d.rio.clip(poly.geometry, poly.crs, drop=True, all_touched=True)
        sim_data_c = sim_d.rio.clip(poly.geometry, poly.crs, drop=True, all_touched=True)
    
    # initiate output lists
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
        if verbose: click.echo('VERBOSE -- determine anomalies.')
        mean_val_timestep_obs = mean_val_timestep_obs - np.mean(mean_val_timestep_obs)
        mean_val_timestep_sim = mean_val_timestep_sim - np.mean(mean_val_timestep_sim)

    obs_df = pd.DataFrame(data=mean_val_timestep_obs, index=obs_idx, columns=[obs_var_name])
    sim_df = pd.DataFrame(data=mean_val_timestep_sim, index=sim_idx, columns=[sim_var_name])

    # accounting for missing values in time series (and thus missing index values!)
    if time_step == 'monthly':
        if verbose: click.echo('VERBOSE -- covering missing months in observation or simulation data.')
        obs_df = obs_df.resample('D').mean().fillna(np.nan).resample('M').mean()
        sim_df = sim_df.resample('D').mean().fillna(np.nan).resample('M').mean()  
    if time_step == 'annual':
        if verbose: click.echo('VERBOSE -- covering missing years in observation or simulation data.')
        obs_df = obs_df.resample('D').mean().fillna(np.nan).resample('Y').mean()
        sim_df = sim_df.resample('D').mean().fillna(np.nan).resample('Y').mean()  

    # concatenating both dataframes to drop rows with missing values in one of the columns
    # dropping rows with missing values is import because time extents of both files probably do not match
    if verbose: click.echo('VERBOSE -- concatenating observed and simulated data.')
    final_df = pd.concat([obs_df, sim_df], axis=1).dropna()

    # computing evaluation metrics
    r2 = spotpy.objectivefunctions.rsquared(final_df[obs_var_name].values, final_df[sim_var_name].values)
    mse = spotpy.objectivefunctions.mse(final_df[obs_var_name].values, final_df[sim_var_name].values)
    rmse = spotpy.objectivefunctions.rmse(final_df[obs_var_name].values, final_df[sim_var_name].values)
    rrmse = spotpy.objectivefunctions.rrmse(final_df[obs_var_name].values, final_df[sim_var_name].values)
    if verbose: click.echo('VERBOSE -- R2 is {}'.format(r2))
    if verbose: click.echo('VERBOSE -- MSE is {}'.format(mse))
    if verbose: click.echo('VERBOSE -- RMSE is {}'.format(rmse))
    if verbose: click.echo('VERBOSE -- RRMSE is {}'.format(rrmse))

    gdd['R2'] = round(r2, 3)
    gdd['MSE'] = round(mse, 3)
    gdd['RMSE'] = round(rmse, 3)
    gdd['RRMSE'] = round(rrmse, 3)

    return gdd

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
    utils.create_out_dir(out_dir)

    # if data is via yml-file, the data is read here as well as are station properties
    if mode == 'yml': 
        df_obs, props = get_data_from_yml(yaml_root, data, station, var_name, encoding, verbose)

    # if data comes from folder, it was already read and can now be retrieved from dictionary
    if mode == 'fld':
        df_obs, props = data[str(station)][1], data[str(station)][0]

    # prepare a geojson-file for output later (if specified)
    if geojson:
        if verbose: click.echo('VERBOSE -- preparing geo-dict for GeoJSON output')
        gdd = {'station': station, 'geometry': Point(props['longitude'], props['latitude'])}

    # get row/col combination for cell corresponding to lon/lat combination
    if verbose: click.echo('VERBOSE -- getting row/column combination from longitude/latitude.')
    row, col = sim_data.find_indices_from_coords(pcr_ds, props['longitude'], props['latitude'])

    # retrieving values at that cell
    if verbose: click.echo('VERBOSE -- reading variable {} at row {} and column {}.'.format(var_name, row, col))
    df_sim = sim_data.read_at_indices(pcr_ds, row, col, var_name=var_name, plot_var_name='SIM')
    df_sim.set_index(pd.to_datetime(df_sim.index), inplace=True)

    df_obs, df_sim = resample_ts(df_obs, df_sim, time_scale)

    # compute scores
    click.echo('INFO -- computing scores.')
    df_scores = sim_data.validate_timeseries(df_sim, df_obs, out_dir=out_dir, suffix=time_scale, return_all_KGE=False)

    df_scores.index = [station]

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

def get_data_from_yml(yaml_root, data, station, var_name, encoding, verbose):
    """[summary]

    Args:
        yaml_root ([type]): [description]
        data ([type]): [description]
        station ([type]): [description]
        var_name ([type]): [description]
        encoding ([type]): [description]
        verbose ([type]): [description]

    Returns:
        [type]: [description]
    """    

    # construct path to GRDC-file
    grdc_file = os.path.join(yaml_root, data[str(station)]['file'])           
    click.echo('INFO -- reading observations from file {}.'.format(grdc_file))

    grdc_data = obs_data.grdc_data(grdc_file)

    if verbose: click.echo('VERBOSE -- retrieving GRDC station properties.')
    plot_title, props = grdc_data.get_grdc_station_properties(encoding=encoding)

    # retrieving values from GRDC file
    if 'column' in data[str(station)].keys():
        df_obs, props = grdc_data.get_grdc_station_values(col_name=data[str(station)]['column'], var_name=var_name, encoding=encoding, verbose=verbose)
    else:
        df_obs, props = grdc_data.get_grdc_station_values(var_name=var_name, verbose=verbose, encoding=encoding)
    df_obs.set_index(pd.to_datetime(df_obs.index), inplace=True)

    # if 'lat' or 'lon' are specified for a station in yml-file,
    # use this instead of GRDC coordinates
    if 'lat' in data[str(station)].keys():
        if verbose: click.echo('VERBOSE -- overwriting GRDC latitude information {} with user input {}.'.format(props['latitude'], data[str(station)]['lat']))
        props['latitude'] = data[str(station)]['lat']
    if 'lon' in data[str(station)].keys():
        if verbose: click.echo('VERBOSE -- overwriting GRDC longitude information {} with user input {}.'.format(props['longitude'], data[str(station)]['lon']))
        props['longitude'] = data[str(station)]['lon']

    return df_obs, props

def resample_ts(df_obs, df_sim, time_scale):
    """[summary]

    Args:
        df_obs ([type]): [description]
        df_sim ([type]): [description]
        time_scale ([type]): [description]

    Returns:
        [type]: [description]
    """    

    # resample if specified to other time scales
    if time_scale == 'month':
        df_obs = time_funcs.resample_to_month(df_obs, stat_func='mean')
        df_sim = time_funcs.resample_to_month(df_sim, stat_func='mean')
    elif time_scale == 'year':
        df_obs = time_funcs.resample_to_annual(df_obs, stat_func='mean')
        df_sim = time_funcs.resample_to_annual(df_sim, stat_func='mean')
    else:
        df_obs = df_obs
        df_sim = df_sim    

    return df_obs, df_sim

def write_output(outputList, time_scale, geojson, out):
    """[summary]

    Args:
        outputList ([type]): [description]
        time_scale ([type]): [description]
        geojson ([type]): [description]
        out ([type]): [description]
    """    

    all_scores, geo_dict = create_output(outputList)

    all_scores = all_scores.T

    if time_scale != None:
        click.echo('INFO -- saving all scores to {}.'.format(os.path.join(out, 'all_scores_{}.csv'.format(time_scale))))
        all_scores.to_csv(os.path.join(out, 'all_scores_{}.csv'.format(time_scale)))
    else:
        click.echo('INFO -- saving all scores to {}.'.format(os.path.join(out, 'all_scores.csv')))
        all_scores.to_csv(os.path.join(out, 'all_scores.csv'))

    # write geojson-file to disc
    if geojson:
        gdf = gpd.GeoDataFrame(geo_dict, crs="EPSG:4326")
        if time_scale != None:
            click.echo('INFO -- saving spatial information to {}'.format(os.path.join(os.path.abspath(out), 'scores_per_location_{}.geojson'.format(time_scale))))
            gdf.to_file(os.path.join(os.path.abspath(out), 'scores_per_location_{}.geojson'.format(time_scale)), driver='GeoJSON')
        else:
            click.echo('INFO -- saving spatial information to {}'.format(os.path.join(os.path.abspath(out), 'scores_per_location.geojson')))
            gdf.to_file(os.path.join(os.path.abspath(out), 'scores_per_location.geojson'), driver='GeoJSON')

def write_output_poly(outputList, sim_var_name, obs_var_name, out, plot):
    """[summary]

    Args:
        outputList ([type]): [description]
        sim_var_name ([type]): [description]
        obs_var_name ([type]): [description]
        out ([type]): [description]
        plot ([type]): [description]
    """    

    all_scores, geo_dict = create_output_poly(outputList)

    click.echo('INFO -- storing dictionary to {}.'.format(os.path.join(out, 'output_dict.csv')))
    all_scores.to_csv(os.path.join(out, '{}_vs_{}.csv'.format(sim_var_name, obs_var_name)))

    # assign evaluation metrics per polygon to geometry and store to file
    gdf = gpd.GeoDataFrame(geo_dict, crs="EPSG:4326")
    click.echo('INFO -- storing polygons to {}.'.format(os.path.join(out, 'output_polygons.geojson')))
    gdf.to_file(os.path.join(out, '{}_vs_{}.geojson'.format(sim_var_name, obs_var_name)), driver='GeoJSON')

    # plot if specified
    if plot:
        fig, axes = plt.subplots(2, 2, figsize=(10, 10), sharex=True, sharey=True)
        gdf.plot(ax=axes[0,0], column='R2', legend=True)
        axes[0,0].set_title('R2')
        gdf.plot(ax=axes[0,1], column='MSE', legend=True)
        axes[0,1].set_title('MSE')
        gdf.plot(ax=axes[1,0], column='RMSE', legend=True)
        axes[1,0].set_title('RMSE')
        gdf.plot(ax=axes[1,1], column='RRMSE', legend=True)
        axes[1,1].set_title('RRMSE')
        plt.savefig(os.path.join(out, '{}_vs_{}.png'.format(sim_var_name, obs_var_name)), dpi=300, bbox_inches='tight')

def create_output(outputList):
    """[summary]

    Args:
        outputList ([type]): [description]

    Returns:
        [type]: [description]
    """    

    geo_dict = {'station': list(), 'KGE': list(), 'R2': list(), 'NSE': list(), 'MSE': list(), 'RMSE': list(), 'RRMSE': list(), 'geometry': list()}

    all_scores = pd.DataFrame()

    for dd in outputList:

        geo_dict['station'].append(dd['station'])
        geo_dict['KGE'].append(dd['KGE'])
        geo_dict['R2'].append(dd['R2'])
        geo_dict['NSE'].append(dd['NSE'])
        geo_dict['MSE'].append(dd['MSE'])
        geo_dict['RMSE'].append(dd['RMSE'])
        geo_dict['RRMSE'].append(dd['RRMSE'])
        geo_dict['geometry'].append(dd['geometry'])

        df = pd.DataFrame.from_dict(dd, orient='index', columns=[dd['station']]).drop(['station', 'geometry'])

        all_scores = pd.concat([all_scores, df], axis=1)

    return all_scores, geo_dict

def create_output_poly(outputList):
    """[summary]

    Args:
        outputList ([type]): [description]

    Returns:
        [type]: [description]
    """    

    geo_dict = {'ID': list(), 'R2': list(), 'MSE': list(), 'RMSE': list(), 'RRMSE': list(), 'geometry': list()}

    all_scores = pd.DataFrame()

    for dd in outputList:

        geo_dict['ID'].append(dd['ID'])
        geo_dict['R2'].append(dd['R2'])
        geo_dict['MSE'].append(dd['MSE'])
        geo_dict['RMSE'].append(dd['RMSE'])
        geo_dict['RRMSE'].append(dd['RRMSE'])
        geo_dict['geometry'].append(dd['geometry'][0])

        df = pd.DataFrame.from_dict(dd, orient='index', columns=[dd['ID']]).drop(['ID', 'geometry'])

        all_scores = pd.concat([all_scores, df], axis=1)

    all_scores = all_scores.T

    return all_scores, geo_dict

def unpickle_object(loc):
    """
    Unpickles a previously pickled object.

    Arguments:
        loc (str): path to pickled object.

    Returns:
        mixed pickles.
    """    

    with open(loc, "rb") as f:
        out = pickle.load(f)

    return out