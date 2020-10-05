#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pcrglobwb_utils
import click
import pandas as pd
import xarray as xr
import numpy as np
import geopandas as gpd
import rioxarray as rio
import matplotlib.pyplot as plt
import datetime
import spotpy
import os, sys
from osgeo import gdal

@click.command()
@click.argument('shp',)
@click.argument('sim',)
@click.argument('obs',)
@click.argument('out',)
@click.option('-gvar', '--gleam-varname', default='E', help='variable name in GLEAM file', type=str)
@click.option('-pvar', '--pcrglobwb-varname', default='total_evaporation', help='variable name in PCR-GLOBWB file', type=str)
@click.option('-cf', '--conversion-factor', default=1000, help='conversion factor to align variable units', type=int)

def main(shp, sim, obs, out, gleam_varname='E', pcrglobwb_varname='land_surface_evaporation', conversion_factor=1000):
    """

    Computes r and RMSE for a give area (as defined by the shp-file) between simulated evaporation from PCR-GLOBWB and GLEAM data.
    Returns a plot of clipped mean values and timeseries of mean values plus bias. Also returns scores of r and rmse as dataframe.
    By default variables 'total_evaporation' and 'E' are used, but this can be replaced depending on user needs. 
    Note that in this case the conversion factor may have to be changed as well.

    shp: path to shp-file

    sim: simulated evaporation.

    obs: GLEAM evaporation data.

    out: path to output folder.

    """    

    print('\n\n')

    pcrglobwb_utils.utils.print_versions()

    print('\n')

    if not os.path.isdir(out):
        os.makedirs(out)
    print('saving output to folder {}'.format(os.path.abspath(out)))

    print('\n')

    print('reading files for GLEAM {0} and PCR-GLOBWB {1}'.format(os.path.abspath(obs), os.path.abspath(sim)))
    GLEAM_ds = xr.open_dataset(obs)
    PCR_ds = xr.open_dataset(sim)

    print('extract raw data from files')
    print('... GLEAM variable {}'.format(gleam_varname))
    GLEAM_data = GLEAM_ds[gleam_varname]
    GLEAM_data = GLEAM_data.T
    print('... PCR variable {}'.format(pcrglobwb_varname))
    PCR_data = PCR_ds[pcrglobwb_varname] * conversion_factor

    print('reading shp-file {}'.format(os.path.abspath(shp)))
    extent_gdf = gpd.read_file(shp, crs='epsg:4326')

    print('clipping nc-files to extent of shp-file')
    try:
        GLEAM_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
    except:
        GLEAM_data.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)
    GLEAM_data.rio.write_crs('epsg:4326', inplace=True)
    GLEAM_data = GLEAM_data.rio.clip(extent_gdf.geometry, extent_gdf.crs, drop=True)

    try:
        PCR_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
    except:
        PCR_data.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)
    PCR_data.rio.write_crs('epsg:4326', inplace=True)
    PCR_data = PCR_data.rio.clip(extent_gdf.geometry, extent_gdf.crs, drop=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    PCR_data.mean(dim='time').plot(ax=ax1)
    ax1.set_title('PCR-GLOBWB')
    GLEAM_data.mean(dim='time').plot(ax=ax2)
    ax2.set_title('GLEAM')
    plt.savefig(os.path.join(out, 'mean_GLEAM_and_PCR_data.png'), dpi=300, bbox_inches='tight')

    print('calculating mean per timestep over clipped area')
    GLEAM_arr = []
    for i in range(len(GLEAM_data.time)):
        time = GLEAM_data.time[i]
        t = pd.to_datetime(time.values)
        mean_Ep = float(GLEAM_data.T.sel(time=t).mean(skipna=True))
        GLEAM_arr.append(mean_Ep)
    PCR_arr = []
    for i in range(len(PCR_ds.time.values)):
        time = PCR_data.time[i]
        t = pd.to_datetime(time.values)
        mean_Ep = float(PCR_data.sel(time=t).mean(skipna=True))
        PCR_arr.append(mean_Ep)

    print('creating datetime indices for dataframes')
    GLEAM_idx = pd.to_datetime(pd.to_datetime(GLEAM_ds.time.values).strftime('%Y-%m'))
    GLEAM_daysinmonth = GLEAM_idx.daysinmonth.values

    PCR_idx = pd.to_datetime(pd.to_datetime(PCR_ds.time.values).strftime('%Y-%m'))
    PCR_daysinmonth = PCR_idx.daysinmonth.values

    print('creating dataframe for GLEAM')
    GLEAM_tuples = list(zip(GLEAM_arr, GLEAM_daysinmonth))
    GLEAM_df = pd.DataFrame(GLEAM_tuples, index=GLEAM_idx, columns=[gleam_varname, 'GLEAM_daysinmonth'])
    print('...dividing monthly aggregated data by days per month to get average monthly values')
    GLEAM_df[gleam_varname] = GLEAM_df[gleam_varname].divide(GLEAM_df['GLEAM_daysinmonth'])
    del GLEAM_df['GLEAM_daysinmonth']

    print('creating dataframe for PCR')
    PCR_tuples = list(zip(PCR_arr, PCR_daysinmonth))
    PCR_df = pd.DataFrame(data=PCR_tuples, index=PCR_idx, columns=[pcrglobwb_varname, 'PCR_daysinmonth'])
    print('...dividing monthly aggregated data by days per month to get average monthly values')
    PCR_df[pcrglobwb_varname] = PCR_df[pcrglobwb_varname].divide(PCR_df['PCR_daysinmonth'])
    del PCR_df['PCR_daysinmonth']

    print('calculating accuracy of PCR-GLOBWB data')
    final_df = pd.concat([GLEAM_df, PCR_df], axis=1).dropna()

    r = spotpy.objectivefunctions.correlationcoefficient(final_df[gleam_varname].values, final_df[pcrglobwb_varname].values)
    rmse = spotpy.objectivefunctions.rmse(final_df[gleam_varname].values, final_df[pcrglobwb_varname].values)

    print('...correlation coefficient is {}'.format(r))
    print('...RMSE is {}'.format(rmse))

    out_dict = dict()
    out_dict['r'] = round(r, 3)
    out_dict['RMSE'] = round(rmse, 0)

    out_df = pd.DataFrame().from_dict(out_dict, orient='index').T
    out_df.to_csv(os.path.join(out, 'evaluation.csv'))

    print('plotting timeseries...')
    fig, ax = plt.subplots(1, 1, figsize=(20,10))
    final_df.plot(ax=ax, legend=True)
    ax.set_title('monthly spatially averaged evapotranspiration')
    ax.set_ylabel('evapotranspiration [mm]')
    ax.text(0.88, 0.05, 'r={}'.format(round(r, 2)), transform=ax.transAxes)
    ax.text(0.88, 0.02, 'rmse={}'.format(round(rmse, 2)), transform=ax.transAxes)
    plt.savefig(os.path.join(out, 'timeseries_monthly_spatial_mean_{0}_and_{1}.png'.format(gleam_varname, pcrglobwb_varname)), dpi=300, bbox_inches='tight')

    print('...and bias')
    fig, ax = plt.subplots(1, 1, figsize=(20,10))
    (final_df[gleam_varname] - final_df[pcrglobwb_varname]).plot(ax=ax)
    ax.set_title('BIAS monthly spatially averaged evapotranspiration (GLEAM - PCR-GLOBWB)')
    ax.set_ylabel('evapotranspiration BIAS [mm]')
    plt.savefig(os.path.join(out, 'bias_monthly_spatial_mean_{0}_and_{1}.png'.format(gleam_varname, pcrglobwb_varname)), dpi=300, bbox_inches='tight')

if __name__ == '__main__':

    main()





