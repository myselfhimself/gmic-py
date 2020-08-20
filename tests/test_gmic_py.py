import contextlib
import inspect
import os
import pathlib
import re
from math import floor

import gmic
import pytest

# Tests parametrization: run calls to gmic.run(), gmic.Gmic() and gmic.Gmic().run() should have the same behaviour!
gmic_instance_types = {
    "argnames": "gmic_instance_run",
    "argvalues": [gmic.run, gmic.Gmic, gmic.Gmic().run],
    "ids": ["gmic_module_run", "gmic_instance_constructor_run", "gmic_instance_run"],
}

FLOAT_SIZE_IN_BYTES = 4


def assert_non_empty_file_exists(filename):
    """ Assert filename corresponds to non-empty file and return is pathlib.Path object
    """
    if type(filename) != pathlib.Path:
        a_file = pathlib.Path(filename)
    else:
        a_file = filename
    assert a_file.exists()
    assert a_file.stat().st_size > 0

    return a_file


def test_gmic_module_has_version_and_build_attributes():
    assert re.match(r"\d\.\d\.\d.*", gmic.__version__)
    assert re.match(r"(\S+:\S+\s?)+", gmic.__build__)


@pytest.mark.parametrize(**gmic_instance_types)
def test_catch_exceptions(gmic_instance_run):
    with pytest.raises(gmic.GmicException, match=r".*Unknown command or filename.*"):
        gmic_instance_run("badly formatted command")


def test_openmp_cflag_enabled():
    assert "openmp_enabled:1" in gmic.__build__


# @pytest.mark.xfail(reason="Linux x libgmic 2.9.1 fails on this", strict=False)
@pytest.mark.parametrize(**gmic_instance_types)
def test_run_gmic_ensure_openmp_linked_and_working(capfd, gmic_instance_run):
    import traceback
    import sys

    gmic_instance_run("v - sp lena eval. \"end(run('echo_stdout[] ',merge(t,max)))\"")
    outerr = capfd.readouterr()
    try:
        assert (
            int(outerr.out.strip()) > 0
        )  # should be "0\n" or "nan\n" if openmp not working
    except AssertionError:
        # Traceback display code from https://stackoverflow.com/a/11587247/420684
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb)  # Fixed format
        tb_info = traceback.extract_tb(tb)
        filename, line, func, text = tb_info[-1]
        pytest.fail(
            "parallel test case fails, OpenMP probably could not link or compile well on this platform, gmic parallelization will not work: stdout: {}; assert check: {}".format(
                outerr.out, text
            )
        )


@pytest.mark.parametrize(**gmic_instance_types)
def test_run_gmic_instance_run_helloworld(capfd, gmic_instance_run):
    # Using pytest stderr capture per https://docs.pytest.org/en/latest/capture.html#accessing-captured-output-from-a-test-function
    gmic_instance_run('echo_stdout "hello world"')
    outerr = capfd.readouterr()
    assert "hello world\n" == outerr.out


@pytest.mark.parametrize(**gmic_instance_types)
def test_run_gmic_instance_run_ppm_vs_pure_python_ppm_equality(gmic_instance_run):
    import array
    import filecmp

    ppm_filename_pure_python = "blue_red_example.ppm"
    ppm_filename_gmic = "blue_red_example_gmic.ppm"
    imgs = []

    # Pure Python ppm generation grabbed and patched from https://solarianprogrammer.com/2017/10/25/ppm-image-python-3/
    # PPM header
    width = 256
    height = 128
    maxval = 255
    ppm_header = "P6\n{} {}\n{}\n".format(width, height, maxval)

    # PPM image data (filled with blue)
    image = array.array("B", [0, 0, 255] * width * height)

    # Fill with red the rectangle with origin at (10, 10) and width x height = 50 x 80 pixels
    for y in range(10, 90):
        for x in range(10, 60):
            index = 3 * (y * width + x)
            image[index] = 255  # red channel
            image[index + 1] = 0  # green channel
            image[index + 2] = 0  # blue channel

    # Save the PPM image as a binary file
    with open(ppm_filename_pure_python, "wb") as f:
        f.write(bytearray(ppm_header, "ascii"))
        image.tofile(f)

    gmic_instance_run(
        "256,128,1,3 fill_color 0,0,255 rectangle 10,10,59,89,1,255,0,0 output {}".format(
            ppm_filename_gmic
        )
    )

    # Compare files saved on disk - OS comparison
    assert (
        filecmp.cmp(ppm_filename_pure_python, ppm_filename_gmic, shallow=False) is True
    )

    # Compare files loaded through gmic - GmicImages comparison
    ppms = []
    gmic_instance_run(
        "{} {}".format(ppm_filename_gmic, ppm_filename_pure_python), images=ppms
    )
    assert_gmic_images_are_identical(ppms[0], ppms[1], cpp_strict=False)
    assert_non_empty_file_exists(ppm_filename_pure_python).unlink()
    assert_non_empty_file_exists(ppm_filename_gmic).unlink()


