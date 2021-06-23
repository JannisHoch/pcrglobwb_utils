=====
Usage
=====

Within python
--------------------

To use pcrglobwb_utils in a project:

.. code-block:: Python

    import pcrglobwb_utils

You have then all the functions available to be used in a bespoke Python-script for output analysis.

See the jupyter notebook in the examples folder for a (limited) overview of the functions and their application.

From command line
---------------------

Alternatively, you can use the command line functionality of pcrglobwb_utils.

Discharge validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This scripts faciliates the validation of simulated discharge against one or more GRDC stations.

.. code-block:: console

    Usage: pcr_eval_timeseries [OPTIONS] NCF OUT

    Uses pcrglobwb_utils to validate simulated time series (currently only
    discharge is supported)  with observations (currently only GRDC) for one
    or more stations. The station name and file with GRDC data need to be
    provided in a separate yml-file. Per station, it is also possible to
    provide lat/lon coordinates which will supersede those provided by GRDC.
    The script faciliates resampling to other temporal resolutions.

    Returns a csv-file with the evaluated time series (OBS and SIM),  a csv-
    file with the resulting scores (KGE, r, RMSE, NSE),  and if specified a
    simple plot of the time series.

    NCF: Path to the netCDF-file with simulations.      
    
    OUT: Main output directory. Per station, a sub-directory will be created.

    Options:
        -v, --var-name TEXT       variable name in netCDF-file
        -y, --yaml-file TEXT      path to yaml-file referencing to multiple GRDC-
                                    files.

        -t, --time-scale TEXT     time scale at which analysis is performed if
                                    upscaling is desired: month, year, quarter

        --plot / --no-plot        simple output plots.
        --verbose / --no-verbose  more or less print output.
        --help                    Show this message and exit.

Evaluation per polygon
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Output from PCR-GLOBWB can be validated against any other gridded dataset as long as it is a netCDF-file.

.. code-block:: console

    Usage: pcr_eval_polygons [OPTIONS] SHP SIM OBS OUT

    Computes r and RMSE for multiple polygons as provided by a shape-file
    between simulated and observed data. Each polygon needs to have a unique
    ID. Contains multiple options to align function settings with data and
    evaluation properties.

    Returns a GeoJSON-file of r and RMSE per polygon, and if specified as
    simple plot.  Also returns scores of r and RMSE as dataframe.

    SHP: path to shp-file with one or more polygons.

    SIM: path to netCDF-file with simulated data.

    OBS: path to netCDF-file with observed data.

    OUT: Path to output folder. Will be created if not there yet.

    Options:
        -id, --shp-id TEXT              unique identifier in shp-file.
        -o, --obs_var_name TEXT         variable name in observations.
        -s, --sim_var_name TEXT         variable name in simulations.
        -cf, --conversion-factor INTEGER
                                        conversion factor applied to simulated
                                        values to align variable units.

        -crs, --coordinate-system TEXT  coordinate system.
        --anomaly / --no-anomaly        whether or not to compute anomalies.
        --sum / --no-sum                whether or not the simulated values or
                                        monthly totals or not.

        --plot / --no-plot              whether or not to save a simple plot fo
                                        results.

        --verbose / --no-verbose        more or less print output.
        --help                          Show this message and exit.

Model benchmarking
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. important:: 

    This script has not been updated yet and thus potentially contains outdated content and workflow!

Sometimes, a model is run several times with different settings or different models are run for the same study area.
In both cases, it may be useful to compare output at the same location for model benchmarking.

This can be done with by calling the script as follows:

.. code-block:: console

    $ python ./scripts/benchmark_output.py nc_file_1.nc nc_file_2.nc ... nc_file_x.nc lat lon outputDir
    


