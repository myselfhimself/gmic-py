import os

import pytest
import gmic
import numpy

from test_gmic_py import (
    gmic_instance_types,
    assert_gmic_images_are_identical,
    assert_non_empty_file_exists,
)

# Test parametrization: dtypes and interlacing toggling between two images
numpy_dtypes_base = (
    numpy.bool,
    numpy.longlong,
    numpy.single,
    numpy.double,
    numpy.longdouble,
    numpy.int8,
    numpy.int16,
    numpy.int32,
    numpy.uint8,
    numpy.uint16,
    numpy.uint32,
    numpy.float32,
    numpy.uint64,
    numpy.int64,
    numpy.float64,
    numpy.uint,
    numpy.intp,
    numpy.uintp,
)
nb_random_dtypes_to_test = 3
dtypes_testing_subset = [None] + list(
    numpy.random.choice(numpy_dtypes_base, nb_random_dtypes_to_test)
)
interleave_toggling_subset = (None, True, False)
numpy_dtypes1 = {"argnames": "dtype1", "argvalues": dtypes_testing_subset}
numpy_dtypes2 = {"argnames": "dtype2", "argvalues": dtypes_testing_subset}
interleave_toggles1 = {
    "argnames": "interleave1",
    "argvalues": interleave_toggling_subset,
}
interleave_toggles2 = {
    "argnames": "interleave2",
    "argvalues": interleave_toggling_subset,
}
squeeze_toggles = {
    "argnames": "squeeze",
    "argvalues": [True, False],
}


@pytest.mark.parametrize(**gmic_instance_types)
def test_gmic_image_to_numpy_ndarray_exception_on_unimportable_numpy_module(
    gmic_instance_run,
):
    # numpy module hiding hack found at: https://stackoverflow.com/a/1350574/420684
    # Artificially prevent numpy from being imported
    import sys

    try:
        import numpy

        old_numpy_sys_value = sys.modules["numpy"]
    except:
        pass  # tolerate that numpy is already not importable
    else:
        # otherwise, make numpy not importable
        del numpy
        sys.modules["numpy"] = None

    import gmic

    images = []
    gmic_instance_run(images=images, command="sp duck")
    with pytest.raises(
        gmic.GmicException, match=r".*'numpy' module cannot be imported.*"
    ):
        images[0].to_numpy_array()

    # Repair our breaking of the numpy import
    sys.modules["numpy"] = old_numpy_sys_value


def gmic_image_to_numpy_array_default_interleave_param(i):
    return i if i is not None else True


def gmic_image_to_numpy_array_default_dtype_param(d):
    return d if d is not None else numpy.float32