@pytest.mark.parametrize(**gmic_instance_types)
def test_run_gmic_instance_run_simple_3pixels_png_output(gmic_instance_run):
    png_filename = "a.png"
    gmic_instance_run('input "(0,128,255)" output ' + png_filename)
    assert_non_empty_file_exists(png_filename).unlink()


@contextlib.contextmanager
def gmic_any_user_file(gmic_file_path=None):
    # DIY non-pytest fixture
    # If gmic_file_path is omitted, a temporary .gmic-suffixed file is created and yielded (use an with: statement)
    import random

    gmicpy_testing_command = "gmicpy_command_" + str(random.randint(0, 999))
    new_gmic_command = """{}:
repeat $! split_opacity
l[0] c 0,255 *[$>] -1 +[$>] 255 endl
a c
done
""".format(
        gmicpy_testing_command
    )
    is_making_temp_file = gmic_file_path is None
    if is_making_temp_file:
        import tempfile

        gmic_file_handle = tempfile.NamedTemporaryFile(
            suffix=".gmic", mode="w+", delete=False
        )
        gmic_file_handle.write(new_gmic_command)
        gmic_file_handle.flush()
        gmic_file_path = gmic_file_handle.name

        yield gmicpy_testing_command, gmic_file_path

        gmic_file_handle.close()
    else:
        backup_path = gmic_file_path + "_backup"

        existed = os.path.exists(gmic_file_path)

        if existed:
            os.rename(gmic_file_path, backup_path)
            assert os.path.exists(backup_path)
        new_gmic_command_file = open(gmic_file_path, "w")
        new_gmic_command_file.write(new_gmic_command)
        new_gmic_command_file.close()

        yield gmicpy_testing_command

        os.unlink(gmic_file_path)
        if existed:
            os.rename(backup_path, gmic_file_path)


@pytest.mark.parametrize(**gmic_instance_types)
def test_gmic_user_file_autoload_and_use(gmic_instance_run, request, capfd):
    # Testing gmic user file auto-load for any type of G'MIC run technique
    # 1. Hack the file to auto-load, injecting a custom command into it
    gmic.run("echo_stdout $_path_user")
    gmic_home_user_file = capfd.readouterr().out.strip()
    assert gmic_home_user_file is not ""

    with gmic_any_user_file(gmic_home_user_file) as gmicpy_testing_command:
        # If gmic_instance_run is the current fixture (ie. run() method of a same instance singleton)
        # reinitialize it, it was created too early in the suite and is not fresh with autoloaded conf
        if inspect.isbuiltin(gmic_instance_run) and gmic_instance_run is not gmic.run:
            g = gmic.Gmic()
            gmic_instance_run = g.run

        # 2. Check that our custom command was auto-loaded as expected
        gmic_instance_run("sp leno " + gmicpy_testing_command)


@pytest.mark.parametrize(**gmic_instance_types)
def test_gmic_user_file_explicit_load_and_use(gmic_instance_run, capfd):
    # Running more than one gmic instance should fail this test, because we need loaded gmic files to persist across runs
    # So only the gmic.Gmic().run method will succeed
    must_fail = gmic_instance_run is gmic.Gmic or gmic_instance_run is gmic.run

    with gmic_any_user_file() as (gmicpy_testing_command, custom_gmic_file):
        gmic_instance_run("m " + custom_gmic_file)

        if must_fail:
            with pytest.raises(
                gmic.GmicException,
                match=r".*Unknown command or filename '{}'.*".format(
                    gmicpy_testing_command
                ),
            ):
                gmic_instance_run("sp leno " + gmicpy_testing_command)
        else:
            gmic_instance_run("sp leno " + gmicpy_testing_command)


@pytest.mark.parametrize(**gmic_instance_types)
def test_gmic_filters_data_json_validation_and_gmicimage__data_str_attribute(
    gmic_instance_run,
):
    import json
    import re

    assert int(gmic.__version__.replace(".", "")) >= 290
    json_result = []
    gmic_instance_run("update")
    gmic_instance_run("parse_gui blur,json", images=json_result)

    # Ensure we have properly type results
    # If the below result is 0 (no item), .config/gmic (or OS-home settings dir) was probably not created
    assert len(json_result) == 1
    assert type(json_result[0]) == gmic.GmicImage

    # Ensure the _data_str dynamic attribute's contents is a JSON-parseable
    # string for this very situation
    json_result_str = json_result[0]._data_str
    assert type(json_result_str) == str
    json_decoded_filters = json.loads(json_result_str)

    # The following validation could happen someday with a JSON schema
    # - Ensure filtering on the 'blur' keywork worked
    # - Ensure the JSON structure is more or less as expected
    assert json_decoded_filters["format_version"] == "gmic_json_1.0"
    assert re.match(r"\d.\d.\d", json_decoded_filters["gmic_version"])

    assert len(json_decoded_filters["categories"]) > 5
    for category in json_decoded_filters["categories"]:
        assert "name" in category
        assert "filters" in category
        for filter in category["filters"]:

            assert (
                "blur" in filter["name"].lower() or "blur" in filter["command"].lower()
            )
            if "parameters" in filter:
                for parameter in filter["parameters"]:
                    assert "type" in parameter
                    if parameter["type"] not in ("separator", "note", "link", "point"):
                        assert (
                            "pos" in parameter
                            and "name" in parameter
                            and "default" in parameter
                        )


