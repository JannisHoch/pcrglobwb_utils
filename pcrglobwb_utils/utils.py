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

def get_idx_as_strftime(df, strftime_format='%Y-%m-%d'):

    idx = df.index.strftime(strftime_format)

    return idx