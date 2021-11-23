from numpy import little_endian
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

@click.group()
def cli():

    return

@cli.command()
@click.argument('ncf')
@click.argument('poly')
@click.argument('out')
@click.option('-v', '--var-name', help='variable name in netCDF-file.', type=str)
@click.option('-id', '--poly-id', help='unique identifier in file containing polygons.', type=str)
@click.option('-crs', '--crs-system', default='epsg:4326', help='coordinate system.', type=str)
@click.option('-of', '--out-file-name', default='mask.list', help='name of file to which polygon and mask data is pickled.', type=str)
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')

def create_POLY_mask(ncf, poly, out, var_name, out_file_name, poly_id, crs_system, verbose):
    """Creates a mask per polygon for a given netCDF file.
    The resulting combination of polygon and mask is saved to a dictionary, wihch in turn is pickled.
    All dictionaries are saved in a list which is pickled too.
    That way, it is possible to perform the time-consuming rioxarray.clip() function only once and save time during evaluation.

    NCF: path to netCDF-file.

    POLY: path to geojson-file with one or more polygons.

    OUT: path where dataframe and masks are pickled to file with -of/--out-file-name.
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
    ds = ds[var_name].sum('time')

    # align spatial settings of nc-files to be compatible with geosjon-file or ply-file
    if verbose: click.echo('VERBOSE -- setting spatial dimensions and crs of nc-files')
    try:
        ds.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
    except:
        ds.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)
    ds.rio.write_crs(crs_system, inplace=True)

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
        mask_data = ds.rio.clip(poly_gdf_id.geometry, drop=False, all_touched=True)

        # if non-nan values are picked up in the aggregation over time, create mask
        if np.sum(mask_data.values) != np.nan:

            # get boolean mask with True for all cells that do not contain missing values
            poly_mask = ~xr.ufuncs.isnan(mask_data)

            # make sure the original 2D-shape is maintained
            assert poly_mask.shape == ds.values.shape

            # define path to pickled mask
            path = os.path.join(out, 'mask_{}.mask'.format(ID))

            # pickle each mask
            with open(path, 'wb') as f:
                pickle.dump(poly_mask, f)
    
            # append ID and path to mask to list
            ll_ID.append(int(ID))
            ll_path.append(path)  

        # otherwise, skip this polygon
        else:
            
            if verbose: click.echo('VERBOSE -- no values found in polygon, skipped.')
            pass

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


@cli.command()
@click.argument('in_dir')
@click.argument('out')
@click.option('-c_thld', '--cat-area-thld', default=0, help='minimum catchment area stations needs to have to be selected', type=int)
@click.option('-y_thld', '--nr-years-thld', default=1, help='minimum number of years stations needs to have to be selected', type=int)
@click.option('-ts_start', '--timeseries-start', default='1900-01', help='start date of observed timeseries to be considered in selection (format="YYYY-MM")', type=str)
@click.option('-ts_end', '--timeseries-end', default='2100-01', help='end date of observed timeseries to be considered in selection (format="YYYY-MM")', type=str)
@click.option('-gc', '--grdc-column', default=' Calculated', help='name of column in GRDC file to be read', type=str)
@click.option('-e', '--encoding', default='ISO-8859-1', help='encoding of GRDC-files.', type=str)
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')

def select_GRDC_stations(in_dir, out, grdc_column, verbose, encoding, cat_area_thld, nr_years_thld, timeseries_end, timeseries_start):
    """This simple function can be run to select GRDC stations based on their properties.
    This can be handy to reduce the number of stations to evaluate in a subsequent step.
    The properties on which selection critieria can be applied are upstream area, number of years of data record, and end date of data record.
    
    A txt-file is written containing the numbers of those stations selected.
    This file can later be applied when evaluating discharge with -f setting in 'pcru_eval_tims grdc'.

    IN_DIR: path to folder where GRDC-stations are located.

    OUT_DIR: path to folder where txt-file is written.
    """    

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
        if (props['cat_area'] >= cat_area_thld) and (props['no_years'] >= nr_years_thld) and (props['ts_end'] <= pd.to_datetime(timeseries_end)) and (props['ts_start'] >= pd.to_datetime(timeseries_start)):
    
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