@pytest.mark.parametrize(**gmic_instance_types)
def test_run_gmic_instance_run_simple_demo_png_output_and_input(gmic_instance_run):
    """ Ensure that zlib is properly linked and ensures that either
    the png library used or the 'convert' tool of the imagemagick suite, for saving png"""

    png_filename = "demo.png"
    gmic_instance_run("testimage2d 512 output " + png_filename)
    a_png = assert_non_empty_file_exists(png_filename)

    # Open generated file
    gmic_instance_run("input " + png_filename)
    a_png.unlink()


@pytest.mark.parametrize(**gmic_instance_types)
def test_run_gmic_instance_run_simple_3pixels_bmp_output(gmic_instance_run):
    """ Ensure that the native bmp file output works"""

    bmp_filename = "a.bmp"
    gmic_instance_run('input "(0,128,255)" output ' + bmp_filename)
    assert_non_empty_file_exists(bmp_filename).unlink()


def test_gmic_image_parameters_fuzzying():
    import struct

    # This should not fail - empty data initializations of a GmicImage
    gmic.GmicImage()
    gmic.GmicImage(None)
    gmic.GmicImage(None, 1, 3)
    gmic.GmicImage(None, 1, 3, 5)
    gmic.GmicImage(None, 1, 3, 5, 22)
    gmic.GmicImage(width=1, depth=3)

    with pytest.raises(TypeError):
        # This used to segfault / fail with core dump
        a = gmic.GmicImage(struct.pack("8f", 1, 3, 5, 7, 2, 6, 10, 14), 4, 2, 1, 1)
        a("wrong", "parameters")

    # Gmic Image with unmatching dimensions compared to its buffer
    with pytest.raises(ValueError) as excinfo:
        b = gmic.GmicImage(struct.pack("8f", 1, 3, 5, 7, 2, 6, 10, 14), 4, 2, 0)
    assert "0*" in str(excinfo.value)

    # Gmic Image with negative dimensions
    with pytest.raises(ValueError) as excinfo:
        b = gmic.GmicImage(struct.pack("8f", 1, 3, 5, 7, 2, 6, 10, 14), 4, 2, -3)
    assert "-24*" in str(excinfo.value)


def test_gmic_image_handmade_attributes_copying():
    import struct

    b = gmic.GmicImage(
        struct.pack("8f", 1, 3, 5, 7, 2, 6, 10, 14), 2, 4, 1, shared=False
    )
    c = gmic.GmicImage(
        b._data, b._width, b._height, b._depth, b._spectrum, b._is_shared
    )
    assert_gmic_images_are_identical(b, c)


def test_gmic_image_construct_buffer_check_and_destroy():
    import re
    import struct

    # Function parameter-time bytes generation: with bad reference management, reading the buffer's bytes later should fail
    i = gmic.GmicImage(struct.pack("8f", 1, 3, 5, 7, 2, 6, 10, 14), 4, 2, 1, 1)
    assert re.compile(
        r"<gmic.GmicImage object at 0x[a-f0-9]+ with _data address at 0x[0-9a-z]+, w=4 h=2 d=1 s=1 shared=0>"
    ).match(repr(i))
    print(dir(i))
    assert i(0) == 1
    assert type(i(0)) == float
    assert i(0, 1) == 2
    assert i(3, 1) == 14
    del i  # Tentative reference decrementing for crash


def test_gmic_image_float_third_dimension_and_precision_conservation():
    import struct
    import re
    import decimal

    # Creating an GmicImage object with an external reference (ie. the regular case)
    first_float = 0.12345
    second_float = 848.48383093
    simple_float_buffer = struct.pack("2f", first_float, second_float)
    a = gmic.GmicImage(simple_float_buffer, 1, 1, 2, 1)
    assert re.compile(
        r"<gmic.GmicImage object at 0x[a-f0-9]+ with _data address at 0x[0-9a-z]+, w=1 h=1 d=2 s=1 shared=0>"
    ).match(repr(a))
    first_float_decimal_places = decimal.Decimal(first_float).as_tuple().digits
    stored_float_decimal_places = decimal.Decimal(a(0, 0, 0)).as_tuple().digits

    common_first_decimals = 0
    for i, j in zip(first_float_decimal_places, stored_float_decimal_places):
        print(i, j)
        if i == j:
            common_first_decimals += 1
        else:
            break
    # We want at list the 5 decimal digits of eg. 0.12345 to remain between GmicImage input and output, even though much higher precision happens in background
    assert common_first_decimals > 5