@pytest.mark.parametrize(**numpy_dtypes1)
@pytest.mark.parametrize(**numpy_dtypes2)
@pytest.mark.parametrize(**interleave_toggles1)
@pytest.mark.parametrize(**interleave_toggles2)
@pytest.mark.parametrize(**squeeze_toggles)
@pytest.mark.parametrize(
    "gmic_command",
    ["sp apples", """3,5,7,2,'x*cos(0.5236)+y*sin(0.8)' -normalize 0,255"""],
    ids=["2dsample", "3dsample"],
)
def test_gmic_image_to_numpy_array_fuzzying(
    dtype1, dtype2, interleave1, interleave2, squeeze, gmic_command
):
    expected_interleave_check = gmic_image_to_numpy_array_default_interleave_param(
        interleave1
    ) == gmic_image_to_numpy_array_default_interleave_param(interleave2)
    params1 = {}
    params2 = {}
    if dtype1 is not None:
        params1["astype"] = dtype1
    if dtype2 is not None:
        params2["astype"] = dtype2
    if interleave1 is not None:
        params1["interleave"] = interleave1
    if interleave2 is not None:
        params2["interleave"] = interleave2
    params1["squeeze_shape"] = params2["squeeze_shape"] = squeeze

    single_image_list = []
    gmic.run(images=single_image_list, command=gmic_command)
    gmic_image = single_image_list[0]
    # Test default dtype parameter is numpy.float32
    numpy_image1 = gmic_image.to_numpy_array(**params1)
    numpy_image2 = gmic_image.to_numpy_array(**params2)
    assert numpy_image1.shape == numpy_image2.shape
    if gmic_image._depth > 1:  # 3d image shape checking
        assert numpy_image1.shape == (
            gmic_image._depth,
            gmic_image._height,
            gmic_image._width,
            gmic_image._spectrum,
        )
    else:  # 2d image shape checking
        if squeeze:
            assert numpy_image1.shape == (
                gmic_image._height,
                gmic_image._width,
                gmic_image._spectrum,
            )
        else:
            assert numpy_image1.shape == (
                gmic_image._depth,
                gmic_image._height,
                gmic_image._width,
                gmic_image._spectrum,
            )
    if dtype1 is None:
        dtype1 = numpy.float32
    if dtype2 is None:
        dtype2 = numpy.float32
    assert numpy_image1.dtype == dtype1
    assert numpy_image2.dtype == dtype2
    # Ensure arrays are equal only if we have same types and interlacing
    # Actually, they could be equal with distinct types but same interlacing, but are skipping cross-types compatibility analysis..
    if (numpy_image1.dtype == numpy_image2.dtype) and expected_interleave_check:
        assert numpy.array_equal(numpy_image1, numpy_image2)

    del gmic_image
    del single_image_list
    del numpy_image1
    del numpy_image2


@pytest.mark.parametrize(**gmic_instance_types)
def test_gmic_image_to_numpy_ndarray_basic_attributes(gmic_instance_run):
    import numpy

    single_image_list = []
    gmic_instance_run(images=single_image_list, command="sp apples")
    gmic_image = single_image_list[0]
    # we do not interleave to keep the same data structure for later comparison
    numpy_image = gmic_image.to_numpy_array(interleave=False)
    assert numpy_image.dtype == numpy.float32
    assert numpy_image.shape == (
        gmic_image._depth,
        gmic_image._height,
        gmic_image._width,
        gmic_image._spectrum,
    )
    bb = numpy_image.tobytes()
    assert len(bb) == len(gmic_image._data)
    assert bb == gmic_image._data


@pytest.mark.parametrize(**gmic_instance_types)
def test_in_memory_gmic_image_to_numpy_nd_array_to_gmic_image(gmic_instance_run):
    single_image_list = []
    gmic_instance_run(images=single_image_list, command="sp duck")
    # TODO convert back and compare with original sp duck GmicImage


@pytest.mark.parametrize(**gmic_instance_types)
def test_numpy_ndarray_RGB_2D_image_gmic_run_without_gmicimage_wrapping(
    gmic_instance_run,
):
    # TODO completely uncoherent test now..
    import PIL.Image
    import numpy

    im1_name = "image.png"
    im2_name = "image.png"
    gmic_instance_run("sp duck output " + im1_name)
    np_PIL_image = numpy.array(PIL.Image.open(im1_name))
    # TODO line below must fail because single numpy arrays rewrite is impossible for us
    with pytest.raises(
        TypeError, match=r".*'images' parameter must be a 'gmic.GmicImage'.*"
    ):
        gmic_instance_run(images=np_PIL_image, command="output[0] " + im2_name)
    imgs = []
    gmic_instance_run(images=imgs, command="{} {}".format(im1_name, im2_name))
    assert_gmic_images_are_identical(imgs[0], imgs[1])


