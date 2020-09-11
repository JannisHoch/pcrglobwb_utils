import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import rasterio as rio
import spotpy as sp
import os, sys

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
    ds = rio.open(fo)
    
    # get indices
    row, col = ds.index(lon, lat)
    
    # close file
    ds.close()
    
    return row, col

def get_idx_as_strftime(df, strftime_format='%Y-%m-%d'):

    idx = df.index.strftime(strftime_format)

    return idx