@pytest.mark.parametrize(**gmic_instance_types)
def test_gmic_image_generation_and_shared_multiple_gmic_print_runs(gmic_instance_run):
    import struct

    shared = True  # having shared False is enough for now to have a crash below, let us test something else as crashing: buffer integrity through multiple run's
    i = gmic.GmicImage(struct.pack("8f", 1, 3, 5, 7, 2, 6, 10, 14), 4, 2, 1, 1, shared)
    pixel_before_gmic_run = i(0, 0)
    gmic_instance_run("print print print", i)
    pixel_after_gmic_instance_run = i(0, 0)
    assert pixel_before_gmic_run == pixel_after_gmic_instance_run


# Per https://stackoverflow.com/a/33024979/420684
# This starts to be builtin from Python > 3.5
def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def assert_get_proper_print_regex(w, h, search_str):
    import re

    bytes_size = int(round(w) * round(h) * FLOAT_SIZE_IN_BYTES)
    bytes_size_str = (
        "{} Kio".format(floor(bytes_size / 1024))
        if bytes_size > 1024
        else "{} b".format(bytes_size)
    )
    assert (
        re.compile(
            r"size = \({},{},1,1\) \[{} of floats\](.*)\n(.*)\n(.*)min = 0".format(
                round(w), round(h), bytes_size_str
            ),
            flags=re.MULTILINE,
        ).search(search_str)
        is not None
    )


def assert_gmic_images_are_identical(gmic_image1, gmic_image2, cpp_strict=True):
    if cpp_strict:
        assert (
            gmic_image1 == gmic_image2
        )  # Use of the builtin __eq__ and __ne__ operators relying on C++ CImg data buffers compare, without w,h,d,s check
        assert not (gmic_image1 != gmic_image2)
    assert gmic_image1._width == gmic_image2._width
    assert gmic_image1._height == gmic_image2._height
    assert gmic_image1._depth == gmic_image2._depth
    assert gmic_image1._spectrum == gmic_image2._spectrum
    assert gmic_image1._data == gmic_image2._data
    assert gmic_image1._is_shared == gmic_image2._is_shared
    for x in range(gmic_image1._width):
        for y in range(gmic_image1._height):
            for z in range(gmic_image1._depth):
                for c in range(gmic_image1._spectrum):
                    assert gmic_image1(x, y, z, c) == gmic_image2(x, y, z, c)


def assert_gmic_image_is_filled_with(gmic_image, w, h, d, s, pixel_value):
    for spectrum in range(int(s)):
        for x in range(int(w)):
            for y in range(int(h)):
                for z in range(int(d)):
                    for c in range(int(s)):
                        pixel = gmic_image(x, y, z, c)
                        assert isclose(pixel, pixel_value)


@pytest.mark.parametrize(**gmic_instance_types)
def test_gmic_image_generation_and_gmic_multiple_resize_run(capfd, gmic_instance_run):
    import struct

    w = 240
    h = 240
    d = 1
    s = 1
    command_to_apply = "resize 50%,50%"
    # Init first 100% size image
    struct_pack_params = (str(w * h) + "f",) + (0,) * w * h
    i = gmic.GmicImage(struct.pack(*struct_pack_params), w, h, d, s, shared=False)
    # Divide original size by 2 and check pixels stability
    gmic_instance_run("{} print".format(command_to_apply), i)
    outerr = capfd.readouterr()
    w = w / 2
    h = h / 2
    assert_get_proper_print_regex(w, h, search_str=outerr.err)
    assert_gmic_image_is_filled_with(i, w, h, d, s, 0)
    # Divide original size by 4 and check pixels stability
    gmic_instance_run("{} print".format(command_to_apply), i)
    outerr = capfd.readouterr()
    w = w / 2
    h = h / 2
    assert_get_proper_print_regex(w, h, search_str=outerr.err)
    assert_gmic_image_is_filled_with(i, w, h, d, s, 0)
    # Divide original size by 16 (now twice by 2) and check pixels stability
    gmic_instance_run("{} {} print".format(command_to_apply, command_to_apply), i)
    outerr = capfd.readouterr()
    w = w / 4
    h = h / 4
    assert_get_proper_print_regex(w, h, search_str=outerr.err)
    assert_gmic_image_is_filled_with(i, w, h, d, s, 0)


