# -*- coding: utf-8 -*-

import pcrglobwb_utils
import click
import matplotlib.pyplot as plt
import datetime
import pandas as pd
import os, sys

@click.group()
def cli():
    pass

@click.command()
@click.argument('out_dir',)
@click.option('-n', '--nc-file', default=None, help='path to netCDF file', multiple=True)
@click.option('-lat', '--latitude', default=None, help='latitude in degree',type=float)
@click.option('-lon', '--longitude', default=None, help='longitude in degree',type=float)

def main(out_dir, nc_file=None, latitude=None, longitude=None):
    """
    OUT_DIR: path to output directory
    """

    nc_file = nc_file
    if nc_file is None:
        sys.exit('provide at least one netCDF file to make this code work!')

    ## OUTPUT DIRECTORY ##
    # check whether output path provided is absolute or relative
    if os.path.isabs(out_dir):
        pass
    else:
        out_dir = os.path.join(os.getcwd(), out_dir)

    # check whether output path already exists, if not make a new folder
    if os.path.exists(out_dir):
        pass
    else:
        os.mkdir(out_dir) 

    # initiate logging
    sys.stdout = open(os.path.join(out_dir, 'logfile.log'), 'w')

    print(datetime.datetime.now())
    print('')

    # parsing arguments and checking whether provided paths are absolute or relative
    print(nc_file)
    ncfiles_list = nc_file # list of nc-files to be evaluated

    df_out = pd.DataFrame()

    # go throuh all provided nc-files
    for i, ncf in enumerate(ncfiles_list):

        # loop through provided filenames and check whether path is absolute or relative
        if os.path.isabs(ncf):
            nc_file = ncf
        else:
            nc_file = os.path.join(os.getcwd(), ncf)

        print('reading from nc-file', os.path.abspath(nc_file))
        print('')

        # get row/col from lon/lat
        row, col = pcrglobwb_utils.utils.find_indices_from_coords(nc_file, longitude, latitude)

        pcr_data = pcrglobwb_utils.sim_data.from_nc(nc_file)

        # extract information at a certain row/col
        q_sim = pcr_data.read_values_at_indices(row,
                                                col,
                                                plot_var_name=str(os.path.abspath(nc_file)))
        
        # concatenate all extracted timeseries to one output dataframe
        df_out = pd.concat([df_out, q_sim], axis=1)
        df_out = df_out.dropna()

    # save output dataframe to csv
    df_out.to_csv(os.path.join(out_dir, 'dataframe.csv'), sep=';')

    # plot timeseries and save to file
    df_out.plot()
    plt.savefig(os.path.join(out_dir, 'benchmark.png'), dpi=300)

if __name__ == '__main__':
    main()
    


