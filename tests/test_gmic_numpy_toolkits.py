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

    image = data.coins()
    edges = filters.sobel(image)
    io.imshow(edges)
    io.show()


def test_toolkit_gmic_to_scikit():
    pass