@pytest.mark.parametrize(**gmic_instance_types)
def test_gmic_image_readonly_attributes_and_bytes_stability(gmic_instance_run):
    import struct

    w = 60
    h = 80
    float_array = struct.pack(*((str(w * h) + "f",) + (0,) * w * h))

    # Ensuring GmicImage's parameters stability after initialization
    i = gmic.GmicImage(float_array, w, h)
    assert i._width == w
    assert i._height == h
    assert i._depth == 1
    assert i._spectrum == 1
    assert i._is_shared == False
    assert i._data == float_array  # First bytes array check
    assert len(i._data) == len(float_array)  # Additional bytes array check just in case

    # Ensure GmicImage's parameters stability after a resize operation
    gmic_instance_run("resize 50%,50%", i)
    required_floats = int(w * h / 4)
    expected_result_float_array = struct.pack(
        *((str(required_floats) + "f",) + (0,) * required_floats)
    )
    assert i._width == w / 2
    assert i._height == h / 2
    assert i._depth == 1
    assert i._spectrum == 1
    assert i._is_shared == False
    assert i._data == expected_result_float_array
    assert len(i._data) == len(expected_result_float_array)

    # Trying with a shared=True type of GmicImage with all dimensions and spectrum channels used
    w = 1
    h = 43
    d = 37
    s = 3
    float_array = struct.pack(*((str(w * h * d * s) + "f",) + (0,) * w * h * d * s))
    i = gmic.GmicImage(float_array, w, h, d, s, shared=True)
    gmic_instance_run("add 1", i)
    required_floats = int(w * h * d * s)
    expected_uniform_pixel_value = 1.0
    expected_result_float_array = struct.pack(
        *(
            (str(required_floats) + "f",)
            + (expected_uniform_pixel_value,) * required_floats
        )
    )
    assert_gmic_image_is_filled_with(i, w, h, d, s, expected_uniform_pixel_value)
    assert i._width == w
    assert i._height == h
    assert i._depth == d
    assert i._spectrum == s
    assert i._is_shared == True
    assert i._data == expected_result_float_array  # First bytes array check
    assert len(i._data) == len(
        expected_result_float_array
    )  # Additional bytes array check just in case


def test_gmic_image_readonly_forbidden_write_attributes():
    import struct

    w = 60
    h = 80
    float_array = struct.pack(*((str(w * h) + "f",) + (0,) * w * h))
    real_attributes = (
        "_data",
        "_data_str",
        "_width",
        "_height",
        "_depth",
        "_spectrum",
        "_is_shared",
    )

    # Ensuring GmicImage's parameters stability after initialization
    i = gmic.GmicImage(float_array, w, h)

    # Ensure unknown attributes fail being read
    with pytest.raises(AttributeError) as excinfo:
        getattr(i, "unkown")
    assert "no attribute 'unkown'" in str(excinfo.value)

    # Ensure known attributes fail being set with an error message variant
    # Note that we do not test setting non-existing attributes
    # because the pythonic object type allows creating new attributes on the fly by setting them
    for a in real_attributes:
        with pytest.raises(AttributeError, match=r".*(readonly|not writable).*"):
            setattr(i, a, "anything")


@pytest.mark.parametrize(**gmic_instance_types)
def test_gmic_images_list_with_image_names_multiple_add_filter_run(gmic_instance_run):
    import struct

    w = 60
    h = 80
    d = s = 1
    nb_images = 10
    base_pixel_multiplicator = 10.0

    image_names = ["some_image_" + str(i) for i in range(nb_images)]
    untouched_image_names = ["some_image_" + str(i) for i in range(nb_images)]
    images = [
        gmic.GmicImage(
            struct.pack(
                *((str(w * h) + "f",) + (i * base_pixel_multiplicator,) * w * h)
            ),
            w,
            h,
        )
        for i in range(nb_images)
    ]
    # First run adding 1 of value to all pixels in all images
    gmic_instance_run("add 1", images, image_names)
    for c, image in enumerate(images):
        assert_gmic_image_is_filled_with(
            images[c], w, h, d, s, c * base_pixel_multiplicator + 1
        )
    assert untouched_image_names == image_names

    # Second run adding 2 of value to all pixels in all images
    gmic_instance_run("add 2", images, image_names)
    for c, image in enumerate(images):
        assert_gmic_image_is_filled_with(
            images[c], w, h, d, s, c * base_pixel_multiplicator + 2 + 1
        )
    assert untouched_image_names == image_names


def test_gmic_image_attributes_visibility():
    import struct

    a = gmic.GmicImage(struct.pack("1f", 1))
    for required_attribute in (
        "_width",
        "_height",
        "_depth",
        "_spectrum",
        "_is_shared",
        "_data",
    ):
        assert required_attribute in dir(a)


def test_gmic_image_object_and_attribute_types():
    import struct

    a = gmic.GmicImage(struct.pack("1f", 1))
    assert type(a) == gmic.GmicImage
    assert type(a._width) == int
    assert type(a._height) == int
    assert type(a._width) == int
    assert type(a._depth) == int
    assert type(a._spectrum) == int
    assert type(a._is_shared) == bool
    assert type(a._data) == bytes


