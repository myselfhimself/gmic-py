PIL support
===========
PIL is the Python Imaging Library and allows to load, save and modify files in many formats. Nowadays Python programmers install its `Pillow <https://pillow.readthedocs.io/en/stable/>`_ fork mostly.
Since gmic-py 2.9.1 you can convert a `GmicImage` from and to a `PIL.Image.Image`.

This support is limited and does not intend to cover all types of image buffer formats accepted by PIL. Because of PIL's `buffer codec limitations highlighted here <https://github.com/python-pillow/Pillow/issues/4954>`_, an intermediate pass which will be invisible to you will leverage methods `GmicImage.to_numpy_helper` and `GmicImage.from_numpy_helper`.

We have tested only 8-bit RGB 2D files in PIL, more or fewer channels and smaller or bigger pixel values should work. `Feel free to add an issue on our tracker for things you really need related to PIL or gmic-py! <https://github.com/myselfhimself/gmic-py/issues>`_

G'MIC Python's PIL input/output conversion methods are simply:

- .. autosignature:: gmic.GmicImage.from_PIL

- .. autosignature:: gmic.GmicImage.to_PIL

Those are fully documented in the :doc:`gmic`.

You are encouraged to write your own version of `to_PIL()` and `from_PIL()` in pure Python by copy-pasting the expressions listed in those API definitions documentation, and tinkering with them.

1. G'MIC x PIL must-know
###############################
* G'MIC's images are 3D (volumetric) non-interleaved with an almost unlimited number of 32-bit float pixel values. Their shape axes order is x,y,z,c (or width, height, depth, channels).
* PIL works mostly in 2D interleaved, assuming here only 8-bit float pixel values (because of our limited support). PIL Images shape are assumed to be y,x,c (or height, width, channels), which may equate to a `squeezed 3D array down to 2D. <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.squeeze.html?highlight=squeeze#numpy.ndarray.squeeze>`_. Shape squeezing and axes flipping is what the `to_PIL()` will do for you.
* G'MIC PIL Image input and output methods will import `numpy` on the fly for you, so that module must be installed too in addition to eg. `Pillow`.

2. PIL <-> G'MIC how-to
#####################################
* The usual way to convert a PIL image to G'MIC is as follows:

.. code-block:: sh

    pip install Pillow
    pip install gmic

.. code-block:: python

    import gmic
    import PIL.Image
    #have some myfile.png somewhere or anything that PIL can open
    gmic_image_from_PIL = gmic.GmicImage.from_PIL(PIL.Image.open("myfile.png"))
    print(gmic_image_from_PIL)
    gmic.run("display", gmic_image_from_PIL)

* The usual way to convert a G'MIC Image to PIL is as follows:

.. code-block:: sh

    pip install Pillow

.. code-block:: python

    import gmic
    import PIL.Image
    gmic_images = []
    gmic.run("sp apples", gmic_images) # store apples image into our list
    PIL_image_from_gmic = gmic_images[0].to_PIL() # to_PIL can take 3 config parameters, see its documentation or run help(gmic.GmicImage.to_PIL)
    print(PIL_image_from_gmic)
    PIL_image_from_gmic.show()
