Scikit-Image support
======================
Scikit-image (or `skimage`) is an image processing framework tied to Scikit. Luckily Its images are of type `numpy.ndarray <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html>`_.
Since gmic-py 2.9.1 you can convert a `GmicImage` from and to a `PIL.Image.Image`.

The `skimage` support is limited for now. It relies on fine-tuned calls to the `GmicImage.from_numpy_helper` and `GmicImage.to_numpy_helper` generic methods.

G'MIC Python's Scikit-image input/output conversion methods are simply:

- .. autosignature:: gmic.GmicImage.from_skimage

- .. autosignature:: gmic.GmicImage.to_skimage

Those are fully documented in the :doc:`gmic`.

You are encouraged to write your own version of `to_skimage()` and `from_skimage()` in pure Python by copy-pasting the expressions listed in those API definitions documentation, and tinkering with them.
You can also help improve the converters upstream with suggestions or patches `on the project repository <https://github.com/myselfhimself/gmic-py/issues>`_.

Must-know
#############
* G'MIC's images are 3D (volumetric) non-interleaved with an almost unlimited number of 32-bit float pixel values. Their shape axes order is x,y,z,c (or width, height, depth, channels).
* Scikit images are the same, with pixel-type agnosticity and different shape: z,y,x,c (depth or layers, height, width, channels (or spectrum)).

How-to
###########
* The usual way to convert a Scikit image to G'MIC is as follows:

.. code-block:: sh

    pip install scikit-image
    pip install gmic

.. code-block:: python

    import gmic
    import skimage
    astronaut = skimage.data.astronaut
    gmic_image_from_skimage = gmic.GmicImage.from_skimage(astronaut)
    print(gmic_image_from_skimage)
    gmic.run("display", gmic_image_from_skimage)

* The usual way to convert a G'MIC Image to PIL is as follows:

.. code-block:: sh

    pip install scikit-image
    pip install gmic

.. code-block:: python

    import gmic
    import skimage
    from skimage.viewer import ImageViewer
    gmic_images = []
    gmic.run("sp apples", gmic_images) # store apples image into our list
    skimage_from_gmic = gmic_images[0].to_skimage() # to_PIL can take 3 config parameters, see its documentation or run help(gmic.GmicImage.to_PIL)
    print(skimage_from_gmic)
    viewer = ImageViewer(skimage_from_gmic) # you might want to call the image's .squeeze() method first to have it 2D
    viewer.show()