@pytest.mark.parametrize(**gmic_instance_types)
def test_gmic_instance_run_parameters_fuzzying_basic(gmic_instance_run):
    import struct

    w = 60
    h = 80
    d = s = 1
    # 0 parameters should not be allowed for the .run() method
    # except for the Gmic class's own constructor which will not trigger .run() if not fed with any parameters
    if gmic_instance_run != gmic.Gmic:
        with pytest.raises(TypeError):
            gmic_instance_run()

    # 1 correct command
    gmic_instance_run("echo_stdout 'bonsoir'")

    # 1 parameters-depending command without an image or with empty list
    gmic_instance_run("print")
    gmic_instance_run("print", [])

    # 1 correct GmicImage, 1 correct command, in wrong order
    with pytest.raises(
        TypeError, match=r".*argument 1 must be str, not gmic.GmicImage.*"
    ):
        gmic_instance_run(gmic.GmicImage(struct.pack("1f", 1.0)), "print")

    # 1 correct GmicImage, 1 correct command, some strange keyword
    with pytest.raises(TypeError, match=r".*hey.*is an invalid keyword argument.*"):
        gmic_instance_run("print", gmic.GmicImage(struct.pack("1f", 1.0), hey=3))

    # 1 correct GmicImage, 1 correct command with flipped keywords
    gmic_instance_run(images=gmic.GmicImage(struct.pack("1f", 1.0)), command="print")

    # 1 correct list of GmicImages, 1 correct command with flipped keywords
    gmic_instance_run(
        images=[
            gmic.GmicImage(struct.pack("1f", 1.0)),
            gmic.GmicImage(struct.pack("2f", 1.0, 2.0), 2),
        ],
        command="add 3",
    )

    # 1 GmicImage, no command
    with pytest.raises(
        TypeError, match=r".*argument 1 must be str, not gmic.GmicImage.*"
    ):
        gmic_instance_run(gmic.GmicImage(struct.pack("1f", 1.0)))

    # 1 GmicImage, no correct command
    with pytest.raises(
        gmic.GmicException, match=r".*Unknown command or filename 'hey'.*"
    ):
        gmic_instance_run(images=gmic.GmicImage(struct.pack("1f", 1.0)), command="hey")

    # 1 non-GmicImage, 1 correct command
    with pytest.raises(
        TypeError,
        match=r".*'int' 'images' parameter must be a .*GmicImage.* or .*list.*",
    ):
        gmic_instance_run(images=42, command="print")

    # 1 GmicImage, 1 correct command, one non-list of image names
    with pytest.raises(
        TypeError, match=r".* 'image_names' parameter must be a list.*str.*"
    ):
        gmic_instance_run(
            images=gmic.GmicImage(struct.pack("1f", 1.0)),
            image_names=3,
            command="add 4",
        )

    # 1 iterable "list" for images but not list (here, a str), 1 correct command
    with pytest.raises(
        TypeError,
        match=r".*'str' 'images' parameter must be a .*GmicImage.* or .*list.*",
    ):
        gmic_instance_run(images="some iterable object", command="print")

    # 1 list of not-only GmicImages, 1 correct command
    with pytest.raises(
        TypeError, match=r"'str'.*object found at position 1 in 'images' list.*"
    ):
        gmic_instance_run(
            images=[gmic.GmicImage(struct.pack("1f", 1.0)), "not gmic image"],
            command="print",
        )

    # 1 list of GmicImages, 1 correct command
    gmic_instance_run(
        images=[
            gmic.GmicImage(struct.pack("1f", 1.0)),
            gmic.GmicImage(struct.pack("1f", 1.0)),
        ],
        command="print",
    )

    # 1 list of GmicImages, no command
    with pytest.raises(TypeError, match=r".*argument 'command'.*"):
        gmic_instance_run(
            images=[
                gmic.GmicImage(struct.pack("1f", 1.0)),
                gmic.GmicImage(struct.pack("1f", 1.0)),
            ]
        )

    # 1 list of GmicImages, multiline whitespace-bloated correct command
    # This most probably requires compilation with libgmic>=2.8.3 to work
    gmic_instance_run(
        images=[
            gmic.GmicImage(struct.pack("1f", 1.0)),
            gmic.GmicImage(struct.pack("1f", 1.0)),
        ],
        command=" \n\n\r\r  print   \n\r   \t print   \n\n\r\t\t    print    \n",
    )


