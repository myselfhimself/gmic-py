Installing
===============
Here is how to install the ``gmic-py`` binary Python module on your operating system.

For now only Mac OS (till 2.8.3) and Linux / Unix (2.9.x) are supported.

For ``sp`` / ``sample`` and ``update`` commands to work, the `curl <https://curl.se/>`_ executable must be installed (highly likely).

If you cannot install anything on your machine, you may also install ``gmic-py`` from a Jupyter Notepad or Google Colab, see :doc:`jupyter`

For Linux / Unix
#########################
If you have pip:

.. code-block:: sh

    pip install gmic

Or conda:

.. code-block:: sh

    conda install gmic

For Mac OS
#########################
If you have pip:

.. code-block:: sh

    pip install gmic

If the OpenMP library is not installed yet, you may want to install it first (for parallelization speedup):

.. code-block:: sh

    brew install libomp # Or possibly clang-omp if failing

For Windows (future)
#########################
gmic-py's support for Windows is planned but not ready yet. 
