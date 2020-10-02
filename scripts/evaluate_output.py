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
@click.option('-e', '--excel-file', default=None, help='path to Excel file',)
@click.option('-lat', '--latitude', default=None, help='latitude in degree',type=float)
@click.option('-lon', '--longitude', default=None, help='longitude in degree',type=float)
@click.option('-m', '--monthly-analysis', default=False, help='resampling all data to monthly average values',type=bool)
@click.option('-y', '--yearly-analysis', default=False, help='resampling all data to yearly average values',type=bool)

def main(ncf, out_dir, grdc_file=None, excel_file=None, latitude=None, longitude=None, monthly_analysis=False, yearly_analysis=False):
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

    print('start logging at {}'.format(datetime.datetime.now()) + os.linesep)

    ## OBSERVED DATA ##
    # getting and checking files and settings for observed data (GRDC or Excel)
    if grdc_file is not None:
        obs_file = grdc_file
    elif excel_file is not None:
        obs_file = excel_file
        if (latitude is None) or (longitude is None):
            raise Warning('if you use a Excel file, you may want to specify latitude/longitude of observation station!')

    if (grdc_file is not None) and (excel_file is not None):
        raise ValueError('you cannot specify both a GRDC file and Excel file - choose your poison!')
    elif (grdc_file is None) and (excel_file is None):
        raise ValueError('specify either a GRDC or Excel file containing observed values - if Excel value is used, also specify latitude and longitude!')

    # getting absolute path to file with observations
    if os.path.isabs(obs_file):
        pass
    else:
        obs_file = os.path.join(os.getcwd(), obs_file)

    print('getting observed data from file {}'.format(os.path.abspath(obs_file)) + os.linesep)

    # initializing data objects
    if grdc_file is not None:
        obs_data = pcrglobwb_utils.obs_data.grdc_data(obs_file)
    if excel_file is not None:
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

        # getting lat/lon information from GRDC station properties
        latitude = grdc_props['latitude']
        longitude = grdc_props['longitude']

    # get observed data from Excel file
    if excel_file is not None:

        df_obs = obs_data.get_values_from_excel(var_name=new_var_name_obs)

    ## NC FILE ##
    #NOTE: tested with 1 file so far only
    # getting absolute path to nc-file
    if os.path.isabs(ncf):
        pass
    else:
        ncf = os.path.join(os.getcwd(), ncf)

    print('reading from nc-file {}'.format(os.path.abspath(ncf)) + os.linesep)

    row, col = pcrglobwb_utils.utils.find_indices_from_coords(ncf, 
                                                              longitude, 
                                                              latitude)

    pcr_data = pcrglobwb_utils.sim_data.from_nc(ncf)

    pcr_data.read_values_at_indices(row,
                                    col,
                                    plot_var_name=new_var_name_sim)

    pcr_stats = pcr_data.calc_stats(out_dir)

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