@pytest.mark.parametrize(**gmic_instance_types)
def test_gmic_instance_run_parameters_fuzzying_for_lists_cardinality(gmic_instance_run):
    import struct

    two_images = [
        gmic.GmicImage(struct.pack("2f", 2.0, 3.0), 1, 2),
        gmic.GmicImage(struct.pack("2f", 17.0, 5.0), 2),
    ]
    original_two_images = [
        gmic.GmicImage(struct.pack("2f", 2.0, 3.0), 1, 2),
        gmic.GmicImage(struct.pack("2f", 17.0, 5.0), 2),
    ]
    two_image_names = ["a", "b"]
    original_two_image_names = ["a", "b"]

    # 1 list of correct length string image_names, correct images, 1 correct command
    gmic_instance_run(images=two_images, image_names=two_image_names, command="print")

    # 1 list of correct length string image_names, no images at all, 1 correct command
    gmic_instance_run(image_names=two_image_names, command="print")

    # 1 list of correct length string image_names, empty images list, 1 correct command
    input_empty_images = []
    input_command = "print"
    gmic_instance_run(
        images=input_empty_images, image_names=two_image_names, command=input_command
    )
    # here gmic will slice the image_names underlying gmic_list to make it the same size as the images gmic_list length
    # if this fails, this means we did not update the image_names output Python object..
    assert len(two_image_names) == 0 and type(two_image_names) == list
    assert len(input_empty_images) == 0 and type(input_empty_images) == list
    assert input_command == "print" and type(input_command) == str

    # empty image_names, empty images list, 1 correct command
    gmic_instance_run(images=[], image_names=[], command="print")

    two_images = [
        gmic.GmicImage(struct.pack("2f", 2.0, 3.0), 1, 2),
        gmic.GmicImage(struct.pack("2f", 17.0, 5.0), 2),
    ]
    original_two_images = [
        gmic.GmicImage(struct.pack("2f", 2.0, 3.0), 1, 2),
        gmic.GmicImage(struct.pack("2f", 17.0, 5.0), 2),
    ]
    two_image_names = ["a", "b"]
    original_two_image_names = ["a", "b"]

    # Testing decreasing size of the images list
    gmic_instance_run(images=two_images, image_names=two_image_names, command="rm[0]")
    # Here G'MIC will remove the first image, so the output two_images should have been changed and be a single-item list
    assert len(two_images) == 1
    # assert two_images[0] == original_two_images[1]
    assert_gmic_images_are_identical(two_images[0], original_two_images[1])
    assert two_image_names == ["b"]

    # Testing single-image parameter with decreasing size of images list (processed by the binding as a 1 item list)
    two_images = [
        gmic.GmicImage(struct.pack("2f", 2.0, 3.0), 1, 2),
        gmic.GmicImage(struct.pack("2f", 17.0, 5.0), 2),
    ]
    original_two_images = [
        gmic.GmicImage(struct.pack("2f", 2.0, 3.0), 1, 2),
        gmic.GmicImage(struct.pack("2f", 17.0, 5.0), 2),
    ]
    two_image_names = ["a", "b"]
    original_two_image_names = ["a", "b"]

    with pytest.raises(
        RuntimeError,
        match=r".*was removed by your G'MIC command.*emptied.*image_names.*untouched.*",
    ):
        gmic_instance_run(
            images=two_images[0], image_names=two_image_names, command="rm[0]"
        )
    assert (
        two_images[0] == original_two_images[0]
    )  # Ensuring input image is preserved (ie. untouched)
    assert (
        two_image_names == original_two_image_names
    )  # Ensuring image names are preserved

    # 1 list of incorrect length string image_names, correct images, 1 correct command
    two_images = [
        gmic.GmicImage(struct.pack("2f", 2.0, 3.0), 1, 2),
        gmic.GmicImage(struct.pack("2f", 17.0, 5.0), 2),
    ]
    original_two_images = [
        gmic.GmicImage(struct.pack("2f", 2.0, 3.0), 1, 2),
        gmic.GmicImage(struct.pack("2f", 17.0, 5.0), 2),
    ]
    one_image_names = ["b"]

    gmic_instance_run(images=two_images, image_names=one_image_names, command="print")
    assert_gmic_images_are_identical(two_images[0], original_two_images[0])
    assert_gmic_images_are_identical(two_images[1], original_two_images[1])
    assert one_image_names == ["b", "[unnamed]"]

    # 1 list of incorrect length string image_names, correct images, 1 correct command
    two_images = [
        gmic.GmicImage(struct.pack("2f", 2.0, 3.0), 1, 2),
        gmic.GmicImage(struct.pack("2f", 17.0, 5.0), 2),
    ]
    original_two_images = [
        gmic.GmicImage(struct.pack("2f", 2.0, 3.0), 1, 2),
        gmic.GmicImage(struct.pack("2f", 17.0, 5.0), 2),
    ]
    one_image_names = ["", ""]

    gmic_instance_run(images=two_images, image_names=one_image_names, command="print")
    assert_gmic_images_are_identical(two_images[0], original_two_images[0])
    assert_gmic_images_are_identical(two_images[1], original_two_images[1])
    assert one_image_names == ["", ""]

    # 1 image GmicImage, 1 image_names string, 1 correct command
    gmic_instance_run(images=two_images[0], image_names="single_image", command="print")
    assert_gmic_images_are_identical(two_images[0], original_two_images[0])

    # 1 image GmicImage in a list, 1 image_names string, 1 correct command
    with pytest.raises(
        TypeError,
        match=r".*'images' parameter must be a '.*GmicImage.*' if the 'image_names' parameter is a bare 'str'.*",
    ):
        gmic_instance_run(
            images=[two_images[0]], image_names="single_image", command="print"
        )

    # 1 non-list image_names sequence, correct images, 1 correct command
    with pytest.raises(
        TypeError,
        match=r".*'tuple' 'image_names' parameter must be a .*list.*of.*str.*",
    ):
        gmic_instance_run(images=two_images, image_names=("a", "b"), command="print")

    # 1 empty list image_names, correct images, 1 correct command
    empty_image_names = []
    gmic_instance_run(images=two_images, image_names=empty_image_names, command="print")
    assert empty_image_names == ["[unnamed]", "[unnamed]"]

    # 1 list of image_names with not only strings, correct images, 1 correct command
    bad_content_image_names = [3, "hey"]
    with pytest.raises(
        TypeError,
        match=r"'int'.*input element found at position 0 in 'image_names' list.*",
    ):
        gmic_instance_run(
            images=two_images, image_names=bad_content_image_names, command="print"
        )

    # 1 list of image_names with 'bytes' strings, correct images, 1 correct command
    bad_content_image_names = [b"bonsoir", "hey"]
    with pytest.raises(
        TypeError,
        match=r"'bytes'.*input element found at position 0 in 'image_names' list.*",
    ):
        gmic_instance_run(
            images=two_images, image_names=bad_content_image_names, command="print"
        )


