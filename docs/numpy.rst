Numpy support
=============
Since gmic-py 2.9.1, you can convert a ``GmicImage`` from and to a ``numpy.ndarray``.

Numpy support is broken down into 4 methods:

- simplified (not yet implemented):

  - .. autosignature:: gmic.GmicImage.from_numpy
  - .. autosignature:: gmic.GmicImage.to_numpy

- full-control, used for PIL and Scikit-image support:

  - .. autosignature:: gmic.GmicImage.from_numpy_helper
  - .. autosignature:: gmic.GmicImage.to_numpy_helper

All those methods are fully documented in the :doc:`gmic`.

1. G'MIC x Numpy must-know
########################################
* G'MIC works in 1D, 2D, 3D, or 4D. Numpy can work from 0D (scalar) to N dimensions (>4D).
* G'MIC has the following array shapes' dimension order: ``(width, height, depth, spectrum)`` (each shape dimension is >= 1). The ``spectrum`` dimension represents the number of values per pixel (eg. for RGB images, ``spectrum=3``). Numpy is shape-agnostic.
* G'MIC works in float32 (ie. 4-bytes float pixel values), which can store eg. signed integers and floats. It is agnostic on the range of value (eg. not just 0-255). Casts from and to numpy.ndarray will be done for you using `numpy.ndarray.astype() <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.astype.html>`_. This can be tuned by parameter ``GmicImage().to_numpy_helper(astype=...)``.
* G'MIC can store a few billions of values per pixel (eg. not just R,G,B,A).
* G'MIC is not made for real-time image processing but is quite fast though :).
* G'MIC stores pixel values internally in a non-interleaved format, eg. ``R,R,R,G,G,G,B,B,B`` for ``(3,1,3)`` image shape.
* The G'MIC => numpy.ndarray conversion (ie. ``GmicImage.to_numpy_helper()``) will flip G'MIC's shape to look like a algebrae-culture-one, ie. (depth, height, width, spectrum), with all dimensions present and >= 1.

* ``numpy`` is not a requirement for the G'MIC's Python binding to install, start and work
* Though, ``numpy`` needs to be installed within your Python environment (but will be imported by G'MIC if you do not import it yourself) for the ``GmicImage.from_numpy_helper()`` and ``GmicImage.to_numpy_helper()`` to work.

.. code-block:: sh

    pip install numpy

* ``numpy`` is very tolerant and has little to no side-effects on your arrays in the ``G'MIC <=> numpy`` conversions.
* Use ``numpy.expand_dims`` and ``numpy.atleast_2d``, ``numpy.atleast_3d`` to fix your numpy arrays's dimensions.
* You might want to flip your pixel values, depending on your pipeline to obtain a numpy array (eg. ``BGR<->RGB``).


2. Numpy <-> G'MIC how-to
#######################################
TODO