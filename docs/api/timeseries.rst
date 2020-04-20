Retrieving timeseries
======================

From points
-----------

.. currentmodule:: timeseries
.. autoclass:: nc_data

.. currentmodule:: timeseries.nc_data

PCR-GLOBWB writes output to netCDF4-files. It is thus necessary to have the right tools to read and process the data.

Of particular interest are timeseries of, for instance, discharge to validate model output.

With these methods the work is hopefully bit easier:

.. autosummary::
   :toctree: generated/
   :nosignatures:

   read_values_at_indices
   calc_montly_avg
   validate_results


    
