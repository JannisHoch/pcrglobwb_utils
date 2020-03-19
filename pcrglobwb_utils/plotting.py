import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import rasterio as rio
import spotpy as sp
import os, sys

def plot_var_at_timestep(fo, var_name, time, savefig=False, outdir=None):
    """
    plots variable at a given timestep from 2D netcdf file.
    
    input:
    ------
    fo {str} = georeferenced 2D nc-file
    var_name {str} = name of variable to be retrieved in nc-file
    time {str} = time at which variable is plotted
    savefig {bool} = True/False whether plot is saved to png at 300 dpi (default: False)
    outdir {str} = output directory where plot is stored (default: None)
    
    output:
    -------
    None
    """
    
    if savefig == True and outdir == None:
        os.sys.exit('No output directory for saving figure specified.')
    
    ds = xr.open_dataset(fo)
    
    plt.figure()
    ds[var_name].sel(time=time).plot()
        
    if savefig:
        f_name = var_name + '_' + time + '.png'
        plt.savefig(os.path.join(outdir, f_name), dpi=300)