import pandas as pd
import xarray as xr
import numpy as np
import geopandas as gpd
import rasterio
import cartopy
from shutil import rmtree
import rioxarray as rio
import matplotlib.pyplot as plt
import datetime
import spotpy
import os, sys
from shapely.geometry import mapping

#TODO: remove all stupid print statements

class validate_per_shape:
    """Initializing object for validating output for area provided by shp-file.

    Args:
        shp_fo (str): Path to shp-file defining the area extent for validation
        crs (str, optional): Definition of projection system in which validation takes place. Defaults to 'epsg:4326'.
        out_dir (str, optional): Path to output directory. In None, then no output is stored. Defaults to None.
    """      

    def __init__(self, shp_fo, shp_key, crs='epsg:4326', out_dir=None):
  
        self.shp_fo = shp_fo
        self.key = shp_key
        self.crs = crs

        print('reading shp-file {}'.format(os.path.abspath(self.shp_fo)))
        self.extent_gdf = gpd.read_file(self.shp_fo, crs=self.crs)

        if self.out_dir != None:
            self.out_dir = os.path.abspath(out_dir)
            if os.path.isdir(out_dir):
                rmtree(out_dir)
            os.makedirs(out_dir)
            print('saving output to {}'.format(self.out_dir))

    def against_GLEAM(self, PCR_nc_fo, GLEAM_nc_fo, PCR_var_name='total_evaporation', GLEAM_var_name='E', convFactor=1000, plot=False):
        """With this function, simulated land surface evaporation (or another evaporation output) from PCR-GLOBWB can be validated against evaporation data from GLEAM (or any other evaporation data in GLEAM).
        Works with monthly totals and computes monthly area averages per time step from it.

        Args:
            PCR_nc_fo (str): Path to netCDF-file containing evaporation output from PCR-GLOBWB.
            GLEAM_nc_fo (str): Path to netCDF-file containing GLEAM evaporation data.
            PCR_var_name (str, optional): netCDF variable name in PCR-GLOBWB output. Defaults to 'land_surface_evaporation'.
            GLEAM_var_name (str, optional): netCDF variable name in GLEAM data. Defaults to 'E'.
            convFactor (int, optional): conversion factor to convert PCR-GLOBWB units to GLEAM units. Defaults to 1000.
            plot (bool, optional): Whether or not to plot the resulting timeseries. Defaults to False.

        Returns:
            list: list containing computed values for R (correlation coefficient) and RMSE (root mean square error) computed with PCR-GLOBWB and GLEAM timeseries.
            dataframe: dataframe containing the timeseries including missing values (NaN).
        """        

        #TODO: make this work with multiple polygons stored in the shape file, e.g. by going through all rows in gpd-object
        #TODO: or, if no shp_fo is specified, by clipping it to extent (xmin, ymin, xmax, ymax) of PCR-GLOBWB nc-file

        print('reading files for GLEAM {0} and PCR-GLOBWB {1}'.format(os.path.abspath(GLEAM_nc_fo), os.path.abspath(PCR_nc_fo)))
        GLEAM_ds = xr.open_dataset(GLEAM_nc_fo)
        PCR_ds = xr.open_dataset(PCR_nc_fo)

        print('extract raw data from nc-files')
        GLEAM_data = GLEAM_ds[GLEAM_var_name] # mm
        PCR_data = PCR_ds[PCR_var_name] # m

        print('clipping nc-files to extent of shp-file')
        try:
            GLEAM_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
        except:
            GLEAM_data.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)
        GLEAM_data.rio.write_crs(self.crs, inplace=True)
        GLEAM_data = GLEAM_data.rio.clip(self.extent_gdf.geometry, self.extent_gdf.crs, drop=True)

        try:
            PCR_data.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)
        except:
            PCR_data.rio.set_spatial_dims(x_dim='longitude', y_dim='latitude', inplace=True)
        PCR_data.rio.write_crs(self.crs, inplace=True)
        PCR_data = PCR_data.rio.clip(self.extent_gdf.geometry, self.extent_gdf.crs, drop=True)

        print('multiplying PCR data with 1000 to convert from [m] to [mm]')
        PCR_data = PCR_data * convFactor # m * 1000 = mm

        print('calculating mean per timestep over clipped area')
        GLEAM_arr = []
        for time in GLEAM_data.time.values:
            mean = float(GLEAM_data.T.sel(time=time).mean(skipna=True))
            GLEAM_arr.append(mean)
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

        r = spotpy.objectivefunctions.correlationcoefficient(final_df_noNaN[GLEAM_var_name].values, final_df_noNaN[PCR_var_name].values)
        rmse = spotpy.objectivefunctions.rmse(final_df_noNaN[GLEAM_var_name].values, final_df_noNaN[PCR_var_name].values)

        print('done')

        if plot:
            print('plotting timeseries...')
            fig, ax = plt.subplots(1, 1, figsize=(20,10))
            final_df.plot(ax=ax, legend=True)
            ax.set_title('monthly spatially averaged evapotranspiration')
            ax.set_ylabel('evapotranspiration [mm]')
            ax.text(0.88, 0.05, 'r={}'.format(round(r, 2)), transform=ax.transAxes)
            ax.text(0.88, 0.02, 'rmse={}'.format(round(rmse, 2)), transform=ax.transAxes)
            if self.out_dir != None:
                plt.savefig(os.path.join(self.out_dir, 'timeseries_monthly_spatial_mean_{0}_and_{1}_GLEAM_validation.png'.format(GLEAM_varName, PCR_varName)), dpi=300)

            print('...and bias')
            fig, ax = plt.subplots(1, 1, figsize=(20,10))
            (final_df[GLEAM_var_name] - final_df[PCR_var_name]).plot(ax=ax)
            ax.set_title('BIAS monthly spatially averaged evapotranspiration (GLEAM - PCR-GLOBWB)')
            ax.set_ylabel('evapotranspiration BIAS [mm]')
            if self.out_dir != None:
                plt.savefig(os.path.join(self.out_dir, 'timeseries_monthly_spatial_mean_{0}_and_{1}_GLEAM_validation_BIAS.png'.format(GLEAM_varName, PCR_varName)), dpi=300)

        return [r, rmse], final_df

    def against_GRACE(self, PCR_nc_fo, GRACE_nc_fo, PCR_var_name='total_thickness_of_water_storage', GRACE_var_name='lwe_thickness', convFactor=100, plot=False):
        """With this function, simulated totalWaterStorage output from PCR-GLOBWB can be validated against GRACE-FO observations. Yields timeseries of anomalies.
        Works with monthly averages and computes monthly area averages per time step from it.

        Args:
            PCR_nc_fo (str): Path to netCDF-file containing totalWaterStorage output from PCR-GLOBWB.
            GRACE_nc_fo (str): Path to netCDF-file containing GRACE-FO data
            PCR_var_name (str, optional): netCDF variable name in PCR-GLOBWB output. Defaults to 'total_thickness_of_water_storage'.
            GRACE_var_name (str, optional): netCDF variable name in GRACE-FO data. Defaults to 'lwe_thickness'.
            convFactor (int, optional): conversion factor to convert PCR-GLOBWB units to GRACE-FO units. Defaults to 100.
            plot (bool, optional): Whether or not to plot the resulting timeseries. Defaults to False.

        Returns:
            list: list containing computed values for R (correlation coefficient) and RMSE (root mean square error) computed with PCR-GLOBWB and GLEAM timeseries.
            dataframe: dataframe containing the timeseries including missing values (NaN).
        """        
        
        print('reading GRACE file {}'.format(os.path.abspath(GRACE_nc_fo)))
        GRACE_ds = xr.open_dataset(GRACE_nc_fo)
        print('reading PCR-GLOBWB file {1}'.format(os.path.abspath(PCR_nc_fo)))
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
            dest_bounds = poly.total_bounds
            dest_srs = poly.crs

            print('computing R and RMSE for polygon with key identifier {} {}'.format(self.key, ID))

            # clipping GRACE data-array to shape extent
            GRACE_data_c = GRACE_data.rio.clip(poly.geometry, poly.crs, drop=True)
            # clipping PCR data-array to shape extent
            PCR_data_c = PCR_data.rio.clip(poly.geometry, poly.crs, drop=True)

            mean_val_timestep_GRACE = list()
            mean_val_timestep_PCR = list()

            # compute mean per time step in clipped data-array and append to array
            for time in GRACE_ds.time.values:
                mean = float(GRACE_data_c.sel(time=time).mean(skipna=True))
                mean_val_timestep_GRACE.append(mean)
            for time in PCR_ds.time.values:
                mean = float(PCR_data_c.sel(time=time).mean(skipna=True))
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

        self.gdf_grace_out = self.extent_gdf.merge(out_df, on=self.key)

        if plot:
            fig, axes = plt.subplots(1, 2, figsize=(20,10), sharey=True, subplot_kw={'projection': cartopy.crs.PlateCarree()})
            self.gdf_grace_out.plot(column='R', ax=axes[0], legend=True, cmap='Reds', legend_kwds={'label': "correlation R", 'orientation': "horizontal"})
            axes[0].set_title('R')
            self.gdf_grace_out.plot(column='RMSE', ax=axes[1], legend=True, legend_kwds={'label': "Root Mean Square Error RMSE", 'orientation': "horizontal"})
            axes[1].set_title('RMSE')
            for ax in axes:
                self.gdf_grace_out.boundary.plot(ax=ax, color='k')
                ax.add_feature(cartopy.feature.LAND)
                ax.add_feature(cartopy.feature.OCEAN)
                ax.add_feature(cartopy.feature.COASTLINE)
                ax.add_feature(cartopy.feature.BORDERS, linestyle=':')
                ax.set_ylabel('longitude')
                ax.set_xlabel('latitude')
                ax.set_xlim(self.gdf_grace_out.total_bounds[0], self.gdf_grace_out.total_bounds[2])
                ax.set_ylim(self.gdf_grace_out.total_bounds[1], self.gdf_grace_out.total_bounds[3])
            if self.out_dir != None:
                plt.savefig(os.path.join(self.out_dir, 'evaluation_per_polygon.png'), dpi=300)

        return self.gdf_grace_out