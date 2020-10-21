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
#     gi = gmic.GmicImage.from_numpy_helper(image, deinterleave=True)
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
    Returns a (w,h,d,s) = (5,4,3,2) image of 5x4x3=60 pixels with 2 float values per-pixel, non-interleaved.
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
                bicolor_non_interleaved_gmic_image.to_numpy_helper(**kwargs).shape == (
                    5,
                    4,
                    3,
                    2,
                )
        else:
            assert (
                bicolor_non_interleaved_gmic_image.to_numpy_helper(**kwargs).shape
                == expected_shape_if_different
            )
    else:
        assert bicolor_non_interleaved_gmic_image.to_numpy_helper(**kwargs).shape == (
            bicolor_non_interleaved_gmic_image._width,
            bicolor_non_interleaved_gmic_image._height,
            bicolor_non_interleaved_gmic_image._depth,
            bicolor_non_interleaved_gmic_image._spectrum,
        )


def test_toolkit_to_numpy_no_preset_squeeze_shape_coherence(
    bicolor_squeezable_non_interleaved_gmic_image, bicolor_non_interleaved_gmic_image
):
    assert bicolor_squeezable_non_interleaved_gmic_image.to_numpy_helper(
        squeeze_shape=True
    ).shape == (4, 2)
    assert bicolor_squeezable_non_interleaved_gmic_image.to_numpy_helper().shape == (
        1,
        4,
        1,
        2,
    )
    assert bicolor_non_interleaved_gmic_image.to_numpy_helper().shape == (5, 4, 3, 2)
    assert bicolor_squeezable_non_interleaved_gmic_image.to_numpy_helper(
        squeeze_shape=False
    ).shape == (1, 4, 1, 2)
    assert bicolor_non_interleaved_gmic_image.to_numpy_helper(
        squeeze_shape=False
    ).shape == (5, 4, 3, 2)
    assert bicolor_non_interleaved_gmic_image.to_numpy_helper(
        squeeze_shape=True
    ).shape == (5, 4, 3, 2)


def test_toolkit_to_numpy_interleave_shape_conservation(
    bicolor_non_interleaved_gmic_image,
):
    assert bicolor_non_interleaved_gmic_image.to_numpy_helper(
        interleave=True
    ).shape == (
        bicolor_non_interleaved_gmic_image._width,
        bicolor_non_interleaved_gmic_image._height,
        bicolor_non_interleaved_gmic_image._depth,
        bicolor_non_interleaved_gmic_image._spectrum,
    )


