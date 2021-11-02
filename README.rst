===============
Overview
===============


.. image:: https://img.shields.io/pypi/v/pcrglobwb_utils.svg
        :target: https://pypi.python.org/pypi/pcrglobwb_utils

.. image:: https://readthedocs.org/projects/pcrglobwb-utils/badge/?version=latest
        :target: https://pcrglobwb-utils.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3725813.svg
   :target: https://doi.org/10.5281/zenodo.3725813
   :alt: DOI

.. image:: https://img.shields.io/badge/License-GPLv3-blue.svg
   :target: https://www.gnu.org/licenses/gpl-3.0
   :alt: License

.. image:: https://codecov.io/gh/JannisHoch/pcrglobwb_utils/branch/dev/graph/badge.svg?token=61HVIA952S
   :target: https://codecov.io/gh/JannisHoch/pcrglobwb_utils
   :alt: Codecov
 
Handy functions to work with PCR-GLOBWB input and output.

* Free software: GNU General Public License v3
* Documentation: https://pcrglobwb-utils.readthedocs.io.


Features
--------

Most mature: 

* evaluation of timeseries simulated by PCR-GLOBWB with observations from GRDC.
  
  * multiple GRDC-stations and properties can be provided via a yml-file.
  * using command line functions and wide range of user-defined options.
  
* command line functions to validate model output against GRACE and GLEAM data for multiple polygons.

Other:

* aggregating and averaging over time scales.
* water balance assessments of PCR-GLOBWB runs.
* statistical analyses.
* ensemble analysis.


Credits
-------

Contributions from Jannis M. Hoch (j.m.hoch@uu.nl).

The package structure was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
