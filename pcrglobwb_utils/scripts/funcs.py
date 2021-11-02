
from pcrglobwb_utils import sim_data, obs_data, utils
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import click
import os

def evaluate_stations(station, pcr_ds, out, mode, yaml_root, data, var_name, time_scale, encoding, geojson, plot, verbose):
    
    # print some info
    click.echo(click.style('INFO: validating station {}.'.format(station), fg='cyan'))
    
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
        click.echo('INFO: preparing geo-dict for GeoJSON output')
        gdd = {'station': station, 'geometry': Point(props['longitude'], props['latitude'])}

    # get row/col combination for cell corresponding to lon/lat combination
    click.echo('INFO: getting row/column combination from longitude/latitude.')
    row, col = sim_data.find_indices_from_coords(pcr_ds, props['longitude'], props['latitude'])

    # retrieving values at that cell
    click.echo('INFO: reading variable {} at row {} and column {}.'.format(var_name, row, col))
    df_sim = sim_data.read_at_indices(pcr_ds, row, col, var_name=var_name, plot_var_name='SIM')
    df_sim.set_index(pd.to_datetime(df_sim.index), inplace=True)

    df_obs, df_sim = resample_ts(pcr_ds, df_obs, df_sim, time_scale)

    # compute scores
    click.echo('INFO: computing scores.')
    df_scores = sim_data.validate_timeseries(df_sim, df_obs, out_dir=out_dir, suffix=time_scale, return_all_KGE=False)

    df_scores.index = [station]

    # update geojson-file with KGE info
    if geojson: 
        # if verbose: click.echo('VERBOSE: adding station KGE to geo-dict')
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

    # construct path to GRDC-file
    grdc_file = os.path.join(yaml_root, data[str(station)]['file'])           
    click.echo('INFO: reading observations from file {}.'.format(grdc_file))

    click.echo('INFO: loading GRDC data.')
    grdc_data = obs_data.grdc_data(grdc_file)

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

    return df_obs, props

def resample_ts(pcr_obj, df_obs, df_sim, time_scale):

    # resample if specified to other time scales
    if time_scale == 'month':
        click.echo('INFO: resampling observed data to monthly time scale.')
        df_obs = df_obs.resample('M', convention='start').mean()
        df_sim = pcr_obj.resample2monthly()
    elif time_scale == 'year':
        click.echo('INFO: resampling observed data to yearly time scale.')
        df_obs = df_obs.resample('Y', convention='start').mean()
        df_sim = pcr_obj.resample2yearly()
    elif time_scale == 'quarter':
        click.echo('INFO: resampling observed data to quarterly time scale.')
        df_obs = df_obs.resample('Q', convention='start').agg('mean')
        df_sim = pcr_obj.resample2quarterly()
    else:
        df_obs = df_obs
        df_sim = df_sim    

    return df_obs, df_sim

def write_output(outputList, time_scale, geojson, out):

    all_scores, geo_dict = create_output(outputList)

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

def create_output(outputList):

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