from . import funcs
import pcrglobwb_utils
import click
import os

@click.command()
@click.argument('in_dir')
@click.argument('out_dir')
@click.option('-gc', '--grdc-column', default=' Calculated', help='name of column in GRDC file to be read (only used with -f option)', type=str)
@click.option('--verbose/--no-verbose', default=False, help='more or less print output.')
@click.option('-e', '--encoding', default='ISO-8859-1', help='encoding of GRDC-files.', type=str)

def main(in_dir, out_dir, grdc_column, verbose, encoding):
    
    in_dir = os.path.abspath(in_dir)

    out_dir = os.path.abspath(out_dir)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    out_ll = list()

    data = funcs.glob_folder(in_dir, grdc_column, verbose, encoding=encoding)

    for d in data:
        grdc_obj = pcrglobwb_utils.obs_data.grdc_data(d)
        props = grdc_obj.get_grdc_station_properties()
        grdc_no = props['grdc_no']
        print(grdc_no)

    out_ll.append(grdc_no)

    return out_ll