Numpy support
=============
Since gmic-py 2.9.1, you can convert ``GmicImage``s from and to ``numpy.ndarray``s.

1. G'MIC from/to Numpy & PIL must-knows
########################################
* G'MIC works in 1D, 2D, 3D, or 4D. Numpy can work from 0D (scalar) to N dimensions (>4D).
* G'MIC has the following array shapes' dimension order: ``(width, height, depth, spectrum)`` (each shape dimension is >= 1). The ``spectrum`` dimension represents the number of values per pixel (eg. for RGB images, ``spectrum=3``).
* G'MIC works in float32 (ie. 4-bytes floats), which can store signed integers and floats. It is agnostic on the range of value (eg. not just 0-255). Casts from and to numpy.ndarray will be done for you. Use `numpy.ndarray.astype <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.astype.html>`_ or ``GmicImage().to_numpy_array(astype=...)`` if needed.
* G'MIC can store a few billions of values per pixel (eg. not just R,G,B,A).
* G'MIC is not made for real-time image processing but is quite fast though :).
* G'MIC stores pixel values internally in a non-interleaved format, eg. ``R,R,R,G,G,G,B,B,B`` for ``(3,1,3)`` image shape.
* The G'MIC => numpy.ndarray conversion (ie. ``GmicImage.to_numpy_array()``) will flip G'MIC's shape to look like a algebrae-culture-one, ie. (depth, height, width, spectrum), with all dimensions present and >= 1.

* PIL - the Python Imaging Library is often used to provide images from a file to numpy in order to end up with a numpy.ndarray object. PIL works in 2d mostly with 1 or more values per pixel.
* PIL will display a shape of ``(h,w)`` for greyscale images (eg. pgm ones), which will be interpreted by G'MIC as (w,h,1,1).
* PIL swaps the width and height of the 2d images it opens, giving shapes such as (h,w) (greyscale images) or (h,w,3) (RGB images).
* The usual way to load an image to numpy with PIL is the following:

.. code-block:: sh
    pip install Pillow

.. code-block:: python
    import numpy
    import PIL.Image
    image_from_numpy = numpy.array(PIL.Image.open("myfile.png"))
    image_from_numpy.shape # eg. (480, 640, 3) for a 640x480 RGB image

* ``numpy`` is not a requirement for the G'MIC's Python binding to install, start and work
* Though, ``numpy`` needs to be installed within your Python environment (but will be imported by G'MIC if you do not import it yourself) for the ``GmicImage.from_numpy_array()`` and ``GmicImage.to_numpy_array()`` to work.

.. code-block:: sh
    pip install numpy

* ``numpy`` is very tolerant and does not have side-effects on your arrays in the ``G'MIC <=> numpy`` conversions, instead blame our G'MIC Python binding or PIL/other image-loading frameworks if used.
* Use ``numpy.expand_dims`` and ``numpy.atleast_2d``, ``numpy.atleast_3d`` to fix your numpy arrays's dimensions.
* You might want to flip your pixel values, depending on your pipeline to obtain a numpy array (eg. ``BGR<->RGB``).


2. Using GmicImage.from_numpy_array()
#####################################
TODO

3. Using GmicImage.to_numpy_array()
#########################################
TODO