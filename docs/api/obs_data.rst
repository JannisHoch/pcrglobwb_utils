Observed data
=========================

There are function to load (meta-)data of observations from file:

From GRDC data
--------------

For reading GRDC data, working with a python-object can be done like this.

.. currentmodule:: pcrglobwb_utils.obs_data

.. autoclass:: grdc_data

   .. rubric:: Methods Summary

   .. autosummary::

      ~grdc_data.get_grdc_station_properties
      ~grdc_data.get_grdc_station_values
      ~grdc_data.to_annual
      ~grdc_data.to_monthly

   .. rubric:: Methods Documentation

   .. automethod:: get_grdc_station_properties
   .. automethod:: get_grdc_station_values
   .. automethod:: to_annual
   .. automethod:: to_monthly

From other sources
--------------------

.. currentmodule:: pcrglobwb_utils.obs_data

.. autoclass:: other_data

   .. rubric:: Methods Summary

   .. autosummary::

      ~other_data.get_values_from_excel
      ~other_data.get_values_from_csv
      ~other_data.to_annual
      ~other_data.to_monthly

   .. rubric:: Methods Documentation

   .. automethod:: get_values_from_excel
   .. automethod:: get_values_from_csv
   .. automethod:: to_annual
   .. automethod:: to_monthly