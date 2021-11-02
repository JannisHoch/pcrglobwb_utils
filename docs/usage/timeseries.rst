Timeseries analysis
======================================

These scripts faciliate the validation of simulated timeseries. 
This can be done in multiple ways. Either for GRDC-stations and the associated default GRDC file standard. In this case, most of the meta-data can be extracted directly from file. The GRDC-script is limited to evaluating discharge simulations.
Or via an Excel-file together with a geojson-file providing the locations of all stations. with the Excel-script, any simulated variable can be evaluated.

Validation with GRDC-data
-------------------------

**Settings**

There are two options how to use this function. What they have in common is that they read a variable ``--var-name`` from a netCDF-file ``NCF`` containing simulated data. 
The variable name default to 'discharge'.

Also, the command line script will create individual sub-folders per evaluated station in the main output folder ``OUT``. 
Per sub-folder, a csv-file with the compuated metrics will be stored along with the underlying timeseries.

Option 1: By providing one yml-file with ``--yaml-file`` which has the subsequent structure for each location to be analysed:
 
.. code-block::

    <location_name>
        file: <path/to/GRDC_file>
        lat: <latitude value>
        lon: <longitude value>
        column: <latitude value>

Note that the properties *lat*, *lon*, and *column* are optional. 
By default, pcrglobwb_utils retrieves latitude and longitude information from the meta-data stored in each GRDC-file.
In some cases, these coordinates may not match with the model river network and thus need to be provided manually.
GRDC-files have often multiple columns with data. pcrglobwb_utils uses ' Calculated' as default. If another column is supposed to be read, this can be specified here.

Option 2: If a batch of stations is to be analysed, it is possible to provide a folder path with ``--folder`` where GRDC-files are stored.
pcrglobwb_utils will then read all files, retrieve meta-data, and perform the analysis.
This has the advantage that not all files need to be specified in a yaml-file, but on the downside gives less possibilites to finetune the analysis.
The only thing that can be provided is the column name in the GRDC file batch via ``--grdc-column``.

In both cases, it is possible to resample simulated and observed data to larger time steps with ``--time-scale``.

With the ``--geojson / --no-geojson`` switch, a geojson-file will be stored to ``OUT`` containing KGE values per evaluated station (or not). Defaults to True.

The ``--plot`` switch activates printing of simple plots of the timeseries per evaluated station.

**Code documentation**

.. code-block:: console

    Usage: pcr_utils_evaluate grdc [OPTIONS] NCF OUT

    Uses pcrglobwb_utils to validate simulated time series (currently only
    discharge is supported)  with observations (currently only GRDC) for one
    or more stations. The station name and file with GRDC data need to be
    provided in a separate yml-file. Per station, it is also possible to
    provide lat/lon coordinates which will supersede those provided by GRDC.
    The script faciliates resampling to other temporal resolutions.

    Returns a csv-file with the evaluated time series (OBS and SIM),  a csv-
    file with the resulting scores (KGE, r, RMSE, NSE),  and if specified a
    simple plot of the time series. If specified, it also returns a geojson-
    file containing KGE values per station evaluated.

    NCF: Path to the netCDF-file with simulations.      
    
    OUT: Main output directory. Per station, a sub-directory will be created.

    Options:
        -v, --var-name TEXT       variable name in netCDF-file
        -y, --yaml-file TEXT      path to yaml-file referencing to multiple GRDC-files.
        -f, --folder PATH         path to folder with GRDC-files.
        -gc, --grdc-column TEXT   name of column in GRDC file to be read (only used with -f option)
        -t, --time-scale TEXT     time scale at which analysis is performed if upscaling is desired: month, year, quarter
        --geojson / --no-geojson  create GeoJSON file with KGE per GRDC station.
        --plot / --no-plot        simple output plots.
        --verbose / --no-verbose  more or less print output.
        --help                    Show this message and exit.

**Examples**

In this example, we make use of a yml-file to validate discharge at location Jaturana (located in the Amazon) with specified lat/lon values and column to be read.

.. code-block::

    Jaturana:
        file: './files/3627000_Jatuarana.day'
        lon: -59.65
        lat: -3.05
        column: ' Original'

The daily values are resampled to quarterly values.

.. code-block:: console

    $ yaml_file='path/to/yaml_file.yml'
    $ sim='path/to/model_output.nc'
    $ out='./OUT/'
    $ pcr_utils_evaluate grdc -y $yaml_file -t quarter $sim $out_dir 

If we had more GRDC files stored in the same folder, we could also perform a batch analysis.

.. code-block:: console

    $ folder='path/to/files/'
    $ sim='path/to/model_output.nc'
    $ out='./OUT/'
    $ pcr_utils_evaluate grdc -f $folder $sim $out_dir 

Validation with Excel-file
---------------------------

If observations are not sources from GRDC, they can be stored in an Excel-file as an alternative.

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

    