@pytest.mark.parametrize(**gmic_instance_types)
def test_numpy_ndarray_RGB_2D_image_integrity_through_numpyPIL_or_gmicimage_from_numpy_factory_method(
    gmic_instance_run,
):
    import PIL.Image
    import numpy

    im1_name = "image.bmp"
    im2_name = "image2.bmp"

    # 1. Generate duck bitmap, save it to disk
    gmic_instance_run("sp duck -output " + im1_name)

    # 2. Load disk duck through PIL/numpy, make it a GmicImage
    image_from_numpy = numpy.array(PIL.Image.open(im1_name))
    assert type(image_from_numpy) == numpy.ndarray
    assert image_from_numpy.shape == (480, 640, 3)
    assert image_from_numpy.dtype == "uint8"
    assert image_from_numpy.dtype.kind == "u"
    gmicimage_from_numpy = gmic.GmicImage.from_numpy_array(image_from_numpy)

    gmic_instance_run(images=gmicimage_from_numpy, command=("output[0] " + im2_name))

    # 3. Load duck into a regular GmicImage through G'MIC without PIL/numpy
    imgs = []
    gmic_instance_run(images=imgs, command="sp duck")
    gmicimage_from_gmic = imgs[0]

    # 4. Use G'MIC to compare both duck GmicImages from numpy and gmic sources
    assert_gmic_images_are_identical(gmicimage_from_numpy, gmicimage_from_gmic)
    assert_non_empty_file_exists(im1_name).unlink()
    assert_non_empty_file_exists(im2_name).unlink()


@pytest.mark.parametrize(**gmic_instance_types)
def test_numpy_PIL_modes_to_gmic(gmic_instance_run):
    import PIL.Image
    import numpy

    origin_image_name = "a.bmp"
    gmicimages = []
    gmic_instance_run("sp duck output " + origin_image_name)
    PILimage = PIL.Image.open("a.bmp")

    modes = [
        "1",
        "L",
        "P",
        "RGB",
        "RGBA",
        "CMYK",
        "YCbCr",
        "HSV",
        "I",
        "F",
    ]  # "LAB" skipped, cannot be converted from RGB

    for mode in modes:
        PILConvertedImage = PILimage.convert(mode=mode)
        NPArrayImages = [numpy.array(PILConvertedImage)]
        print(PILConvertedImage, NPArrayImages[0].shape, NPArrayImages[0].dtype)
        gmicimages = [gmic.GmicImage.from_numpy_array(nd) for nd in NPArrayImages]
        gmic_instance_run(images=gmicimages, command="print")

    # TODO this test seems uncomplete..

    # Outputs
    """
    <PIL.Image.Image image mode=1 size=640x480 at 0x7FAD99B18908> (640, 480) bool
    <PIL.Image.Image image mode=L size=640x480 at 0x7FAD324FD4E0> (640, 480) uint8
    <PIL.Image.Image image mode=P size=640x480 at 0x7FAD324FD8D0> (640, 480) uint8
    <PIL.Image.Image image mode=RGB size=640x480 at 0x7FAD324FD908> (640, 480, 3) uint8
    <PIL.Image.Image image mode=RGBA size=640x480 at 0x7FAD324FD8D0> (640, 480, 4) uint8
    <PIL.Image.Image image mode=CMYK size=640x480 at 0x7FAD324FD908> (640, 480, 4) uint8
    <PIL.Image.Image image mode=YCbCr size=640x480 at 0x7FAD324FD8D0> (640, 480, 3) uint8
    <PIL.Image.Image image mode=HSV size=640x480 at 0x7FAD324FD908> (640, 480, 3) uint8
    <PIL.Image.Image image mode=I size=640x480 at 0x7FAD324FD8D0> (640, 480) int32
    <PIL.Image.Image image mode=F size=640x480 at 0x7FAD324FD908> (640, 480) float32
    """

    assert_non_empty_file_exists(origin_image_name).unlink()


def test_basic_from_numpy_array_to_numpy_array():
    duck = []
    gmic.run("sp duck", duck)
    original_duck_gmic_image = duck[0]
    duck_numpy_image = original_duck_gmic_image.to_numpy_array(squeeze_shape=True)
    duck_io_gmic_image = gmic.GmicImage.from_numpy_array(duck_numpy_image)

    assert_gmic_images_are_identical(original_duck_gmic_image, duck_io_gmic_image)


