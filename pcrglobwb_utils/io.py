#!/usr/bin/env python
# coding: utf-8

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import click
import pickle
import os

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