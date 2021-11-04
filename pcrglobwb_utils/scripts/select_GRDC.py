import pcrglobwb_utils
import pandas as pd
import click
import os

@click.command()
@click.argument('in_dir')
@click.argument('out_dir')
@click.option('-c_thld', '--cat-area-thld', default=0, help='minimum catchment area stations needs to have to be selected', type=int)
@click.option('-y_thld', '--nr-years-thld', default=1, help='minimum number of years stations needs to have to be selected', type=int)
@click.option('-ts_end', '--timeseries-end', default='1900-01', help='end date of observed timeseries to be considered in selection (format="YYYY-MM")', type=str)
@click.option('-gc', '--grdc-column', default=' Calculated', help='name of column in GRDC file to be read', type=str)
@click.option('-e', '--encoding', default='ISO-8859-1', help='encoding of GRDC-files.', type=str)
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')

def main(in_dir, out_dir, grdc_column, verbose, encoding, cat_area_thld, nr_years_thld, timeseries_end):
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

    # create output directory if not there yet
    out_dir = os.path.abspath(out_dir)
    if not os.path.isdir(out_dir):
        if verbose: click.echo('INFO -- creating output folder {}'.format(out_dir))
        os.makedirs(out_dir)
    # define output file with selected stations
    out_fo = os.path.join(out_dir, 'selected_GRDC_stations.txt')

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