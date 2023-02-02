Simulated data
======================

From netCDF files
----------------------

``pcrglobwb_utils`` has a dedicated class to extract values from a netCDF-file for a given location. 
Also, the timeseries can be resampled in time.

.. currentmodule:: pcrglobwb_utils.sim_data

.. autoclass:: from_nc

   .. rubric:: Methods Summary

   .. autosummary::

      ~from_nc.get_copy
      ~from_nc.get_indices
      ~from_nc.get_values_from_coords
      ~from_nc.get_values_from_indices
      ~from_nc.to_annual
      ~from_nc.to_monthly
      ~from_nc.validate

   .. rubric:: Methods Documentation

   .. automethod:: get_copy
   .. automethod:: get_indices
   .. automethod:: get_values_from_coords
   .. automethod:: get_values_from_indices
   .. automethod:: to_annual
   .. automethod:: to_monthly
   .. automethod:: validate

Functions
-----------

.. currentmodule:: pcrglobwb_utils.sim_data

.. autofunction:: apply_window_search
.. autofunction:: find_indices_from_coords
.. autofunction:: read_at_coords
.. autofunction:: read_at_indices
.. autofunction:: validate_timeseries

    
