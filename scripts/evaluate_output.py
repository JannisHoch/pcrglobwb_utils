# -*- coding: utf-8 -*-

import pcrglobwb_utils
import click
import matplotlib.pyplot as plt
import datetime
import os, sys

@click.group()
def cli():
    pass

@click.command()
@click.argument('ncf',)
@click.argument('out_dir',)
@click.option('-g', '--grdc-file', default=None, help='path to GRDC file')
@click.option('-c', '--csv-file', default=None, help='path to CSV file',)
@click.option('-lat', '--latitude', default=None, help='latitude in degree',type=float)
@click.option('-lon', '--longitude', default=None, help='longitude in degree',type=float)
@click.option('-m', '--monthly-analysis', default=False, help='resampling all data to monthly average values',type=bool)
@click.option('-y', '--yearly-analysis', default=False, help='resampling all data to yearly average values',type=bool)

def main(ncf, out_dir, grdc_file=None, csv_file=None, latitude=None, longitude=None, monthly_analysis=False, yearly_analysis=False):
    """
    Arguments:

        NCF: netcdf-file

        OUT_DIR: path to output directory
    """   

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

    ## OBSERVED DATA ##
    # getting and checking files and settings for observed data (GRDC or CSV)
    if grdc_file is not None:
        obs_file = grdc_file
    elif csv_file is not None:
        obs_file = csv_file
        if (latitude is None) or (longitude is None):
            print('if you use a CSV file, you may want to specify latitude/longitude of observation station!')
    elif (grdc_file is not None) and (csv_file is not None):
        sys.exit('you cannot specify both a GRDC file and CSV file - choose your poison!')
    else:
        sys.exit('specify either a GRDC or CSV file containing observed values - if CSV value is used, also specify latitude and longitude!')

    if os.path.isabs(obs_file):
        pass
    else:
        obs_file = os.path.join(os.getcwd(), obs_file)

    print('getting observed data from file', os.path.abspath(obs_file))
    print('')

    if grdc_file is not None:
        obs_data = pcrglobwb_utils.obs_data.grdc_data(obs_file)
    if csv_file is not None:
        obs_data = pcrglobwb_utils.obs_data.other_data(obs_file)

    # provding plot names 
    #TODO: make this more interactive and less hard-coded
    new_var_name_obs = 'Qobs [m3/s]'
    new_var_name_sim = 'Qsim [m3/s]'

    # get observed data from GRDC file
    if grdc_file is not None:

        # get GRDC station properties
        grdc_plot_title, grdc_props = obs_data.get_grdc_station_properties()
        print('GRDC station properties are:')
        print(grdc_props)
        print('')

        # get GRDC timeseries
        df_obs = obs_data.get_grdc_station_values(var_name=new_var_name_obs,
                                                plot=False)

    # get observed data from CSV file
    if csv_file is not None:

        df_obs = obs_data.get_values_from_csv()

    ## NC FILE ##
    #NOTE: tested with 1 file so far only
    if os.path.isabs(ncf):
        pass
    else:
        ncf = os.path.join(os.getcwd(), ncf)

    print('reading from nc-file', os.path.abspath(ncf))
    print('')

    row, col = pcrglobwb_utils.utils.find_indices_from_coords(ncf, 
                                                            grdc_props['longitude'], 
                                                            grdc_props['latitude'])

    pcr_data = pcrglobwb_utils.sim_data.from_nc(ncf)

    q_sim = pcr_data.read_values_at_indices(row,
                                            col,
                                            plot_var_name=new_var_name_sim)

    if monthly_analysis:
        print('resampling to monthly average values' + os.linesep)
        df_obs = df_obs.resample('M').mean()
        pcr_data.daily2monthly()

    if yearly_analysis:
        print('resampling to yearly average values' + os.linesep)
        df_obs = df_obs.resample('Y').mean()
        pcr_data.daily2yearly()

    if monthly_analysis and yearly_analysis:
        raise ValueError('not possible to resampling to both monthly and yearly values - please specify only one option as True')

    df_eval, eval_dic = pcr_data.validate_results(df_obs,
                                                out_dir,
                                                new_var_name_obs,
                                                new_var_name_sim,
                                                plot=False,
                                                save_fig=True)
    
    print('head of evaluated dataframe columns')
    print(df_eval.head())
    print('')
    
    print('timeseries validation results are:')
    print(eval_dic)

    df_eval.to_csv(os.path.join(out_dir, 'dataframe.csv'), sep=';')

if __name__ == '__main__':
    main()

