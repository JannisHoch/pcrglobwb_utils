import pcrglobwb_utils
import xarray as xr
import pandas as pd
import numpy as np
import geopandas as gpd
import rioxarray as rio
import rasterio
import os, sys

def print_versions():

    print('pcrglobwb_utils version {}'.format(pcrglobwb_utils.__version__))
    print('pandas version {}'.format(pd.__version__))
    print('xarray version {}'.format(xr.__version__))
    print('numpy version {}'.format(np.__version__))
    print('geopandas version {}'.format(gpd.__version__))
    print('rasterio version {}'.format(rasterio.__version__))
    print('rioxarray version {}'.format(rio.__version__))

def find_indices_from_coords(fo, lon, lat):
    """Read in georeferenced 2D file (e.g. tiff or nc-file) and get row and column indices corresponding to given longitude and latitude information.

    Arguments:
        fo (str): georeferenced 2D file
        lon (float): longitude of point
        lat (float): latitude of point

    Returns:
        float: row corresponding to longitude
        float: column corresponding to latitude
    """
    
    # open file
    ds = rasterio.open(fo)
    
    # get indices
    row, col = ds.index(lon, lat)
    
    # close file
    ds.close()
    
    return row, col

def get_idx_as_strftime(df, strftime_format='%Y-%m-%d'):

    idx = df.index.strftime(strftime_format)

    return idx