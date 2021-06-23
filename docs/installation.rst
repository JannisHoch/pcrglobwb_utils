.. _installation:

.. highlight:: shell

============
Installation
============

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

    $ cd path/to/pcrglobwb_utils
    $ python setup.py develop

Alternatively, you can use:

.. code-block:: console

    $ cd path/to/pcrglobwb_utils    
    $ pip install -e path/to/pcrglobwb_utils

From PyPI
----------

pcrglobwb_utils can also be installed from PyPI. To do so, use this command:

.. code-block:: console

    $ pip install pcrglobwb-utils

If a specific version is required, then the command would need to look like this:

.. code-block:: console

    $ pip install pcrglobwb-utils==version


.. _Github repo: https://github.com/JannisHoch/pcrglobwb_utils
