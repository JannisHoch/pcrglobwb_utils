=====
Usage
=====

You can either use the functions of pcrglobwb_utils and integrate them into your bespoke workflow. 
Or you can use some of the pre-built command line functions covering some of the most common workflows.

Within python
--------------------

To use pcrglobwb_utils in a project:

.. code-block:: Python

    import pcrglobwb_utils

You have then all the functions available to be used in a bespoke Python-script for output analysis.

See the jupyter notebook in the :ref:`Examples`  for more information. They also contain links to interactive versions hosted on myBinder.

From command line
---------------------

Alternatively, you can use the command line functionality of pcrglobwb_utils. There are currently two kinds of applications for which command line scripts are developed.

First, for validating timeseries of simulated discharge. This can be done using GRDC-data (for selected files or entire batch runs) or by providing observations in an Excel-file. 
The latter option then requires a geojson-file with the locations of the observation stations in the Excel-file.

And second, to validate timeseries of any other modle output with gridded observations in netCDF-format. The validation will be performed at a user-specified aggregation level. 
This level is defined by providing a geojson-file containing one or multiple polygons for which the spatial mean is computed per time step.

Top-level information abou the command line scripts can be accessed via

.. code-block:: console

    $ pcr_utils_evaluate --help

For an elaborated overview, please see the documention of the various command line functions.

.. toctree::
   :numbered:
   :maxdepth: 1

   Timeseries analysis <usage/timeseries>
   Analysis per polygon <usage/polygon>


