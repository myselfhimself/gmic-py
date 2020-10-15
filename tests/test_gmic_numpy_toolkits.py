import inspect
import struct

import pytest
import gmic
import numpy

from test_gmic_py import (
    gmic_instance_types,
    assert_gmic_images_are_identical,
    assert_non_empty_file_exists,
)


#
#
def test_toolkit_gmic_from_scikit():
    pass


#     from skimage import data, io, filters
#     from skimage.data import download_all
#
#     download_all()  # grabbing more data for proper 3d conversion testing
#
#     image = data.lfw_subset()
#     print(image.shape)
#     print(image)
#     io.imshow(image)
#     io.show()
#
#     # skimage shape is (height, width, spectrum)
#     # gmic will flip them
#
#     gi = gmic.GmicImage.from_numpy_array(image, deinterleave=True)
#     gmic.run("display", gi)


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


@pytest.fixture
def bicolor_squeezable_non_interleaved_gmic_image():
    """
    Returns a (w,h,d,s) = (5,4,3,2) image of 5x4x3=60 pixels with 2 float values each, non-interleaved.
    Ie. arranged in the buffer as: 60 float values for the 1st channel, 60 float values for the 2nd channel.
    Color1 is a float in range [0:126], color2 is a float in range [127:255].

    This gives a way to inspect interleaved/non-interleaved state through transformations.
    :return: gmic.GmicImage
    """
    import struct

    w = 1
    h = 4
    d = 1
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
        ({"permute": "xyzc"}, False),
        ({"permute": ""}, (gmic.GmicException, r".*should be 4-characters.*")),
        ({"permute": "xyz"}, (gmic.GmicException, r".*should be 4\-characters.*")),
        (
            {"permute": "xyaz"},
            (gmic.GmicException, r".*should be made up of.*characters.*"),
        ),
        ({"permute": "zxyc"}, (3, 5, 4, 2)),
        ({"permute": "zxyc", "astype": numpy.uint8}, (3, 5, 4, 2)),
        (
            {"permute": "zxyc", "astype": numpy.uint8, "squeeze_shape": True},
            (3, 5, 4, 2),
        ),
        ({"permute": "yxzc"}, (4, 5, 3, 2)),
        ({"permute": "zyxc"}, (3, 4, 5, 2)),
        ({"permute": "zyxc", "interleave": True}, (3, 4, 5, 2)),
    ],
)
def test_toolkit_to_numpy_no_preset_shape_coherence(
    bicolor_non_interleaved_gmic_image, kwargs, expected_shape_if_different
):
    """
    Returned numpy.ndarray shape must be independent of astype and interleave values.
    It must be sensible to permute and squeeze_shape (tested in different test case) values only.
    """
    if isinstance(expected_shape_if_different, tuple):
        if inspect.isclass(expected_shape_if_different[0]) and issubclass(
            expected_shape_if_different[0], Exception
        ):
            with pytest.raises(
                expected_shape_if_different[0], match=expected_shape_if_different[1]
            ):
                bicolor_non_interleaved_gmic_image.to_numpy_array(**kwargs).shape == (
                    5,
                    4,
                    3,
                    2,
                )
        else:
            assert (
                bicolor_non_interleaved_gmic_image.to_numpy_array(**kwargs).shape
                == expected_shape_if_different
            )
    else:
        assert bicolor_non_interleaved_gmic_image.to_numpy_array(**kwargs).shape == (
            bicolor_non_interleaved_gmic_image._width,
            bicolor_non_interleaved_gmic_image._height,
            bicolor_non_interleaved_gmic_image._depth,
            bicolor_non_interleaved_gmic_image._spectrum,
        )


def test_toolkit_to_numpy_no_preset_squeeze_shape_coherence(
    bicolor_squeezable_non_interleaved_gmic_image, bicolor_non_interleaved_gmic_image
):
    assert bicolor_squeezable_non_interleaved_gmic_image.to_numpy_array(
        squeeze_shape=True
    ).shape == (4, 2)
    assert bicolor_squeezable_non_interleaved_gmic_image.to_numpy_array(
        squeeze_shape=False
    ).shape == (1, 4, 1, 2)
    assert bicolor_non_interleaved_gmic_image.to_numpy_array(
        squeeze_shape=False
    ).shape == (5, 4, 3, 2)
    assert bicolor_non_interleaved_gmic_image.to_numpy_array(
        squeeze_shape=True
    ).shape == (5, 4, 3, 2)


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


def test_toolkit_to_numpy_no_preset_no_default_interleave(
    bicolor_non_interleaved_gmic_image,
):
    untouched_interleaving_numpy_array = (
        bicolor_non_interleaved_gmic_image.to_numpy_array(interleave=False)
    )
    w, h, d, s = (
        bicolor_non_interleaved_gmic_image._width,
        bicolor_non_interleaved_gmic_image._height,
        bicolor_non_interleaved_gmic_image._depth,
        bicolor_non_interleaved_gmic_image._spectrum,
    )

    # ensure non-interleaved image's shape is not altered after generation, and its data buffer is non-interleaved
    assert untouched_interleaving_numpy_array.shape == (w, h, d, s)
    assert untouched_interleaving_numpy_array.dtype == numpy.float32

    # ensure interleave=False is the default value parameter of to_numpy_array()
    non_default_interleaved_numpy_array = (
        bicolor_non_interleaved_gmic_image.to_numpy_array()
    )
    assert numpy.array_equal(
        non_default_interleaved_numpy_array, untouched_interleaving_numpy_array
    )

    # ensure GmicImage raw data buffer as the same floats order and values as the numpy.ndarray raw buffer
    assert struct.unpack(
        "120f", non_default_interleaved_numpy_array.tobytes()
    ) == struct.unpack("120f", bicolor_non_interleaved_gmic_image._data)


def test_toolkit_to_numpy_no_preset_interleave_parameter(
    bicolor_non_interleaved_gmic_image,
):
    # ensure that shape and dtype are maintained through interleaving
    interleaved_numpy_array = bicolor_non_interleaved_gmic_image.to_numpy_array(
        interleave=True
    )
    w, h, d, s = (
        bicolor_non_interleaved_gmic_image._width,
        bicolor_non_interleaved_gmic_image._height,
        bicolor_non_interleaved_gmic_image._depth,
        bicolor_non_interleaved_gmic_image._spectrum,
    )
    assert interleaved_numpy_array.shape == (w, h, d, s)
    assert interleaved_numpy_array.dtype == numpy.float32

    # Ensure that GmicImage.to_numpy_array() does not interleave by default
    # This is a slightly different test than in test_toolkit_to_numpy_no_preset_no_default_interleave()
    default_non_interleaved_numpy_array = (
        bicolor_non_interleaved_gmic_image.to_numpy_array()
    )
    assert struct.unpack("120f", interleaved_numpy_array.tobytes()) != struct.unpack(
        "120f", default_non_interleaved_numpy_array.tobytes()
    )

    # per-pixel range checking is now easy to do for numpy has straightforward pixel addresses for interleaved buffers
    for x in range(w):
        for y in range(h):
            for z in range(d):
                assert 0 <= interleaved_numpy_array[x, y, z, 0] < 128
                assert 127 <= interleaved_numpy_array[x, y, z, 1] < 255


def test_toolkit_to_numpy_with_gmic_preset():
    pass


def test_toolkit_from_numpy_with_gmic_preset():
    pass


# TODO remove this
if __name__ == "__main__":
    test_toolkit_gmic_from_scikit()
