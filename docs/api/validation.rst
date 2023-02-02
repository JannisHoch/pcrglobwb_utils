Functions for validation
=========================

Timeseries
-----------

GRDC
^^^^^^^^^^^^^^^^^^^^^^^

The top-level to evalute simulated timeseries with GRDC observations can be used via command line.

.. currentmodule:: pcrglobwb_utils.eval

.. autofunction:: GRDC

EXCEL
^^^^^^^

.. todo:: 

    Documentation needs to be added still.


Polygons
---------

With ``pcrglobwb_utils`` it is possible to validate spatially-varying PCR-GLOBWB output against a range of datasets. 
Per domain, area averages per timestep are computed and timeseries validated.

.. autoclass:: spatial_validation.validate_per_shape
    :members: