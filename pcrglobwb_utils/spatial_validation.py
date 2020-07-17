import pandas as pd
import xarray as xr
import numpy as np
import geopandas as gpd
import rasterio
import rioxarray as rio
import matplotlib.pyplot as plt
import datetime
import spotpy
import os, sys

#TODO: make this object-based

def validate_with_GLEAM(PCR_nc_fo, GLEAM_nc_fo, shp_fo, PCR_var_name='land_surface_evaporation', GLEAM_var_name='E', convFactor=1000, crs='epsg:4326', plot=False, out_dir=None):
    """With this function, simulated land surface evaporation (or another evaporation output) from PCR-GLOBWB can be validated against evaporation data from GLEAM (or any other evaporation data in GLEAM).
    Area averages are computed per time step. The area of interest is specified with a shapefile.

    Args:
        PCR_nc_fo (str): Path to netCDF-file containing evaporation output from PCR-GLOBWB
        GLEAM_nc_fo (str): Path to netCDF-file containing GLEAM evaporation data
        shp_fo (str): Path to shapefile containing boundary of area of interest. Currently, only one area can be simulated at a time, function is not tested with shapefiles containing multiple polygons.
        PCR_var_name (str, optional): netCDF variable name in PCR-GLOBWB output. Defaults to 'land_surface_evaporation'.
        GLEAM_var_name (str, optional): netCDF variable name in GLEAM data. Defaults to 'E'.
        convFactor (int, optional): conversion factor to convert PCR-GLOBWB units to GLEAM units. Defaults to 1000.
        crs (str, optional): Projection system to be used. Defaults to 'epsg:4326'.
        plot (bool, optional): Whether or not to plot the resulting timeseries. Defaults to False.
        out_dir (str, optional): Path to folder where figures will be stored. If 'None', no output will be stored. Defaults to None.

    Returns:
        list: list containing computed values for R (correlation coefficient) and RMSE (root mean square error) computed with PCR-GLOBWB and GLEAM timeseries
        dataframe: dataframe containing the timeseries including missing values (NaN)
    """    

    #TODO: make this work with multiple polygons stored in the shape file, e.g. by going through all rows in gpd-object
    #TODO: or, if no shp_fo is specified, by clipping it to extent (xmin, ymin, xmax, ymax) of PCR-GLOBWB nc-file

    print('reading files for GLEAM {0} and PCR-GLOBWB {1}'.format(os.path.abspath(GLEAM_nc_fo), os.path.abspath(PCR_nc_fo)))
    GLEAM_ds = xr.open_dataset(GLEAM_nc_fo)
    PCR_ds = xr.open_dataset(PCR_nc_fo)

    print('extract raw data from nc-files')
    GLEAM_data = GLEAM_ds[GLEAM_var_name] # mm
    PCR_data = PCR_ds[PCR_var_name] # m

    print('reading shp-file {}'.format(os.path.abspath(shp_fo)))
    extent_gdf = gpd.read_file(shp_fo, crs=crs)

    print('clipping nc-files to extent of shp-file')
    GLEAM_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
    GLEAM_data.rio.write_crs(crs, inplace=True)
    GLEAM_data = GLEAM_data.rio.clip(extent_gdf.geometry, extent_gdf.crs, drop=True)

    PCR_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
    PCR_data.rio.write_crs(crs, inplace=True)
    PCR_data = PCR_data.rio.clip(extent_gdf.geometry, extent_gdf.crs, drop=True)

    print('multiplying PCR data with 1000 to convert from [m] to [mm]')
    PCR_data = PCR_data * convFactor # m * 1000 = mm

    print('calculating mean per timestep over clipped area')
    GLEAM_arr = []
    for time in GLEAM_data.time.values:
        mean_Ep = float(GLEAM_data.T.sel(time=time).mean(skipna=True))
        GLEAM_arr.append(mean_Ep)
    PCR_arr = []
    for time in PCR_ds.time.values:
        mean = float(PCR_data.sel(time=time).mean(skipna=True))
        PCR_arr.append(mean)

    print('creating datetime indices for dataframes')
    GLEAM_idx = pd.to_datetime(pd.to_datetime(GLEAM_ds.time.values).strftime('%Y-%m'))
    GLEAM_daysinmonth = GLEAM_idx.daysinmonth.values

    PCR_idx = pd.to_datetime(pd.to_datetime(PCR_ds.time.values).strftime('%Y-%m'))
    PCR_daysinmonth = PCR_idx.daysinmonth.values

    print('creating dataframe for GLEAM')
    GLEAM_tuples = list(zip(GLEAM_arr, GLEAM_daysinmonth))
    GLEAM_df = pd.DataFrame(GLEAM_tuples, index=GLEAM_idx, columns=[GLEAM_var_name, 'GLEAM_daysinmonth'])
    print('...dividing monthly aggregated data by days per month to get average monthly values')
    GLEAM_df[GLEAM_var_name] = GLEAM_df[GLEAM_var_name].divide(GLEAM_df['GLEAM_daysinmonth'])
    del GLEAM_df['GLEAM_daysinmonth']

    print('creating dataframe for PCR')
    PCR_tuples = list(zip(PCR_arr, PCR_daysinmonth))
    PCR_df = pd.DataFrame(data=PCR_tuples, index=PCR_idx, columns=[PCR_var_name, 'PCR_daysinmonth'])
    print('...dividing monthly aggregated data by days per month to get average monthly values')
    PCR_df[PCR_var_name] = PCR_df[PCR_var_name].divide(PCR_df['PCR_daysinmonth'])
    del PCR_df['PCR_daysinmonth']

    print('concatenating dataframes')
    final_df = pd.concat([GLEAM_df, PCR_df], axis=1)
    final_df_noNaN = pd.concat([GLEAM_df, PCR_df], axis=1).dropna()

    r = spotpy.objectivefunctions.correlationcoefficient(final_df_noNaN[GLEAM_var_name].values, _final_df_noNaNdf[PCR_var_name].values)
    rmse = spotpy.objectivefunctions.rmse(final_df_noNaN_df[GLEAM_var_name].values, final_df_noNaN_df[PCR_var_name].values)

    print('...correlation coefficient is {}'.format(r))
    print('...RMSE is {}'.format(rmse))

    if plot:
        print('plotting timeseries...')
        fig, ax = plt.subplots(1, 1, figsize=(20,10))
        final_df.plot(ax=ax, legend=True)
        ax.set_title('monthly spatially averaged evapotranspiration')
        ax.set_ylabel('evapotranspiration [mm]')
        ax.text(0.88, 0.05, 'r={}'.format(round(r, 2)), transform=ax.transAxes)
        ax.text(0.88, 0.02, 'rmse={}'.format(round(rmse, 2)), transform=ax.transAxes)
        if out_dir != None:
            plt.savefig(os.path.join(out_dir, 'timeseries_monthly_spatial_mean_{0}_and_{1}_GLEAM_validation.png'.format(GLEAM_varName, PCR_varName)), dpi=300)

        print('...and bias')
        fig, ax = plt.subplots(1, 1, figsize=(20,10))
        (final_df[GLEAM_var_name] - final_df[PCR_var_name]).plot(ax=ax)
        ax.set_title('BIAS monthly spatially averaged evapotranspiration (GLEAM - PCR-GLOBWB)')
        ax.set_ylabel('evapotranspiration BIAS [mm]')
        if out_dir != None:
            plt.savefig(os.path.join(out_dir, 'timeseries_monthly_spatial_mean_{0}_and_{1}_GLEAM_validation_BIAS.png'.format(GLEAM_varName, PCR_varName)), dpi=300)

    return [r, rmse], final_df


def funvalidate_with_GRACE(parameter_list):
    pass