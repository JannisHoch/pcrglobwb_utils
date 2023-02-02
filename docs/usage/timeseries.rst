.. _usage_timeseries:

Timeseries analysis
======================================

These scripts faciliate the validation of simulated timeseries. 
This can be done in multiple ways. Either for GRDC-stations and the associated default GRDC file standard. In this case, most of the meta-data can be extracted directly from file. 
The GRDC-script is limited to evaluating discharge simulations.
Or via an Excel-file together with a geojson-file providing the locations of all stations. with the Excel-script, any simulated variable can be evaluated.

Validation with GRDC-data
-------------------------

**Code documentation**

.. code-block:: console

    Usage: pcru_eval_tims grdc [OPTIONS] NCF DATA_LOC OUT

    Uses pcrglobwb_utils to validate simulated time series (currently only
    discharge is supported)  with observations (currently only GRDC) for one or
    more stations. The station name and file with GRDC data need to be provided
    in a separate yml-file. Per station, it is also possible to provide lat/lon
    coordinates which will supersede those provided by GRDC. The script
    faciliates resampling to other temporal resolutions.

    Returns a csv-file with the evaluated time series (OBS and SIM), a csv-file
    with the resulting scores (KGE, R2, RMSE, RRMSE, NSE),  and if specified a
    simple plot of the time series. If specified, it also returns a geojson-file
    containing KGE values per station evaluated.

    NCF: Path to the netCDF-file with simulations.

    DATA_LOC: either yaml-file or folder with GRDC files.      
    
    OUT: Main output directory. Per station, a sub-directory will be created.

    Options:
    -v, --var-name TEXT             variable name in netCDF-file
    -gc, --grdc-column TEXT         name of column in GRDC file to be read (only
                                    used with -f option)
    -e, --encoding TEXT             encoding of GRDC-files.
    -sf, --selection-file TEXT      path to file produced by pcru_sel_grdc
                                    function (only used with -f option)
    -t, --time-scale TEXT           time scale at which analysis is performed if
                                    resampling is desired. String needs to
                                    follow pandas conventions.
    -N, --number-processes INTEGER  number of processes to be used in
                                    multiprocessing.Pool()- defaults to number
                                    of CPUs in the system.
    --verbose / --no-verbose        more or less print output.
    --help                          Show this message and exit.

**Settings**

There are two options how to use this function. What they have in common is that they read a variable ``--var-name`` from a netCDF-file ``NCF`` containing simulated data. 
The variable name default to 'discharge'.

Also, the command line script will create individual sub-folders per evaluated station in the main output folder ``OUT``. 
Per sub-folder, a csv-file with the compuated metrics will be stored along with the underlying timeseries.

Option 1: Detailed analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By providing one yml-file as ``DATA_LOC`` which has the subsequent structure for each location to be analysed:
 
.. code-block:: yaml

    <location_name>
        file: <path/to/GRDC_file>
        lat: <latitude value>
        lon: <longitude value>
        column: <latitude value>
    <location_name>
        file: <path/to/GRDC_file>
        lat: <latitude value>
        lon: <longitude value>
        column: <latitude value>

``file`` needs to point to the GRDC file corresponding to this station. It can be a relative or absolute path.

``lat``, ``lon``, and ``column`` are optional settings. 

By default, ``pcrglobwb_utils`` retrieves latitude and longitude information from the meta-data stored in each GRDC-file, 
and performs a window search around this location to reduce the risk of a mis-match between GRDC coords and location in the model output.
In some cases, this may still not be sufficient and hence coordinates can be provided manually via the yaml-file.

GRDC-files have often multiple columns with data. ``pcrglobwb_utils`` uses ``' Calculated'`` as default. 
If another column is supposed to be read, this can be specified here.

**Example**

In this example, we make use of a yml-file to validate discharge at locations Obidos and Jaturana (both located in the Amazon).

.. code-block:: yaml

    Obidos:
        file: 'path/to/files/3629000_Obidos.day'
        column: ' Original'

    Jaturana:
        file: 'path/to/files/3627000_Jatuarana.day'
        lon: -59.65
        lat: -3.05
        column: ' Calculated'

While we use the GRDC coordinates for Obidos, we specify them for Jaturana. Also, the column to be read in the GRDC-file differs per station.

The daily values are resampled to monthly values in this example.

.. code-block:: console

    $ yaml_file='path/to/yaml_file.yml'
    $ sim='path/to/model_discharge_output.nc'
    $ out='./OUT/'
    $ pcru_eval_tims grdc $sim $yaml_file $out_dir -t M 

Option 2: batch analysis
^^^^^^^^^^^^^^^^^^^^^^^^^ 

