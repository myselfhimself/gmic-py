Welcome to gmic-py's documentation!
===================================
``gmic-py`` is a Python 3 binding for the `G'MIC Image Processing Framework <https://gmic.eu/>`_ written in C++.

G'MIC provides image-processing commands for 1D to 4D images, as well as many graphical filters.
It is thus targetted at both artists and data-scientists.

This documentation showcases various uses of ``gmic-py``:

* gmic-py alone in pure Python,
* with `Numpy <https://numpy.org/>`_,
* with the `Python Imaging Library (PIL) <https://python-pillow.org/>`_,
* with `scikit-image <https://scikit-image.org/>`_,
* (soon) with `pygame <https://www.pygame.org/>`_,
* (soon) with `p5 processing for Python <https://pypi.org/project/p5/>`_.

For Linux and generally, ``gmic-py`` can be installed for Python >= 3.6 using:

.. code-block:: sh

    pip install gmic

MacOS works the same but needs `libomp` on top.
Windows will be supported in the third quarter of 2020.

Head over to the :doc:`installing` section for more setup details.

Head over to the :doc:`gettingstarted` section for examples.

.. toctree::
   :maxdepth: 2

   installing
   gettingstarted
   compiling
   numpy
   PIL
   skimage
   jupyter
   gmic



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