def test_toolkit_to_numpy_no_preset_no_default_interleaving(
    bicolor_non_interleaved_gmic_image,
):
    untouched_interleaving_numpy_array = (
        bicolor_non_interleaved_gmic_image.to_numpy_helper(interleave=False)
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

    # ensure interleave=False is the default value parameter of to_numpy_helper()
    non_default_interleaved_numpy_array = (
        bicolor_non_interleaved_gmic_image.to_numpy_helper()
    )
    assert numpy.array_equal(
        non_default_interleaved_numpy_array, untouched_interleaving_numpy_array
    )

    # ensure GmicImage raw data buffer as the same floats order and values as the numpy.ndarray raw buffer
    non_interleaved_numpy_buffer = struct.unpack(
        "120f", non_default_interleaved_numpy_array.tobytes()
    )
    assert non_interleaved_numpy_buffer == struct.unpack(
        "120f", bicolor_non_interleaved_gmic_image._data
    )

    # check buffer float values proper non-interleaving
    for pos, f in enumerate(non_interleaved_numpy_buffer):
        if pos < 60:
            assert 0 <= f < 128
        else:
            assert 127 <= f < 255


def test_toolkit_to_numpy_no_preset_interleave_parameter(
    bicolor_non_interleaved_gmic_image,
):
    # ensure that shape and dtype are maintained through interleaving
    interleaved_numpy_array = bicolor_non_interleaved_gmic_image.to_numpy_helper(
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

    # Ensure that GmicImage.to_numpy_helper() does not interleave by default
    # This is a slightly different test than in test_toolkit_to_numpy_no_preset_no_default_interleave()
    default_non_interleaved_numpy_array = (
        bicolor_non_interleaved_gmic_image.to_numpy_helper()
    )

    interleaved_numpy_buffer = struct.unpack("120f", interleaved_numpy_array.tobytes())
    assert interleaved_numpy_buffer != struct.unpack(
        "120f", default_non_interleaved_numpy_array.tobytes()
    )

    # per-pixel range checking is now easy to do for numpy has straightforward pixel addresses for interleaved buffers
    for x in range(w):
        for y in range(h):
            for z in range(d):
                assert 0 <= interleaved_numpy_array[x, y, z, 0] < 128
                assert 127 <= interleaved_numpy_array[x, y, z, 1] < 255

    # check buffer float values proper interleaving
    for pos, f in enumerate(interleaved_numpy_buffer):
        if pos % 2 == 0:
            assert 0 <= f < 128
        else:
            assert 127 <= f < 255


def test_toolkit_to_numpy_no_preset_astype_coherence(
    bicolor_non_interleaved_gmic_image,
):
    assert bicolor_non_interleaved_gmic_image.to_numpy_helper().dtype == numpy.float32
    assert (
        bicolor_non_interleaved_gmic_image.to_numpy_helper(astype=None).dtype
        == numpy.float32
    )

    assert (
        bicolor_non_interleaved_gmic_image.to_numpy_helper(astype=numpy.float32).dtype
        == numpy.float32
    )
    assert (
        bicolor_non_interleaved_gmic_image.to_numpy_helper(astype=numpy.uint8).dtype
        == numpy.uint8
    )
    assert (
        bicolor_non_interleaved_gmic_image.to_numpy_helper(astype=numpy.float16).dtype
        == numpy.float16
    )


def test_toolkit_to_PIL():
    # Compares G'MIC and PIL PNG lossless output with both square and non-square images
    l = []
    PIL_leno_filename = "PIL_leno.png"
    PIL_apples_filename = "PIL_apples.png"
    gmic.run("sp leno sp apples", l)
    PIL_leno, PIL_apples = l[0].to_PIL(), l[1].to_PIL()
    PIL_leno.save(PIL_leno_filename, compress_level=0)
    PIL_apples.save(PIL_apples_filename, compress_level=0)
    PIL_reloaded_imgs = []
    gmic.run(PIL_leno_filename + " " + PIL_apples_filename, PIL_reloaded_imgs)
    assert_non_empty_file_exists(PIL_leno_filename).unlink()
    assert_non_empty_file_exists(PIL_apples_filename).unlink()
    assert_gmic_images_are_identical(l[0], PIL_reloaded_imgs[0])
    assert_gmic_images_are_identical(l[1], PIL_reloaded_imgs[1])


def test_toolkit_to_PIL_advanced():
    # to_PIL fine-graining parameters testing
    l = []
    gmic.run("sp leno sp apples", l)
    PIL_leno = l[0].to_PIL(mode="HSV")
    assert PIL_leno.mode == "HSV"
    assert PIL_leno.width == l[0]._width
    assert PIL_leno.height == l[0]._height
    with pytest.raises(ValueError, match=r".*Too many dimensions.*"):
        l[1].to_PIL(squeeze_shape=False)
    # non-erroring commands
    l[1].to_PIL(astype=float)
    l[1].to_PIL(astype=numpy.uint8)


def test_toolkit_from_PIL():
    # Compares G'MIC and PIL PNG lossless output with both square and non-square images
    import PIL.Image

    l = []
    gmic.run("sp leno sp apples", l)

    PIL_apples_filename = "PIL_apples.png"
    PIL_leno_filename = "PIL_leno.png"

    gmic.run("sp leno output " + PIL_leno_filename)
    PIL_leno = PIL.Image.open(PIL_leno_filename)
    leno = gmic.GmicImage.from_PIL(PIL_leno)
    assert_gmic_images_are_identical(l[0], leno)
    assert_non_empty_file_exists(PIL_leno_filename).unlink()

    gmic.run("sp apples output " + PIL_apples_filename)
    PIL_apples = PIL.Image.open(PIL_apples_filename)
    apples = gmic.GmicImage.from_PIL(PIL_apples)
    assert_gmic_images_are_identical(l[1], apples)
    assert_non_empty_file_exists(PIL_apples_filename).unlink()


def test_toolkit_to_numpy_with_gmic_preset():
    pass


def test_toolkit_from_numpy_with_gmic_preset():
    pass


# TODO remove this
if __name__ == "__main__":
    test_toolkit_gmic_from_scikit()