def test_from_numpy_array_proper_dimensions_number():
    zero_dimensions_array = numpy.ndarray([])

    with pytest.raises(
        gmic.GmicException, match=r".*'data'.*'numpy.ndarray'.*1D and 4D.*=0.*"
    ):
        gmic.GmicImage.from_numpy_array(zero_dimensions_array)

    five_dimensions_array = numpy.zeros((1, 2, 3, 4, 5))
    with pytest.raises(
        gmic.GmicException, match=r".*'data'.*'numpy.ndarray'.*1D and 4D.*=5.*"
    ):
        gmic.GmicImage.from_numpy_array(five_dimensions_array)


def test_basic_to_numpy_array_from_numpy_array():
    gmic.run("sp duck output duck.png")
    import PIL.Image

    pil_image = numpy.array(PIL.Image.open("duck.png"))

    pil_gmic_image = gmic.GmicImage.from_numpy_array(pil_image)
    duck_io_numpy_image = pil_gmic_image.to_numpy_array(squeeze_shape=True)

    assert numpy.array_equal(duck_io_numpy_image, pil_image)

    assert_non_empty_file_exists("duck.png").unlink()


def test_from_numpy_array_class_method_existence():
    # should not raise any AttributeError
    getattr(gmic.GmicImage, "from_numpy_array")


def test_to_numpy_array_instance_method_existence():
    a = gmic.GmicImage()
    # should not raise any AttributeError
    getattr(a, "to_numpy_array")


def test_numpy_format_attributes_existence():
    getattr(gmic, "NUMPY_FORMAT_DEFAULT")
    getattr(gmic, "NUMPY_FORMAT_GMIC")
    getattr(gmic, "NUMPY_FORMAT_SCIKIT_IMAGE")
    getattr(gmic, "NUMPY_FORMAT_PIL")


@pytest.mark.parametrize("size_1d", [1, 5])
@pytest.mark.parametrize("size_2d", [1, 5])
@pytest.mark.parametrize("size_3d", [1, 5])
@pytest.mark.parametrize("size_4d", [1, 5])
@pytest.mark.parametrize("pixel_value_min", [0, -200])
@pytest.mark.parametrize("pixel_value_max", [0.05, 1000])
def test_fuzzy_1d_4d_random_gmic_matrices(
    size_1d, size_2d, size_3d, size_4d, pixel_value_min, pixel_value_max
):
    gmic_image_list = []
    gmic_command = "{},{},{},{} rand {},{}".format(
        size_1d, size_2d, size_3d, size_4d, pixel_value_min, pixel_value_max
    )
    gmic.run(gmic_command, gmic_image_list)
    gmic_image = gmic_image_list[-1]
    # Using the default astype dkind: float32
    # Using default output formatter: gmic.NUMPY_FORMAT_DEFAULT which has interleave=True, permute='zyxc'
    numpy_image = gmic_image.to_numpy_array()

    assert numpy_image.shape == (size_3d, size_2d, size_1d, size_4d)
    assert numpy_image.dtype == numpy.float32

    # Ensure numpy pixel values fit in the random values range
    numpy_image_min_value = numpy.amin(numpy_image)
    numpy_image_max_value = numpy.amax(numpy_image)
    assert pixel_value_min <= numpy_image_min_value <= pixel_value_max
    assert pixel_value_min <= numpy_image_max_value <= pixel_value_max

    # Ensure per-pixel equality in both numpy and gmic matrices
    for x in range(size_1d):
        for y in range(size_2d):
            for z in range(size_3d):
                for c in range(size_4d):
                    assert numpy_image[z, y, x, c] == gmic_image(x, y, z, c)


# Useful for some IDEs with debugging support
if __name__ == "__main__":
    pytest.main([os.path.abspath(os.path.dirname(__file__))])
