import pcrglobwb_utils
import click
import yaml
import os
import glob
import pandas as pd

def check_mode(yaml_file, folder):
    """Checks whether GRDC data is read via a yml-file or all files within a folder are used.
    Also checks that not both options are specified at once.
    """

    if (yaml_file != None) and (folder != None):
        raise ValueError('ERROR: not possible to specify both yaml-file and folder - only one option posssible!')

    if yaml_file != None:
        click.echo(click.style('INFO: reading GRDC data via yml-file.', fg='red'))
        mode = 'yml'
    if folder != None:
        click.echo(click.style('INFO: reading GRDC data from folder.', fg='red'))
        mode = 'fld'

    return mode

def read_yml(yaml_file):
    """Loads and parses a yaml-file and returns its content as well root.
    """

    # get path to yml-file containing GRDC station info
    yaml_file = os.path.abspath(yaml_file)
    click.echo(click.style('INFO: parsing GRDC station information from file {}'.format(yaml_file), fg='red'))
    # get content of yml-file
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    # get location of yml-file
    yaml_root = os.path.dirname(yaml_file)

    return data, yaml_root

def glob_folder(folder, grdc_column, verbose, encoding='ISO-8859-1'):
    """Collects and reads all files within a folder.
    Assumes all files are GRDC files and retrieves station properties and values from file.
    Returns all of this info as dictionary.
    """

    folder = os.path.abspath(folder)
    click.echo('INFO: folder with GRDC data is {}'.format(folder))
    files = sorted(glob.glob(os.path.join(folder,'*')))

    dd = dict()

    for f in files:
        click.echo('INFO: loading GRDC file {} with encoding {}.'.format(f, encoding))
        grdc_data = pcrglobwb_utils.obs_data.grdc_data(f)
        # if verbose: click.echo('VERBOSE: retrieving GRDC station properties.')
        plot_title, props = grdc_data.get_grdc_station_properties(encoding=encoding)

        # retrieving values from GRDC file
        df_obs, props = grdc_data.get_grdc_station_values(col_name=grdc_column, var_name='OBS', encoding=encoding, verbose=verbose)

        df_obs.set_index(pd.to_datetime(df_obs.index), inplace=True)

        dd[str(props['station'])] = [props, df_obs]

    return dd