def test_gmic_image_rich_compare():
    import struct

    a = gmic.GmicImage(struct.pack("2f", 1.0, 2.0), 2, 1)
    a2 = gmic.GmicImage(struct.pack("2f", 1.0, 2.0), 2, 1)
    a3 = gmic.GmicImage(struct.pack("2f", 1.0, 2.0), 1, 2)
    b = gmic.GmicImage(struct.pack("1f", 3.0))
    b2 = gmic.GmicImage(struct.pack("1f", 3.0))

    # Trying == operator between GmicImages (the C++ operator just compares buffers, not dimensions)
    assert a == a2 == a3
    assert b == b2
    assert not (b == a)

    # Trying != operator between GmicImages
    assert b != a
    assert not (b != b2)

    # Comparing GmicImage with a different type
    assert b != "b"

    # Trying all operators other than == and !=, they must be "not supported"
    for operator, representation in zip(
        ["__gt__", "__ge__", "__lt__", "__le__"], [">", ">=", "<", "<="]
    ):
        assert getattr(b, operator)(b) == NotImplemented


@pytest.mark.skip(
    reason="some machines/OS are too brave and will try this allocation for minutes instead of erroring"
)
def test_gmic_image_memory_exhaustion_initialization_resilience():
    import struct

    # out of memory
    pytest.skip()
    with pytest.raises(MemoryError):
        gmic.GmicImage(
            struct.pack("8f", (0.0,) * 494949 * 2000 * 393938 * 499449),
            494949,
            2000,
            393938,
            499449,
        )


@pytest.mark.parametrize(**gmic_instance_types)
def test_gmic_images_post_element_removal_conservation(gmic_instance_run):
    import struct

    a = gmic.GmicImage(struct.pack("2f", 1.0, 2.0), 2, 1)
    original_a = gmic.GmicImage(struct.pack("2f", 1.0, 2.0), 2, 1)

    images = [a, a, a]
    # If this core dumps, this means that there is a missing or badly put memcpy() on input list GmicImage(s) retrieval
    gmic_instance_run(command="rm[0]", images=images)
    for i in images:
        assert_gmic_images_are_identical(i, original_a)


def test_gmic_class_void_parameters_instantation_and_simple_hello_world_run(capfd):
    gmic_instance = gmic.Gmic()
    gmic_instance.run('echo_stdout "hello world"')
    outerr = capfd.readouterr()
    assert "hello world\n" == outerr.out

    # No variable assignment
    gmic.Gmic().run('echo_stdout "hello world2"')
    outerr = capfd.readouterr()
    assert "hello world2\n" == outerr.out


def test_gmic_class_direct_run_remains_usable_instance():
    gmic_instance = gmic.Gmic('echo_stdout "single instance"')
    assert type(gmic_instance) == gmic.Gmic
    gmic_instance.run('echo_stdout "other run"')


def test_filling_empty_gmicimage_list_with_input_image_nonregtest_issue_30():
    images = []
    gmic.run(images=images, command="sp lena")
    assert len(images) == 1
    assert type(images[0]) == gmic.GmicImage


def test_gmic_module_run_vs_single_instance_run_benchmark():
    from time import time

    testing_command = "sp lena blur 10 blur 30 blur 4"
    testing_iterations_max = 100
    expected_speed_improvement_by_single_instance_runs = 1.1  # at least 10%

    time_before_module_runs = time()
    for a in range(testing_iterations_max):
        gmic.run(testing_command)
    time_after_module_runs = time()

    time_before_instance_runs = time()
    gmic_instance = gmic.Gmic()
    for a in range(testing_iterations_max):
        gmic_instance.run(testing_command)
    time_after_instance_runs = time()

    assert (
        time_after_instance_runs - time_before_instance_runs
    ) * expected_speed_improvement_by_single_instance_runs < (
        time_after_module_runs - time_before_module_runs
    )


# Useful for some IDEs with debugging support
if __name__ == "__main__":
    pytest.main([os.path.abspath(os.path.dirname(__file__))])
