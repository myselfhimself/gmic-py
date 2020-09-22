import os

import pytest
import gmic
import numpy

from test_gmic_py import (
    gmic_instance_types,
    assert_gmic_images_are_identical,
    assert_non_empty_file_exists,
)


def test_toolkit_gmic_from_scikit():
    from skimage import data, io, filters
    from skimage.data import download_all
    download_all() # grabbing more data for proper 3d conversion testing

    image = data.lfw_subset()
    print(image.shape)
    print(image)
    io.imshow(image)
    io.show()

    # skimage shape is (height, width, spectrum)
    # gmic will flip them

    gi = gmic.GmicImage.from_numpy_array(image, deinterleave=True)
    gmic.run("display", gi)


def test_toolkit_gmic_to_scikit():
    pass


# TODO remove this
if __name__ == "__main__":
    test_toolkit_gmic_from_scikit()
