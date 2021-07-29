Analysis per polygon
======================================

Output from PCR-GLOBWB can be validated against any other gridded dataset as long as it is a netCDF-file.

**Settings**

In each file containing polygons (``PLY``), it is important that each polygon has a unique identifier ``ply-id``.
For each of the polygons, the script will compute the spatial average for both simulations and observations for each time step.
From the resulting timeseries, r, MSE, and RMSE are derived.

If the units between simulations and observations are not identical, it is possible to apply a ``--conversion-factor`` which will be multiplied with the simulated values. The default values is 1.

Should it be required to perform the analysis in another coordinate system than EPSG 4326, it can be provided via ``--coordinate-system``. Default is EPSG 4326.

In some instances, anomalies are required instead of the raw timeseries. By specifying ``--anomaly``, the scripts derives the anomalies of observation and simulation per time step. Default setting is off.

For some variables, PCR-GLOBWB outputs monthly totals. In case the observations are monthly averages, it is possible to derive monthly values by dividing the total with the number of days per month. 
This can be activated by setting the ``--sum`` switch. Default is off.

For a quick visual analysis of the output, it is possible to activate the ``--plot`` switch. Default is off.

**Code documentation**

.. code-block:: console

    Usage: pcr_utils_evaluate poly [OPTIONS] PLY SIM OBS OUT

    Computes r, MSE, and RMSE for multiple polygons as provided by a shape-file
    between simulated and observed data. Each polygon needs to have a unique
    ID. Contains multiple options to align function settings with data and
    evaluation properties.

    Returns a GeoJSON-file of r, MSE, and RMSE per polygon, and if specified as
    simple plot.  
    Also returns scores of r, MSE, and RMSE per polygon as dataframe.

    PLY: path to shp-file or geojson-file with one or more polygons.

    SIM: path to netCDF-file with simulated data.

    OBS: path to netCDF-file with observed data.

    OUT: Path to output folder. Will be created if not there yet.

    Options:
        -id, --ply-id TEXT              unique identifier in file containing polygons.
        -o, --obs_var_name TEXT         variable name in observations.
        -s, --sim_var_name TEXT         variable name in simulations.
        -cf, --conversion-factor INT    conversion factor applied to simulated values to align variable units.
        -crs, --coordinate-system TEXT  coordinate system.
        --anomaly / --no-anomaly        whether or not to compute anomalies.
        --sum / --no-sum                whether or not the simulated values are monthly totals or not.
        --plot / --no-plot              whether or not to save a simple plot of results.
        --verbose / --no-verbose        more or less print output.
        --help                          Show this message and exit.

**Example**

In this example, simulated ``total_thickness_of_water_storage`` is validated against ``lwe_thickness`` from GRACE. 
Since GRACE data is in [cm], simulated data is converted from [m] by multiplying with 100.
Also, the anomaly per time step is determined.

.. code-block:: console

    $ shp='/path/to/polygon.geojson'
    $ obs='/path/to/GRACE.nc'
    $ sim='/path/to/model_output.nc'
    $ out='./OUT/'

    $ pcr_utils_evaluate poly -o lwe_thickness -s total_thickness_of_water_storage -cf 100 -id ID --anomaly $shp $sim $obs $out