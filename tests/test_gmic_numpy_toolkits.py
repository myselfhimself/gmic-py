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

    download_all()  # grabbing more data for proper 3d conversion testing

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


@pytest.fixture
def bicolor_non_interleaved_gmic_image():
    """
    Returns a (w,h,d,s) = (5,4,3,2) image of 5x4x3=60 pixels with 2 float values each, non-interleaved.
    Ie. arranged in the buffer as: 60 float values for the 1st channel, 60 float values for the 2nd channel.
    Color1 is a float in range [0:126], color2 is a float in range [127:255].

    This gives a way to inspect interleaved/non-interleaved state through transformations.
    :return: gmic.GmicImage
    """
    import struct

    w = 5
    h = 4
    d = 3
    c = 2  # eg. just red and green
    nb_floats = w * h * d * c
    c0 = list(range(w * h * d))  # color1 range in [0:126]
    c1 = list(range(127, 127 + w * h * d))  # color2 range in [127:255]
    print(len(c1) + len(c0))
    gmic_image_buffer = struct.pack("{}f".format(nb_floats), *tuple(c0 + c1))
    non_interleaved_gmicimage = gmic.GmicImage(gmic_image_buffer, w, h, d, c)

    return non_interleaved_gmicimage


def test_bicolor_non_interleaved_gmic_pixel_values(bicolor_non_interleaved_gmic_image):
    # ensure we have built a properly deinterleaved G'MIC image
    for x in range(bicolor_non_interleaved_gmic_image._width):
        for y in range(bicolor_non_interleaved_gmic_image._height):
            for z in range(bicolor_non_interleaved_gmic_image._depth):
                assert 0 <= bicolor_non_interleaved_gmic_image(x, y, z, 0) < 127
                assert 126 < bicolor_non_interleaved_gmic_image(x, y, z, 1) < 255


@pytest.mark.parametrize(
    "kwargs,expected_shape_if_different",
    [
        ({}, False),
        ({"interleave": True}, False),
        ({"interleave": False}, False),
        ({"astype": numpy.uint8}, False),
        ({"permute": "xyz"}, False),
        ({"permute": "zxy"}, (3, 5, 4, 2)),
        ({"permute": "zxy", "astype": numpy.uint8}, (3, 5, 4, 2)),
        (
            {"permute": "zxy", "astype": numpy.uint8, "squeeze_shape": True},
            (3, 5, 4, 2),
        ),
        ({"permute": "yxz"}, (4, 5, 3, 2)),
        ({"permute": "zyx"}, (3, 4, 5, 2)),
        ({"permute": "zyx", "interleave": True}, (3, 4, 5, 2)),
    ],
)
def test_toolkit_to_numpy_no_preset_shape_coherence(
    bicolor_non_interleaved_gmic_image, kwargs, expected_shape_if_different
):
    """
    Shape must be independent of astype, interleave and astype values.
    It must be sensible to permute and squeeze_shape values only.
    """
    assert bicolor_non_interleaved_gmic_image.to_numpy_array(**kwargs).shape == (
        expected_shape_if_different
        if expected_shape_if_different
        else (
            bicolor_non_interleaved_gmic_image._width,
            bicolor_non_interleaved_gmic_image._height,
            bicolor_non_interleaved_gmic_image._depth,
            bicolor_non_interleaved_gmic_image._spectrum,
        )
    )


# TODO squeeze shape test with one more axes=1 value


def test_toolkit_to_numpy_interleave_shape_conservation(
    bicolor_non_interleaved_gmic_image,
):
    assert bicolor_non_interleaved_gmic_image.to_numpy_array(interleave=True).shape == (
        bicolor_non_interleaved_gmic_image._width,
        bicolor_non_interleaved_gmic_image._height,
        bicolor_non_interleaved_gmic_image._depth,
        bicolor_non_interleaved_gmic_image._spectrum,
    )


def test_toolkit_to_numpy_no_preset_interleave(bicolor_non_interleaved_gmic_image):
    untouched_interleaving_numpy_array = bicolor_non_interleaved_gmic_image.to_numpy_array(
        interleave=False
    )
    # ensure shape is not altered
    assert untouched_interleaving_numpy_array.shape == (
        bicolor_non_interleaved_gmic_image._width,
        bicolor_non_interleaved_gmic_image._height,
        bicolor_non_interleaved_gmic_image._depth,
        bicolor_non_interleaved_gmic_image._spectrum,
    )
    assert untouched_interleaving_numpy_array.dtype == numpy.float32
    for x in range(w):
        for y in range(h):
            for z in range(d):
                # Ensure the G'MIC to numpy conversion without interleaving keeps same array values order
                assert 0 <= untouched_interleaving_numpy_array[x, y, z, 0] < 128
                assert 255 < untouched_interleaving_numpy_array[x, y, z, 1] > 127

    interleaved_numpy_array = bicolor_non_interleaved_gmic_image.to_numpy_array()
    assert interleaved_numpy_array == bicolor_non_interleaved_gmic_image.to_numpy_array(
        interleave=False
    )
    assert interleaved_numpy_array.shape == (w, h, d, c)
    assert interleaved_numpy_array.dtype == numpy.float32
    for x in range(w):
        for y in range(h):
            for z in range(d):
                assert 0 <= untouched_interleaving_numpy_array[x, y, z][0] < 128
                assert 255 < bicolor_non_interleaved_gmic_image[x, y, z][1] > 127


def test_toolkit_to_numpy_no_preset_no_deinterleave():
    pass


def test_toolkit_to_numpy_with_gmic_preset():
    pass


def test_toolkit_from_numpy_with_gmic_preset():
    pass


# TODO remove this
if __name__ == "__main__":
    test_toolkit_gmic_from_scikit()