If a batch of stations is to be analysed, it is possible to provide a folder path where GRDC-files are stored as ``DATA_LOC``.
``pcrglobwb_utils`` will then read all files, retrieve meta-data, and perform the analysis.
It is possible to only select stations fulfilling certain requirements by providing a file containing selected stations with option ``--selection-file``.
This has the advantage that not all files need to be specified in a yaml-file, but on the downside gives less possibilites to finetune the analysis.
The only thing that can be provided is the column name in the GRDC file batch via ``--grdc-column``.

.. note:: 

    To reduce the risk of stations not being located in the 'right' cell, a window search is automatically performed to find the best matching cell.

In both cases, it is possible to resample simulated and observed data to larger time steps with ``--time-scale``.

To speed up computations, it is possible to parallelise the evaluation by specifying a number of cores as ``-number-processes``. 
Note that the number of cores used may be scaled down to either the number of stations available or the number of cores available.

**Example**

In the example above, both GRDC files are stored in the folder ``path/to/files``. Instead of specifying these files manually, we can just analyse the entire folder content.

When analysing many files, it may make sense to parallelise this process, here across 8 cores.
And again, we want to perform the analysis at the monthly scale.

.. code-block:: console

    $ folder='path/to/files/'
    $ sim='path/to/model_discharge_output.nc'
    $ out='./OUT/'
    $ pcru_eval_tims grdc $sim $folder $out_dir -N 8 -t M

Validation with Excel-file
---------------------------

If observations are not sources from GRDC, they can be stored in an Excel-file as an alternative.

.. attention:: 

    This settings is by far less well tested than the use of GRDC data.

**Settings**

Key inputs are a netCDF-file containing simulated values (``NCF``). 
With the option ``--var-name``, the variable name can be specified. By default, variable 'discharge' will be read.

Observed values are provided with an Excel-file (``XLS``). 
The file needs to have two or more columns. The first column contains the dates of observed values. All other columns contain then the observed values themselves.
The first row must contain the names of the stations to be analysed (except for the first column which does not have to have a header).

The list of stations to be analysed is retrieved from a geojson-file (``LOC``). 
It contains the locations (lat/lon) of the stations and also a unique identifier per station which must be provided with ``--location-id``.

The command line script will create individual sub-folders per evaluated station in the main output folder ``OUT``. 
Per sub-folder, a csv-file with the compuated metrics will be stored along with the underlying timeseries.

With the ``--geojson / --no-geojson`` switch, a geojson-file will be stored to ``OUT`` containing KGE values per evaluated station (or not). Defaults to True.

The ``--plot`` switch activates printing of simple plots of the timeseries per evaluated station.

.. note:: 

    While the GRDC script works only with simulated discharge, the Excel script provided more freedom and can be used to evaluate any timeseries and variable simulated with PCR-GLOBWB!

**Code documentation**

.. code-block:: console

    Usage: pcr_utils_evaluate excel [OPTIONS] NCF XLS LOC OUT

    Uses pcrglobwb_utils to validate simulated time series with observations
    for one or more stations. The station names and their locations need to be
    provided via geojson-file. Observations are read from Excel-file and
    analysis will be performed for all stations with matching names in Excel-
    file columns and geojson-file. The Excel-file must have only one sheet
    with first column being time stamps of observed values, and all other
    columns are observed values per station. These columns must have a header
    with the station name. The script faciliates resampling to other temporal
    resolutions.

    Returns a csv-file with the evaluated time series (OBS and SIM),  a csv-
    file with the resulting scores (KGE, r, RMSE, NSE),  and if specified a
    simple plot of the time series. If specified, it also returns a geojson-
    file containing KGE values per station evaluated.

    NCF: Path to the netCDF-file with simulations.

    XLS: Path to Excel-file containing dates and values per station.

    LOC: Path to geojson-file containing location and names of stations.

    OUT: Main output directory. Per station, a sub-directory will be created.

    Options:
        -v, --var-name TEXT             variable name in netCDF-file
        -id, --location-id TEXT         unique identifier in locations file.
        -t, --time-scale TEXT           time scale at which analysis is performed if upscaling is desired: month, year, quarter.
        --plot / --no-plot              simple output plots.
        --geojson / --no-geojson        create GeoJSON file with KGE per GRDC station.
        --verbose / --no-verbose        more or less print output.
        --help                          Show this message and exit.

**Example**

In this example, each station in the geojson-file with a unqiue identifier 'station' will be matched with the columns in the Excel-file to validate simulated sediment transport.

.. code-block:: console

    $ sim='path/to/model_output.nc'
    $ excel='path/to/data.xlsx'
    $ loc='path/to/stations.geojson'
    $ out='./OUT/'
    $ pcr_utils_evaluate excel -v sedimentTransport -id station $sim $excel_file $loc $out

    


