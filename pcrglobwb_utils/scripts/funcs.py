
import pcrglobwb_utils
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import click
import os

def evaluate_stations(station, ncf, out, mode, yaml_root, data, var_name, time_scale, encoding, geojson, verbose):

    # print some info
    click.echo(click.style('INFO: validating station {}.'.format(station), fg='cyan'))
    
    # create sub-directory per station
    out_dir = out + '/{}'.format(station)
    pcrglobwb_utils.utils.create_out_dir(out_dir)

    # if data is via yml-file, the data is read here as well as are station properties
    if mode == 'yml': 
        df_obs, props = get_data_from_yml(yaml_root, data, station, var_name, encoding, verbose)

    # if data comes from folder, it was already read and can now be retrieved from dictionary
    if mode == 'fld':
        df_obs, props = data[str(station)][1], data[str(station)][0]

    # now get started with simulated data
    click.echo('INFO: loading simulated data from {}.'.format(ncf))
    pcr_data = pcrglobwb_utils.sim_data.from_nc(ncf)

    # prepare a geojson-file for output later (if specified)
    if geojson:
        click.echo('INFO: preparing geo-dict for GeoJSON output')
        gdd = {'station': station, 'geometry': Point(props['longitude'], props['latitude'])}

    # get row/col combination for cell corresponding to lon/lat combination
    click.echo('INFO: getting row/column combination from longitude/latitude.')
    row, col = pcr_data.get_indices(props['longitude'], props['latitude'])

    # retrieving values at that cell
    click.echo('INFO: reading variable {} at row {} and column {}.'.format(var_name, row, col))
    df_sim = pcr_data.get_values(row, col, var_name=var_name, plot_var_name='SIM')
    df_sim.set_index(pd.to_datetime(df_sim.index), inplace=True)

    df_obs, df_sim = resample_ts(pcr_data, df_obs, df_sim, time_scale)

    # compute scores
    click.echo('INFO: computing scores.')
    df_scores = pcr_data.validate(df_obs, out_dir=out_dir, suffix=time_scale, return_all_KGE=False)

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

    return gdd

def get_data_from_yml(yaml_root, data, station, var_name, encoding, verbose):

    # construct path to GRDC-file
    grdc_file = os.path.join(yaml_root, data[str(station)]['file'])           
    click.echo('INFO: reading observations from file {}.'.format(grdc_file))

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

def write_output(all_scores, geo_dict, time_scale, geojson, out):

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