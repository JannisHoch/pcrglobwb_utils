import pcrglobwb_utils
import pandas as pd
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
import pickle
import click
import os

@click.group()
def cli():

    return

@cli.command()
@click.argument('raster')
@click.argument('poly')
@click.argument('out')
@click.option('-v', '--var-name', help='variable name in netCDF-file.', type=str)
@click.option('-id', '--poly-id', help='unique identifier in file containing polygons.', type=str)
@click.option('-crs', '--crs-system', default='epsg:4326', help='coordinate system.', type=str)
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')

def create_POLY_mask(raster, poly, out, var_name, poly_id, crs_system, verbose):

    # create main output dir
    out = os.path.abspath(out)
    pcrglobwb_utils.utils.create_out_dir(out)

    pickle_out = os.path.join(out, 'masks')
    pcrglobwb_utils.utils.create_out_dir(pickle_out)

    raster = os.path.abspath(raster)

    click.echo(click.style('INFO -- reading raster data from {}'.format(raster), fg='red'))
    ds = xr.open_dataset(raster)
    ds = ds[var_name].sel(time=ds.time.values[0])

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

    ll = list()

    click.echo('INFO -- looping through polygons')
    for ID in poly_gdf[poly_id].unique():

        poly_gdf_id = poly_gdf.loc[poly_gdf[poly_id] == ID]

        poly_mask = ds.rio.clip(poly_gdf_id.geometry, drop=False, all_touched=True)

        with open(os.path.join(pickle_out, 'mask_{}.pkl'.format(ID)), 'wb') as f:
            pickle.dump(poly_mask, f)

        dd = {'ID': ID,
              'pkl': os.path.join(pickle_out, 'mask_{}.pkl'.format(ID))}   

        ll.append(dd)

    
    with open(os.path.join(out, 'mask_list.txt'), 'wb') as f:
            pickle.dump(ll, f)


@cli.command()
@click.argument('in_dir')
@click.argument('out')
@click.option('-c_thld', '--cat-area-thld', default=0, help='minimum catchment area stations needs to have to be selected', type=int)
@click.option('-y_thld', '--nr-years-thld', default=1, help='minimum number of years stations needs to have to be selected', type=int)
@click.option('-ts_end', '--timeseries-end', default='1900-01', help='end date of observed timeseries to be considered in selection (format="YYYY-MM")', type=str)
@click.option('-gc', '--grdc-column', default=' Calculated', help='name of column in GRDC file to be read', type=str)
@click.option('-e', '--encoding', default='ISO-8859-1', help='encoding of GRDC-files.', type=str)
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')

def select_GRDC_stations(in_dir, out, grdc_column, verbose, encoding, cat_area_thld, nr_years_thld, timeseries_end):
    """This simple function can be run to select GRDC stations based on their properties.
    This can be handy to reduce the number of stations to evaluate in a subsequent step.
    The properties on which selection critieria can be applied are upstream area, number of years of data record, and end date of data record.
    
    A txt-file is written containing the numbers of those stations selected.
    This file can later be applied when evaluating discharge with -f setting in 'pcru_eval_tims grdc'.

    Args:

        IN_DIR: path to folder where GRDC-stations are located.

        OUT_DIR: path to folder where txt-file is written.
    """    
    
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
    for f in files:

        grdc_obj = pcrglobwb_utils.obs_data.grdc_data(f)
        title, props = grdc_obj.get_grdc_station_properties()

        # apply thresholds to station properties
        if (props['cat_area'] > cat_area_thld) and (props['no_years'] > nr_years_thld) and (props['ts_end'] > pd.to_datetime(timeseries_end)):
    
            # if both criteria are met, station is selected and appended to list
            if verbose: click.echo('... selected!')
            out_ll.append(props['station'])
    
    # write list to output file
    fo = open(out_fo,'w')
    if verbose: click.echo('INFO -- writing selected stations to {}'.format(fo))
    for item in out_ll:
        fo.write("%s\n" % item)
    fo.close()