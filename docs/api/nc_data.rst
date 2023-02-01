Simulated data
======================

From netCDF files
----------------------

PCR-GLOBWB writes output to netCDF4-files. It is thus necessary to have the right tools to read and process the data.

The 'from_nc' class
^^^^^^^^^^^^^^^^^^^^

``pcrglobwb_utils`` has a dedicated class to extract values from a netCDF-file for a given location. 
Also, the timeseries can be resampled in time.

.. autoclass:: sim_data.from_nc
    :members:

    
