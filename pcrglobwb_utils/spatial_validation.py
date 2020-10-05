import pandas as pd
import xarray as xr
import numpy as np
import geopandas as gpd
import rasterio
from shutil import rmtree
import rioxarray as rio
import matplotlib.pyplot as plt
import datetime
import spotpy
import os, sys

#TODO: remove all stupid print statements

class validate_per_shape:
    """Initializing object for validating output for area(s) provided by shp-file.
    If the shp-file contains multiptle (polygon) geometries, validation is performed per individual geometry.
    Per geometry, r and RMSE are determined.

    Args:
        shp_fo (str): Path to shp-file defining the area extent for validation.
        shp_key (str): Column name in shp-file to be used as unique identifier per entry in shp-file.
        crs (str, optional): Definition of projection system in which validation takes place. Defaults to 'epsg:4326'.
        out_dir (str, optional): Path to output directory. In None, then no output is stored. Defaults to None.
    """      

    def __init__(self, shp_fo, shp_key, crs='epsg:4326', out_dir=None):
  
        self.shp_fo = shp_fo
        self.key = shp_key
        self.crs = crs
        self.out_dir = out_dir

        print('reading shp-file {}'.format(os.path.abspath(self.shp_fo)))
        self.extent_gdf = gpd.read_file(self.shp_fo, crs=self.crs)

        if self.out_dir != None:
            self.out_dir = os.path.abspath(self.out_dir)
            if os.path.isdir(self.out_dir):
                rmtree(self.out_dir)
            os.makedirs(self.out_dir)
            print('saving output to {}'.format(self.out_dir))

    def against_GLEAM(self, PCR_nc_fo, GLEAM_nc_fo, PCR_var_name='total_evaporation', GLEAM_var_name='E', convFactor=1000):
        """With this function, simulated land surface evaporation (or another evaporation output) from PCR-GLOBWB can be validated against evaporation data from GLEAM (or any other evaporation data in GLEAM).
        Works with monthly totals and computes monthly area averages per time step from it.

        Args:
            PCR_nc_fo (str): Path to netCDF-file containing evaporation output from PCR-GLOBWB.
            GLEAM_nc_fo (str): Path to netCDF-file containing GLEAM evaporation data.
            PCR_var_name (str, optional): netCDF variable name in PCR-GLOBWB output. Defaults to 'land_surface_evaporation'.
            GLEAM_var_name (str, optional): netCDF variable name in GLEAM data. Defaults to 'E'.
            convFactor (int, optional): conversion factor to convert PCR-GLOBWB units to GLEAM units. Defaults to 1000.

        Returns:
            geo-dataframe: containing data of shp-file appended with columns for R and RMSE per entry.
        """        

        print('reading GLEAM file {}'.format(os.path.abspath(GLEAM_nc_fo)))
        GLEAM_ds = xr.open_dataset(GLEAM_nc_fo)
        print('reading PCR-GLOBWB file {}'.format(os.path.abspath(PCR_nc_fo)))
        PCR_ds = xr.open_dataset(PCR_nc_fo)

        print('extract raw data from nc-files')
        GLEAM_data = GLEAM_ds[GLEAM_var_name] # mm
        GLEAM_data = GLEAM_data.T
        PCR_data = PCR_ds[PCR_var_name] # m
        PCR_data = PCR_data  * convFactor # m * 1000 = mm
        
        GLEAM_idx = pd.to_datetime(pd.to_datetime(GLEAM_ds.time.values).strftime('%Y-%m'))
        GLEAM_daysinmonth = GLEAM_idx.daysinmonth.values

        PCR_idx = pd.to_datetime(pd.to_datetime(PCR_ds.time.values).strftime('%Y-%m'))
        PCR_daysinmonth = PCR_idx.daysinmonth.values

        print('clipping nc-files to extent of shp-file')
        #- GLEAM
        try:
            GLEAM_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
        except:
            GLEAM_data.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)
        GLEAM_data.rio.write_crs(self.crs, inplace=True)
        #- PCR-GLOBWB
        try:
            PCR_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
        except:
            PCR_data.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)
        PCR_data.rio.write_crs(self.crs, inplace=True)

        out_dict = {}

        for ID in self.extent_gdf[self.key].unique():

            poly = self.extent_gdf.loc[self.extent_gdf[self.key] == ID]

            print('computing R and RMSE for polygon with key identifier {} {}'.format(self.key, ID))

            # clipping GRACE data-array to shape extent
            GLEAM_data_c = GLEAM_data.rio.clip(poly.geometry, poly.crs, drop=True)
            # clipping PCR data-array to shape extent
            PCR_data_c = PCR_data.rio.clip(poly.geometry, poly.crs, drop=True)

            mean_val_timestep_GLEAM = list()
            mean_val_timestep_PCR = list()

            # compute mean per time step in clipped data-array and append to array
            for i in range(len(GLEAM_data_c.time.values)):
                time = GLEAM_data_c.time[i]
                t = pd.to_datetime(time.values)
                mean = float(GLEAM_data_c.sel(time=t).mean(skipna=True))
                mean_val_timestep_GLEAM.append(mean)
            for i in range(len(PCR_data_c.time.values)):
                time = PCR_data_c.time[i]
                t = pd.to_datetime(time.values)
                mean = float(PCR_data_c.sel(time=t).mean(skipna=True))
                mean_val_timestep_PCR.append(mean)

            GLEAM_tuples = list(zip(mean_val_timestep_GLEAM, GLEAM_daysinmonth))
            GLEAM_df = pd.DataFrame(GLEAM_tuples, index=GLEAM_idx, columns=[GLEAM_var_name, 'GLEAM_daysinmonth'])
            GLEAM_df[GLEAM_var_name] = GLEAM_df[GLEAM_var_name].divide(GLEAM_df['GLEAM_daysinmonth'])
            del GLEAM_df['GLEAM_daysinmonth']

            PCR_tuples = list(zip(mean_val_timestep_PCR, PCR_daysinmonth))
            PCR_df = pd.DataFrame(data=PCR_tuples, index=PCR_idx, columns=[PCR_var_name, 'PCR_daysinmonth'])
            PCR_df[PCR_var_name] = PCR_df[PCR_var_name].divide(PCR_df['PCR_daysinmonth'])
            del PCR_df['PCR_daysinmonth']

            final_df = pd.concat([GLEAM_df, PCR_df], axis=1)
            final_df_noNaN = pd.concat([GLEAM_df, PCR_df], axis=1).dropna()

            r = spotpy.objectivefunctions.correlationcoefficient(final_df_noNaN[GLEAM_var_name].values, final_df_noNaN[PCR_var_name].values)
            rmse = spotpy.objectivefunctions.rmse(final_df_noNaN[GLEAM_var_name].values, final_df_noNaN[PCR_var_name].values)

            poly_skill_dict = {'R':round(r, 2),
                               'RMSE': round(rmse, 2)}

            out_dict[ID] = poly_skill_dict

        out_df = pd.DataFrame().from_dict(out_dict).T
        out_df.index.name = self.key

        gdf_gleam_out = self.extent_gdf.merge(out_df, on=self.key)

        return gdf_gleam_out

    def against_GRACE(self, PCR_nc_fo, GRACE_nc_fo, PCR_var_name='total_thickness_of_water_storage', GRACE_var_name='lwe_thickness', convFactor=100):
        """With this function, simulated totalWaterStorage output from PCR-GLOBWB can be validated against GRACE-FO observations. Yields timeseries of anomalies.
        Works with monthly averages and computes monthly area averages per time step from it.

        Args:
            PCR_nc_fo (str): Path to netCDF-file containing totalWaterStorage output from PCR-GLOBWB.
            GRACE_nc_fo (str): Path to netCDF-file containing GRACE-FO data
            PCR_var_name (str, optional): netCDF variable name in PCR-GLOBWB output. Defaults to 'total_thickness_of_water_storage'.
            GRACE_var_name (str, optional): netCDF variable name in GRACE-FO data. Defaults to 'lwe_thickness'.
            convFactor (int, optional): conversion factor to convert PCR-GLOBWB units to GRACE-FO units. Defaults to 100.

        Returns:
            geo-dataframe: containing data of shp-file appended with columns for R and RMSE per entry.
        """        
        
        print('reading GRACE file {}'.format(os.path.abspath(GRACE_nc_fo)))
        GRACE_ds = xr.open_dataset(GRACE_nc_fo)
        print('reading PCR-GLOBWB file {}'.format(os.path.abspath(PCR_nc_fo)))
        PCR_ds = xr.open_dataset(PCR_nc_fo)

        print('extract raw data from nc-files')
        GRACE_data = GRACE_ds[GRACE_var_name] # cm
        PCR_data = PCR_ds[PCR_var_name] # m
        PCR_data = PCR_data  * convFactor # m * 100 = cm

        GRACE_idx = pd.to_datetime(pd.to_datetime(GRACE_ds.time.values).strftime('%Y-%m'))
        PCR_idx = pd.to_datetime(pd.to_datetime(PCR_ds.time.values).strftime('%Y-%m'))

        print('clipping nc-files to extent of shp-file')
        #- GRACE
        try:
            GRACE_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
        except:
            GRACE_data.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)
        GRACE_data.rio.write_crs(self.crs, inplace=True)
        #- PCR-GLOBWB
        try:
            PCR_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
        except:
            PCR_data.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)
        PCR_data.rio.write_crs(self.crs, inplace=True)

        out_dict = {}

        for ID in self.extent_gdf[self.key].unique():

            poly = self.extent_gdf.loc[self.extent_gdf[self.key] == ID]

            print('computing R and RMSE for polygon with key identifier {} {}'.format(self.key, ID))

            # clipping GRACE data-array to shape extent
            GRACE_data_c = GRACE_data.rio.clip(poly.geometry, poly.crs, drop=True)
            # clipping PCR data-array to shape extent
            PCR_data_c = PCR_data.rio.clip(poly.geometry, poly.crs, drop=True)

            mean_val_timestep_GRACE = list()
            mean_val_timestep_PCR = list()

            # compute mean per time step in clipped data-array and append to array
            for i in range(len(GRACE_data_c.time)):
                time = GRACE_data_c.time[i]
                t = pd.to_datetime(time.values)
                mean = float(GRACE_data_c.sel(time=t).mean(skipna=True))
                mean_val_timestep_GRACE.append(mean)
            for i in range(len(PCR_data_c.time.values)):
                time = PCR_data_c.time[i]
                t = pd.to_datetime(time.values)
                mean = float(PCR_data_c.sel(time=t).mean(skipna=True))
                mean_val_timestep_PCR.append(mean)

            # get anomaly
            GRACE_anomaly = mean_val_timestep_GRACE - np.mean(mean_val_timestep_GRACE)
            PCR_anomaly = mean_val_timestep_PCR - np.mean(mean_val_timestep_PCR)

            # create pandas dataframe from data and index arrays
            GRACE_df = pd.DataFrame(data=GRACE_anomaly, index=GRACE_idx, columns=['GRACE data'])
            PCR_df = pd.DataFrame(data=PCR_anomaly, index=PCR_idx, columns=['PCR data'])

            # accounting for missing values in time series (and thus missing index values!)
            GRACE_df = GRACE_df.resample('D').mean().fillna(np.nan).resample('M').mean()
            PCR_df = PCR_df.resample('D').mean().fillna(np.nan).resample('M').mean()

            GRACE_df = GRACE_df.loc[GRACE_df.index >= PCR_df.index.min()]
            GRACE_df = GRACE_df.loc[GRACE_df.index <= PCR_df.index.max()]

            # concatenating both dataframes to drop rows with missing values in one of the columns
            # dropping rows with missing values is import because time extents of both files probably do not match
            final_df = pd.concat([GRACE_df, PCR_df], axis=1).dropna()

            r = spotpy.objectivefunctions.correlationcoefficient(final_df['GRACE data'].values, final_df['PCR data'].values)
            rmse = spotpy.objectivefunctions.rmse(final_df['GRACE data'].values, final_df['PCR data'].values)

            poly_skill_dict = {'R':round(r, 2),
                       'RMSE': round(rmse, 2)}

            out_dict[ID] = poly_skill_dict

        out_df = pd.DataFrame().from_dict(out_dict).T
        
        out_df.index.name = self.key
        gdf_grace_out = self.extent_gdf.merge(out_df, on=self.key)

        return gdf_grace_out