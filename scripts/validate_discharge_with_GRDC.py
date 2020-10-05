import click
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import spotpy as sp
import pcrglobwb_utils
import os


@click.group()
def cli():
    pass

@click.command()
@click.argument('sim',)
@click.argument('obs',)
@click.argument('out',)
@click.option('-lon', '--longitude', default=None, help='longitude in degree', type=float)
@click.option('-lat', '--latitude', default=None, help='latitude in degree', type=float)

def main(sim, obs, out, longitude=None, latitude=None):
    """Validates discharge from PCR-GLOBWB with GRDC observations at a location.

    If longitude or latitude are  not provided in command line, coordinates are retrieved from GRDC file.

    SIM (str): path to PCR-GLOBWB discharge output.

    OBS (str): path to GRDC file.

    OUT (str): path to output folder.
    """

    print('\n\n\n')
    print(pcrglobwb_utils.__version__)
    print('')

    ### OUTPUT DIR ###

    if not os.path.isdir(out):
        os.makedirs(out)
    print('saving output to folder {}'.format(os.path.abspath(out)))

    ### GRDC DATA ###

    print('reading observed data from file {}'.format(os.path.abspath(obs)))

    # create object from GRDC file
    grdc_obj = pcrglobwb_utils.obs_data.grdc_data(obs)
    plot_title, props = grdc_obj.get_grdc_station_properties()
    # reading values from GRDC station text file and providing a variable name
    df_GRDC, props = grdc_obj.get_grdc_station_values(var_name='Q$obs$ GRDC')

    fig, ax = plt.subplots(1, 1, figsize=(20, 10))
    df_GRDC.plot(ax=ax)
    plt.savefig(os.path.join(out, 'GRDC_data.png'), dpi=300, bbox_inches='tight')
    plt.close()

    ### PCR-GLOBWB DATA ###

    print('reading model data from file {}'.format(sim))

    if longitude == None:
        longitude = props['longitude']
        print('no longitude provided, setting it to {} according to GRDC file'.format(props['longitude']))
    if latitude == None:
        latitude = props['latitude']
        print('no latitude provided, setting it to {} according to GRDC file'.format(props['latitude']))

    # based on lon/lat information of input or GRDC station, find corresponding row/col indices in nc-file
    row, col = pcrglobwb_utils.utils.find_indices_from_coords(sim, longitude, latitude)

    # create object first
    nc_object = pcrglobwb_utils.sim_data.from_nc(sim)
    # apply method to read values at specific row and col
    df_PCR = nc_object.read_values_at_indices(row, col, plot_var_name='Q$sim$ PCR-GLOBWB (1km)')

    fig, ax = plt.subplots(1, 1, figsize=(20, 10))
    ax.set_title('at lat/lon {0:0.2f}/{1:0.2f}'.format(latitude, longitude))
    df_PCR.plot(ax=ax)
    plt.savefig(os.path.join(out, 'PCR_data.png'), dpi=300, bbox_inches='tight')
    plt.close()

    ### BOTH ###

    both = pd.concat([df_GRDC, df_PCR], axis=1, join="inner", verify_integrity=True)

    ### EVALUATION ##

    nc_object.validate_results(df_GRDC, out_dir=out, return_all_KGE=True)

    ### PLOTTING ###

    fig, ax = plt.subplots(1, 1, figsize=(20,10))
    both['Q$sim$ PCR-GLOBWB (1km)'].plot(ax=ax, c='r', marker='o')
    both['Q$obs$ GRDC'].plot(ax=ax, c='k', marker='o')
    ax.set_title('station {0} / lat {1:0.2f} / lon {2:0.2f}'.format(props['station'], latitude, longitude))
    ax.set_ylabel('discharge [m3/s]')
    plt.legend()
    plt.savefig(os.path.join(out, 'timeseries_'+str(props['station'])+'.png'), dpi=300, bbox_inches='tight')
    plt.close()

    print('\n\n\n')

if __name__ == '__main__':
    main()
