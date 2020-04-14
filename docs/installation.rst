.. _installation:

.. highlight:: shell

============
Installation
============

.. note:: Currently, it is not possible to install this package via pip or conda

From source
------------

The sources for pcrglobwb_utils can be downloaded from the `Github repo`_.

You can clone the public repository:

.. code-block:: console

    $ git clone git://github.com/JannisHoch/pcrglobwb_utils

To avoid conflicting package version numbers, it is advised to create a separate conda environnmet
for this package:

.. code-block:: console

    $ conda-env create -f=path/to/pcrglobwb_utils/environment.yml

Subsequently, activate this environment with:

.. code-block:: console

    $ conda activate pcrglobwb_utils

Installation of the package is then possible:

.. code-block:: console

    $ python path/to/pcrglobwb_utils/setup.py develop


.. _Github repo: https://github.com/JannisHoch/pcrglobwb_utils
