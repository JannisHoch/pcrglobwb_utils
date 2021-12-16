#!/usr/bin/env python
# coding: utf-8

import pcrglobwb_utils
import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
import pickle
import click
from datetime import datetime
import os

def mask_polygons(ncf, poly, out, var_name, out_file_name, poly_id, crs_system='epsg:4326', verbose=False):
    """This function produces a mask per polygon for a given ncf-file if there is data that is not-nan or not only zero.
    The masks are linked to polygon IDs. These links are pickled to a dataframe, which can be used later in the actual
    evaluation process.

    Arguments:
        ncf (str): path to netCDF-file.
        poly (str): path to geojson-file with polygons.
        out (str): path where dataframe and masks are pickled/stored.
        var_name (str): variable name in netCDF-file to be considered.
        out_file_name (str): name of file for pickled dataframe.
        poly_id (str): unique identifier of polygons.
        crs_system (str): coordinate system to be used. Defaults to 'epsg:4326'.
        verbose (bool): verbose on/off. Defaults to False.
    """    

    t_start = datetime.now()

    click.echo(click.style('INFO -- start preprocsesing: create-poly-mask.', fg='green'))
    click.echo(click.style('INFO -- pcrglobwb_utils version {}.'.format(pcrglobwb_utils.__version__), fg='green'))

    # create output dir
    out = os.path.abspath(out)
    pcrglobwb_utils.utils.create_out_dir(out)

    # open netCDF-file and reduce to first time step
    click.echo(click.style('INFO -- reading raster data from {}'.format(os.path.abspath(ncf)), fg='red'))
    ds = xr.open_dataset(os.path.abspath(ncf))
    # aggregate over time to pick also sparse data points in time
    ds_sum = ds[var_name].sum('time')
    ds_min = ds[var_name].min('time') 
    ds_max = ds[var_name].max('time') 

    ds_sum = pcrglobwb_utils.utils.align_geo(ds_sum, crs_system=crs_system, verbose=verbose)
    ds_min = pcrglobwb_utils.utils.align_geo(ds_min, crs_system=crs_system, verbose=verbose)
    ds_max = pcrglobwb_utils.utils.align_geo(ds_max, crs_system=crs_system, verbose=verbose)

    # read shapefile with one or more polygons
    click.echo(click.style('INFO -- reading polygons from {}'.format(os.path.abspath(poly)), fg='red'))
    poly_gdf = gpd.read_file(poly, crs=crs_system, driver='GeoJSON')

    # initiate lists for polygon ID and path to pickled mask
    ll_ID = list()
    ll_path = list()

    # go through all polygons
    click.echo('INFO -- looping through polygons')
    for ID in poly_gdf[poly_id].unique():

        if verbose: click.echo('VERBOSE -- polygon identifier {}.'.format(ID))

        # select polygon associated to unique identifier
        poly_gdf_id = poly_gdf.loc[poly_gdf[poly_id] == ID]

        # create mask by clipping DataArray to polygon geometry
        # note that this will contain actual values, not boolean ones
        mask_data = ds_sum.rio.clip(poly_gdf_id.geometry, drop=False, all_touched=True)
        mask_data_min = ds_min.rio.clip(poly_gdf_id.geometry, drop=False, all_touched=True)
        mask_data_max = ds_max.rio.clip(poly_gdf_id.geometry, drop=False, all_touched=True)

        if np.sum(mask_data).item() != np.nan:
            nan_flag = True
        else:
            nan_flag = False

        if (np.sum(mask_data_min).item() != 0.0) and (np.sum(mask_data_max).item() != 0.0):
            min_max_flag = True
        else:
            min_max_flag = False

        # if not only nan values are picked up in the aggregation over time, create mask
        # or if the sum of maximum and minimum values per cell do not equal 0, indicating all values are 0, create mask 
        # otherwise, skip this polygon
        if nan_flag and min_max_flag:

            # get boolean mask with True for all cells that do not contain missing values
            # poly_mask = ~xr.ufuncs.isnan(mask_data) # deprecated
            poly_mask = ~np.isnan(mask_data)

            # make sure the original 2D-shape is maintained
            assert poly_mask.shape == ds_sum.values.shape

            # define path to pickled mask
            path = os.path.join(out, 'mask_{}.mask'.format(ID))

            # pickle each mask
            with open(path, 'wb') as f:
                pickle.dump(poly_mask, f)
    
            # append ID and path to mask to list
            ll_ID.append(int(ID))
            ll_path.append(path)  

        if not nan_flag:

            if verbose: click.echo('VERBOSE -- not creating mask. Only nan values found in polygon.')

        if not min_max_flag:

            if verbose: click.echo('VERBOSE -- not creating mask. Min/max values only 0 in polygon.')

    # create output dataframe
    dd = {'ID': ll_ID, 'path': ll_path}
    df_out = pd.DataFrame(data=dd)
    df_out.set_index('ID', inplace=True)
    
    # pickle list with dictionaries linking unique polygon identifiers with their masks 
    fname = os.path.join(out, out_file_name)
    click.echo('INFO -- pickling list with dictionaries to {}'.format(fname))
    with open(fname, 'wb') as f:
            pickle.dump(df_out, f)

    t_end = datetime.now()
    delta_t  = t_end - t_start

    click.echo(click.style('INFO -- done.', fg='green'))
    click.echo(click.style('INFO -- run time: {}.'.format(delta_t), fg='green'))

def select_grdc_stations(in_dir, out, grdc_column, verbose, encoding, cat_area_thld, nr_years_thld, timeseries_end, timeseries_start):

    t_start = datetime.now()
    
    click.echo(click.style('INFO -- start preprocessing: select-grdc-stations.', fg='green'))
    click.echo(click.style('INFO -- pcrglobwb_utils version {}.'.format(pcrglobwb_utils.__version__), fg='green'))
    
    # input directory
    in_dir = os.path.abspath(in_dir)

    # create main output dir
    out = os.path.abspath(out)
    pcrglobwb_utils.utils.create_out_dir(out)

    # define output file with selected stations
    out_fo = os.path.join(out, 'selected_GRDC_stations.txt')

    # initiate list with GRDC No.s which are selected
    out_ll = list()

    # collect all GRDC-files in the input folder
    data, files = pcrglobwb_utils.utils.glob_folder(in_dir, grdc_column, verbose, encoding=encoding)

    # from each file, collect properties and apply selection
    click.echo('INFO -- applying selection criteria')
    for key in data.keys():

        loc_data = data[str(key)]
        props = loc_data[0]

        # apply thresholds to station properties
        if (props['cat_area'] >= cat_area_thld) and (props['no_years'] >= nr_years_thld) and (props['ts_end'] >= pd.to_datetime(timeseries_end)) and (props['ts_start'] >= pd.to_datetime(timeseries_start)):
    
            # if both criteria are met, station is selected and appended to list
            if verbose: click.echo('... selected!')
            out_ll.append(props['station'])

    click.echo('INFO -- {}/{} stations selected'.format(len(out_ll), len(files)))
    
    # write list to output file
    fo = open(out_fo,'w')
    click.echo('INFO -- writing selected stations to {}'.format(out_fo))
    for item in out_ll:
        fo.write("%s\n" % item)
    fo.close()

    t_end = datetime.now()
    delta_t  = t_end - t_start

    click.echo(click.style('INFO -- done.', fg='green'))
    click.echo(click.style('INFO -- run time: {}.'.format(delta_t), fg='green'))