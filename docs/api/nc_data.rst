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

Functions
^^^^^^^^^^^^^^^^^^^^

The underlying function to extract and validate data are.

.. autofunction:: sim_data.find_indices_from_coords

.. autofunction:: sim_data.apply_window_search

.. autofunction:: sim_data.read_at_indices

.. autofunction:: sim_data.read_at_coords

.. autofunction:: sim_data.validate_timeseries

.. note:: 

    Functions for resampling in time are part of the :ref:`time functions <time_funcs>` module.

    
