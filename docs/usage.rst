=====
Usage
=====

Within python
--------------------

To use pcrglobwb_utils in a project:

.. code-block:: Python

    import pcrglobwb_utils

You have then all the functions available to be used in a bespoke Python-script for output analysis.

From command line
---------------------

Alternatively, you can use the command line functionality of pcrglobwb_utils.

In the current version, it allows you to either validate one nc-file against observations at a GRDC-station or to benchmark different nc-files at one locations specified by lat/lon.

For the start, two convenience scripts are provided as well as two shell-scripts facilitating the use of pcrglobwb_utils for command line applications.

Convenience script for model validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For this script, it is only possible to use one output nc-file together with a text file containing observed values and following the default GRDC format.
Note that there is a dedicated function in the module to also read csv-files with other formatting, but this is not supported in command line application.

.. code-block:: Python

    python ./scripts/evaluate_output.py simulation.nc GRDCfile.txt outputDir

Alternatively, you can use the shell-script

.. code-block:: console

    bash run_example_evaluation.sh

The functions called in the script will provide a plot, a pandas-dataframe, and a dictionary with the results of several objective functions in a user-defined output directory.

Convenience script for model benchmarking
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes, a model is run several times with different settings or different models are run for the same study area.
In both cases, it may be useful to compare output at the same location for model benchmarking.

This can be done with by calling the script as follows:

.. code-block:: Python

    python ./scripts/benchmark_output.py nc_file_1.nc nc_file_2.nc ... nc_file_x.nc lat lon outputDir

Alternatively, you can use the shell-script

.. code-block:: console

    bash run_example_benchmark.sh

For the output files 1 until x, values are read from a location with the specified lon/lat and a plot as well as a pandas-dataframe stored in a user-defined output directory.

.. note:: The functionality of rasterio is used here to convert the lat/lon information to the corresponding row/col index.

    


