Functions for validation
=========================

Timeseries
-----------

GRDC
^^^^^^^^^^^^^^^^^^^^^^^

The top-level to evalute simulated timeseries with GRDC observations can be used via command line.
See :ref:`_usage_timeseries`.

.. currentmodule:: eval

.. autofunction:: GRDC

GSIM
^^^^^^

.. todo::
    
    Would be very nice to have

EXCEL
^^^^^^^

.. todo:: 

    Documentation needs to be added still.


Polygons
---------

With ``pcrglobwb_utils`` it is possible to validate spatially-varying PCR-GLOBWB output against a range of datasets. 
Per domain, area averages per timestep are computed and timeseries validated.

.. currentmodule:: spatial_validation

.. autoclass:: validate_per_shape

   .. rubric:: Methods Summary

   .. autosummary::

      ~validate_per_shape.against_GLEAM
      ~validate_per_shape.against_GRACE

   .. rubric:: Methods Documentation

   .. automethod:: against_GLEAM
   .. automethod:: against_GRACE