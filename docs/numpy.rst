Numpy support
=============
`Numpy <https://numpy.org>`_ stands for "numeric Python" and is a very famous data processing library for scientists.
Since `gmic-py` 2.9.1, you can convert a ``GmicImage`` from and to a ``numpy.ndarray`` for simpler manipulation.
The `numpy.ndarray` type is used in turn by many graphics processing toolkits.

Numpy input/output support for `gmic-py` is broken down into 4 methods:

- simplified input/output:

  - .. autosignature:: gmic.GmicImage.from_numpy
  - .. autosignature:: gmic.GmicImage.to_numpy

- full-control, also used for PIL and Scikit-image support:

  - .. autosignature:: gmic.GmicImage.from_numpy_helper
  - .. autosignature:: gmic.GmicImage.to_numpy_helper

All those methods are fully documented in the :doc:`gmic`.
If you want to implement new `gmic-py` conversion methods for some library that uses `numpy.ndarray`s a lot, you might just want to import and call the `*_numpy_helper` methods with your own very parameters.

1. G'MIC x Numpy must-know
########################################
* G'MIC works in 1D, 2D, 3D, or 4D. Numpy can work from 0D (scalar) to N dimensions (>4D).
* G'MIC has the following array shapes' dimension order: ``(width, height, depth, spectrum)``. The ``spectrum`` (or channels) dimension represents the number of values per pixel (eg. for RGB images, ``spectrum=3``). Numpy is shape-agnostic.
* G'MIC works in float32 (ie. 4-bytes float pixel values). Casts from and to `numpy.ndarray` will be done for you using `numpy.ndarray.astype() <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.astype.html>`_. This can be tuned by parameter ``GmicImage().to_numpy_helper(astype=...)``.
* G'MIC can store a few billions of values per pixel (eg. not just R,G,B,A).
* G'MIC is not made for real-time image processing but is quite fast though :).
* G'MIC stores pixel values internally in a non-interleaved format, eg. ``R,R,R,G,G,G,B,B,B`` for ``(3,1,3)`` image shape.
* For now the shape is not altered between within input/output methods provided by G'MIC. To alter those, you can use either the `permute=` parameter or pre- or post-process you numpy array with a `numpy transpose() <https://numpy.org/doc/stable/reference/generated/numpy.transpose.html>`_ call containing several axes.

* ``numpy`` is not a requirement for the G'MIC's Python binding to install, start and work. But is must be installed if you happen to call the `to_/from_/numpy_*` methods.

.. code-block:: sh

    pip install numpy

* Use `numpy.expand_dims <https://numpy.org/doc/stable/reference/generated/numpy.expand_dims.html>`_ and `numpy.atleast_2d <https://numpy.org/doc/stable/reference/generated/numpy.atleast_2d.html>`_, `numpy.atleast_3d <https://numpy.org/doc/stable/reference/generated/numpy.atleast_3d.html>`_, `numpy.squeeze <https://numpy.org/doc/stable/reference/generated/numpy.squeeze.html>`_ to fix your numpy arrays's dimensions.
* Advanced note: the compile flag for enabling or disabling numpy support in gmic-py is `gmic_py_numpy` (see `setup.py <https://github.com/myselfhimself/gmic-py/blob/master/setup.py>`_).

2. Numpy <-> G'MIC how-to
#######################################
* The usual way to convert a Numpy array to G'MIC is as follows:

.. code-block:: sh

    pip install numpy
    pip install gmic

.. code-block:: python

    import gmic
    import numpy.random
    arr = numpy.random.rand(512,256,3)
    gmic_image_from_numpy = gmic.GmicImage.from_numpy(arr)
    # You might have identically called gmic.GmicImage.from_numpy_helper(arr, deinterleave=True)
    print(gmic_image_from_numpy)
    gmic.run("display", gmic_image_from_numpy)

* The usual way to convert a G'MIC Image to Numpy is as follows:

.. code-block:: sh

    pip install numpy
    pip install gmic
    pip install matplotlib

.. code-block:: python

    import gmic
    import numpy
    from matplotlib import pyplot as plt
    gmic_images = []
    gmic.run("sp apples", gmic_images) # store apples image into our list
    numpy_image_from_gmic = gmic_images[0].to_numpy()
    # You might have identically called gmic.GmicImage.to_numpy_helper(arr, interleave=True)
    print(numpy_image_from_gmic)
    plt.imshow(numpy_image_from_gmic)
    plt.show()
