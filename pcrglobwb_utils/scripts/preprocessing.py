import pcrglobwb_utils
import click

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

    pcrglobwb_utils.pre.mask_polygons(ncf, poly, out, var_name, out_file_name, poly_id, crs_system, verbose)

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

    pcrglobwb_utils.pre.select_grdc_stations(in_dir, out, grdc_column, verbose, encoding, cat_area_thld, nr_years_thld, timeseries_end, timeseries_start)