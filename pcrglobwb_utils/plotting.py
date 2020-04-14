import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import rasterio as rio
import spotpy as sp
import os, sys

def plot_var_at_timestep(fo, var_name, time, savefig=False, outdir=None):
    """Plots variable at a given timestep from 2D netcdf file.
    
    Arguments:
        fo {str} -- path to nc-file
        var_name {str} -- variable name to be plotted
        time {str} -- time at which variable is to be plotted
    
    Keyword Arguments:
        savefig {bool} -- whether or not to save the figure (default: {False})
        outdir {str} -- path to location where figure is to be stored (default: {None})
    """
    
    if savefig == True and outdir == None:
        os.sys.exit('No output directory for saving figure specified.')
    
    ds = xr.open_dataset(fo)
    
    plt.figure()
    ds[var_name].sel(time=time).plot()
        
    if savefig:
        f_name = var_name + '_' + time + '.png'
        plt.savefig(os.path.join(outdir, f_name), dpi=300)