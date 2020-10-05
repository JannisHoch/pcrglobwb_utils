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
@click.option('-gvar', '--grace-varname', default='lwe_thickness', help='variable name in GRACE file', type=str)
@click.option('-pvar', '--pcrglobwb-varname', default='total_thickness_of_water_storage', help='variable name in PCR-GLOBWB file', type=str)
@click.option('-cf', '--conversion-factor', default=100, help='conversion factor to align variable units', type=int)

def main(shp, sim, obs, out, grace_varname='lwe_thickness', pcrglobwb_varname='total_thickness_of_water_storage', conversion_factor=100):
    """

    Computes r and RMSE for a give area (as defined by the shp-file) between simulated evaporation from PCR-GLOBWB and GRACE data.
    Returns a plot of clipped mean values and timeseries of mean values plus bias. Also returns scores of r and rmse as dataframe.
    By default variables 'total_evaporation' and 'E' are used, but this can be replaced depending on user needs. 
    Note that in this case the conversion factor may have to be changed as well.

    shp: path to shp-file

    sim: simulated TWS.

    obs: GRACE data.

    out: path to output folder.

    """    

    print('\n\n')

    pcrglobwb_utils.utils.print_versions()

    print('\n')

    if not os.path.isdir(out):
        os.makedirs(out)
    print('saving output to folder {}'.format(os.path.abspath(out)))

    print('\n')

    print('reading files for GRACE {0} and PCR-GLOBWB {1}'.format(os.path.abspath(obs), os.path.abspath(sim)))
    GRACE_ds = xr.open_dataset(obs)
    PCR_ds = xr.open_dataset(sim)

    print('extract raw data from files')
    print('... GRACE variable {}'.format(grace_varname))
    GRACE_data = GRACE_ds[grace_varname]
    # GRACE_data = GRACE_data.T
    print('... PCR variable {}'.format(pcrglobwb_varname))
    PCR_data = PCR_ds[pcrglobwb_varname] * conversion_factor

    print('reading shp-file {}'.format(os.path.abspath(shp)))
    extent_gdf = gpd.read_file(shp, crs='epsg:4326')

    print('clipping nc-files to extent of shp-file')
    try:
        GRACE_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
    except:
        GRACE_data.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)
    GRACE_data.rio.write_crs('epsg:4326', inplace=True)
    GRACE_data = GRACE_data.rio.clip(extent_gdf.geometry, extent_gdf.crs, drop=True)

    try:
        PCR_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
    except:
        PCR_data.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)
    PCR_data.rio.write_crs('epsg:4326', inplace=True)
    PCR_data = PCR_data.rio.clip(extent_gdf.geometry, extent_gdf.crs, drop=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    PCR_data.mean(dim='time').plot(ax=ax1)
    ax1.set_title('PCR-GLOBWB')
    GRACE_data.mean(dim='time').plot(ax=ax2)
    ax2.set_title('GRACE')
    plt.savefig(os.path.join(out, 'mean_GRACE_and_PCR_data.png'), dpi=300, bbox_inches='tight')

    print('calculating mean per timestep over clipped area')
    GRACE_arr = []
    for i in range(len(GRACE_data.time)):
        time = GRACE_data.time[i]
        t = pd.to_datetime(time.values)
        mean_Ep = float(GRACE_data.T.sel(time=t).mean(skipna=True))
        GRACE_arr.append(mean_Ep)
    PCR_arr = []
    for i in range(len(PCR_ds.time.values)):
        time = PCR_data.time[i]
        t = pd.to_datetime(time.values)
        mean_Ep = float(PCR_data.sel(time=t).mean(skipna=True))
        PCR_arr.append(mean_Ep)

    print('determine anomalies')
    GRACE_anomaly = GRACE_arr - np.mean(GRACE_arr)
    PCR_anomaly = PCR_arr - np.mean(PCR_arr)

    print('creating datetime indices for dataframes')
    GRACE_idx = pd.to_datetime(pd.to_datetime(GRACE_ds.time.values).strftime('%Y-%m'))
    PCR_idx = pd.to_datetime(pd.to_datetime(PCR_ds.time.values).strftime('%Y-%m'))

    GRACE_df = pd.DataFrame(data=GRACE_anomaly, index=GRACE_idx, columns=[grace_varname])
    PCR_df = pd.DataFrame(data=PCR_anomaly, index=PCR_idx, columns=[pcrglobwb_varname])

    # accounting for missing values in time series (and thus missing index values!)
    GRACE_df = GRACE_df.resample('D').mean().fillna(np.nan).resample('M').mean()
    PCR_df = PCR_df.resample('D').mean().fillna(np.nan).resample('M').mean()

    GRACE_df = GRACE_df.loc[GRACE_df.index >= PCR_df.index.min()]
    GRACE_df = GRACE_df.loc[GRACE_df.index <= PCR_df.index.max()]

    print('calculating accuracy of PCR-GLOBWB data')
    final_df = pd.concat([GRACE_df, PCR_df], axis=1).dropna()

    r = spotpy.objectivefunctions.correlationcoefficient(final_df[grace_varname].values, final_df[pcrglobwb_varname].values)
    rmse = spotpy.objectivefunctions.rmse(final_df[grace_varname].values, final_df[pcrglobwb_varname].values)

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
    ax.set_title('monthly spatially averaged TWS anomaly')
    ax.set_ylabel('TWS anomaly [cm]')
    ax.text(0.88, 0.05, 'r={}'.format(round(r, 2)), transform=ax.transAxes)
    ax.text(0.88, 0.02, 'rmse={}'.format(round(rmse, 2)), transform=ax.transAxes)
    plt.savefig(os.path.join(out, 'timeseries_monthly_spatial_mean_{0}_and_{1}.png'.format(grace_varname, pcrglobwb_varname)), dpi=300, bbox_inches='tight')

if __name__ == '__main__':

    main()





