import pytest

FLOAT_SIZE_IN_BYTES = 4

def test_import_gmic():
    import gmic

def test_catch_exceptions():
    import gmic
    with pytest.raises(Exception, match=r".*Unknown command or filename.*"):
        gmic.run('badly formatted command')

def test_run_gmic_ensure_openmp_linked_and_working(capfd):
    import gmic
    import traceback
    import sys
    gmic.run('v - sp lena eval. "end(call(\'echo_stdout[] \',merge(t,max)))"')
    outerr = capfd.readouterr()
    try:
        assert int(outerr.out.strip()) > 0 # should be "0\n" or "nan\n" if openmp not working
    except AssertionError:
        # Traceback display code from https://stackoverflow.com/a/11587247/420684
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb) # Fixed format
        tb_info = traceback.extract_tb(tb)
        filename, line, func, text = tb_info[-1]
        pytest.fail('parallel test case fails, OpenMP probably could not link or compile well on this platform, gmic parallelization will not work: stdout: {}; assert check: {}'.format(outerr.out, text))

def test_run_gmic_run_helloworld(capfd):
    import gmic
    # Using pytest stderr capture per https://docs.pytest.org/en/latest/capture.html#accessing-captured-output-from-a-test-function
    gmic.run('echo_stdout "hello world"')
    outerr = capfd.readouterr()
    assert "hello world\n" == outerr.out

def test_run_gmic_run_simple_3pixels_png_output():
    import gmic
    import pathlib
    png_filename = "a.png"
    gmic.run('input "(0,128,255)" output ' + png_filename)
    a_png = pathlib.Path(png_filename)
    # Ensure generated png file exists and is non empty
    assert a_png.exists()
    assert a_png.stat().st_size > 0
    a_png.unlink()


def test_run_gmic_run_simple_demo_png_output_and_input():
    """ Ensure that zlib is properly linked and ensures that either
    the png library used or the 'convert' tool of the imagemagick suite, for saving png"""
    import gmic
    import pathlib
    png_filename = "demo.png"
    gmic.run('testimage2d 512 output ' + png_filename)
    a_png = pathlib.Path(png_filename)
    # Ensure generated png file exists and is non empty
    assert a_png.exists()
    assert a_png.stat().st_size > 0

    # Open generated file
    gmic.run('input ' + png_filename)
    a_png.unlink()


def test_run_gmic_run_simple_3pixels_bmp_output():
    """ Ensure that the native bmp file output works"""
    import gmic
    import pathlib
    bmp_filename = "a.bmp"
    gmic.run('input "(0,128,255)" output ' + bmp_filename)
    a_bmp = pathlib.Path(bmp_filename)
    # Ensure generated bmp file exists and is non empty
    assert a_bmp.exists()
    assert a_bmp.stat().st_size > 0
    a_bmp.unlink()

def test_gmic_image_parameters_fuzzying():
    import gmic
    import struct
    import re
    # Fail test if anything else as a TypeError is raised
    with pytest.raises(TypeError):
        # This used to segfault / fail with core dump
        i = gmic.GmicImage(None, 1, 3)

    with pytest.raises(TypeError):
        # This used to segfault / fail with core dump
        a = gmic.GmicImage(struct.pack('8f', 1, 3, 5, 7, 2, 6, 10, 14), 4, 2, 1, 1)
        a('wrong', 'parameters')

    # Gmic Image with unmatching dimensions compared to its buffer
    with pytest.raises(ValueError) as excinfo:
        b = gmic.GmicImage(struct.pack('8f', 1, 3, 5, 7, 2, 6, 10, 14), 4, 2, 0)
    assert "0*" in str(excinfo.value)

    # Gmic Image with negative dimensions
    with pytest.raises(ValueError) as excinfo:
        b = gmic.GmicImage(struct.pack('8f', 1, 3, 5, 7, 2, 6, 10, 14), 4, 2, -3)
    assert "-24*" in str(excinfo.value)

def test_gmic_image_handmade_attributes_copying():
    import gmic
    import struct
    b = gmic.GmicImage(struct.pack('8f', 1, 3, 5, 7, 2, 6, 10, 14), 2,4,1, shared=False)
    c = gmic.GmicImage(b._data, b._width, b._height, b._depth, b._spectrum, b._is_shared)
    assert_gmic_images_are_identical(b,c)

def test_gmic_image_construct_buffer_check_and_destroy():
    import re
    import gmic
    import struct
    # Function parameter-time bytes generation: with bad reference management, reading the buffer's bytes later should fail
    i = gmic.GmicImage(struct.pack('8f', 1, 3, 5, 7, 2, 6, 10, 14), 4, 2, 1, 1)
    assert re.compile(r"<gmic.GmicImage object at 0x[a-f0-9]+ with _data address at 0x[0-9a-z]+, w=4 h=2 d=1 s=1 shared=0>").match(repr(i))
    print(dir(i))
    assert i(0) == 1
    assert type(i(0)) == float
    assert i(0,1) == 2
    assert i(3,1) == 14
    del i # Tentative reference decrementing for crash

def test_gmic_image_float_third_dimension_and_precision_conservation():
    import gmic
    import struct
    import re
    import decimal
    # Creating an GmicImage object with an external reference (ie. the regular case)
    first_float = 0.12345
    second_float = 848.48383093
    simple_float_buffer = struct.pack('2f', first_float, second_float)
    a = gmic.GmicImage(simple_float_buffer, 1, 1, 2, 1)
    assert re.compile(r"<gmic.GmicImage object at 0x[a-f0-9]+ with _data address at 0x[0-9a-z]+, w=1 h=1 d=2 s=1 shared=0>").match(repr(a))
    first_float_decimal_places = decimal.Decimal(first_float).as_tuple().digits
    stored_float_decimal_places = decimal.Decimal(a(0, 0, 0)).as_tuple().digits

    common_first_decimals = 0
    for i,j in zip(first_float_decimal_places, stored_float_decimal_places):
        print(i, j)
        if i==j:
            common_first_decimals += 1
        else:
            break
    # We want at list the 5 decimal digits of eg. 0.12345 to remain between GmicImage input and output, even though much higher precision happens in background
    assert common_first_decimals > 5

def test_gmic_image_generation_and_shared_multiple_gmic_print_runs():
    import gmic
    import struct
    import re
    shared = True # having shared False is enough for now to have a crash below, let us test something else as crashing: buffer integrity through multiple run's
    i = gmic.GmicImage(struct.pack('8f', 1, 3, 5, 7, 2, 6, 10, 14), 4, 2, 1, 1, shared)
    pixel_before_gmic_run = i(0,0)
    gmic.run("print print print", i)
    pixel_after_gmic_run = i(0,0)
    assert pixel_before_gmic_run == pixel_after_gmic_run

# Per https://stackoverflow.com/a/33024979/420684
# This starts to be builtin from Python > 3.5
def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def assert_get_proper_print_regex(w, h, search_str):
    import re
    import time
    assert re.compile(r"size = \({},{},1,1\) \[{} b of floats\](.*)\n(.*)\n(.*)min = 0".format(round(w), round(h), int(round(w)*round(h)*FLOAT_SIZE_IN_BYTES)), flags=re.MULTILINE).search(search_str) is not None

def assert_gmic_images_are_identical(gmic_image1, gmic_image2):
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
                    assert gmic_image1(x,y,z,c) == gmic_image2(x,y,z,c)

def assert_gmic_image_is_filled_with(gmic_image, w, h, d, s, pixel_value):
    for spectrum in range(int(s)):
        for x in range(int(w)):
            for y in range(int(h)):
                for z in range(int(d)):
                    for c in range(int(s)):
                        pixel = gmic_image(x, y, z, c)
                        assert isclose(pixel, pixel_value)

def test_gmic_image_generation_and_gmic_multiple_resize_run(capfd):
    import gmic
    import struct
    import re
    w = 60
    h = 60
    d = 1
    s = 1
    command_to_apply = "resize 50%,50%"
    # Init first 100% size image
    struct_pack_params = (str(w*h)+'f',) + (0,)*w*h
    i = gmic.GmicImage(struct.pack(*struct_pack_params), w, h, d, s, shared=False)
    # Divide original size by 2 and check pixels stability
    gmic.run("{} print".format(command_to_apply), i)
    outerr = capfd.readouterr()
    w = w/2
    h = h/2
    assert_get_proper_print_regex(w, h, search_str=outerr.err)
    assert_gmic_image_is_filled_with(i, w, h, d, s, 0)
    # Divide original size by 4 and check pixels stability
    gmic.run("{} print".format(command_to_apply), i)
    outerr = capfd.readouterr()
    w = w/2
    h = h/2
    assert_get_proper_print_regex(w, h, search_str=outerr.err)
    assert_gmic_image_is_filled_with(i, w, h, d, s, 0)
    # Divide original size by 16 (now twice by 2) and check pixels stability
    gmic.run("{} {} print".format(command_to_apply, command_to_apply), i)
    outerr = capfd.readouterr()
    w = w/4
    h = h/4
    assert_get_proper_print_regex(w, h, search_str=outerr.err)
    assert_gmic_image_is_filled_with(i, w, h, d, s, 0)

def test_gmic_image_readonly_attributes_and_bytes_stability():
    import gmic
    import struct
    w = 60
    h = 80
    float_array = struct.pack(*((str(w*h)+'f',) + (0,)*w*h))

    # Ensuring GmicImage's parameters stability after initialization
    i = gmic.GmicImage(float_array, w, h)
    assert i._width == w
    assert i._height == h
    assert i._depth == 1
    assert i._spectrum == 1
    assert i._is_shared == False
    assert i._data == float_array # First bytes array check
    assert len(i._data) == len(float_array) # Additional bytes array check just in case

    # Ensure GmicImage's parameters stability after a resize operation
    gmic.run("resize 50%,50%", i)
    required_floats = int(w*h/4)
    expected_result_float_array = struct.pack(*((str(required_floats)+'f',) + (0,)*required_floats))
    assert i._width == w/2
    assert i._height == h/2
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
    float_array = struct.pack(*((str(w*h*d*s)+'f',) + (0,)*w*h*d*s))
    i = gmic.GmicImage(float_array, w, h, d, s, shared=True)
    gmic.run("add 1", i)
    required_floats= int(w*h*d*s)
    expected_uniform_pixel_value = 1.0
    expected_result_float_array = struct.pack(*((str(required_floats)+'f',) + (expected_uniform_pixel_value,)*required_floats))
    assert_gmic_image_is_filled_with(i, w, h, d, s, expected_uniform_pixel_value)
    assert i._width == w
    assert i._height == h
    assert i._depth == d
    assert i._spectrum == s
    assert i._is_shared == True
    assert i._data == expected_result_float_array # First bytes array check
    assert len(i._data) == len(expected_result_float_array) # Additional bytes array check just in case

def test_gmic_image_readonly_forbidden_write_attributes():
    import gmic
    import struct
    w = 60
    h = 80
    float_array = struct.pack(*((str(w*h)+'f',) + (0,)*w*h))
    real_attributes = ("_data", "_width", "_height", "_depth", "_spectrum", "_is_shared")

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

def test_gmic_images_list_with_image_names_multiple_add_filter_run():
    import gmic
    import struct
    w = 60
    h = 80
    d = s = 1
    nb_images = 10
    base_pixel_multiplicator = 10.0

    image_names = ["some_image_" + str(i) for i in range(nb_images)]
    untouched_image_names = ["some_image_" + str(i) for i in range(nb_images)]
    images = [gmic.GmicImage(struct.pack(*((str(w*h)+'f',) + (i*base_pixel_multiplicator,)*w*h)), w, h) for i in range(nb_images)]
    # First run adding 1 of value to all pixels in all images
    gmic.run("add 1", images, image_names)
    for c, image in enumerate(images):
        assert_gmic_image_is_filled_with(images[c], w, h, d, s, c*base_pixel_multiplicator+1)
    assert untouched_image_names == image_names

    # Second run adding 2 of value to all pixels in all images
    gmic.run("add 2", images, image_names)
    for c, image in enumerate(images):
        assert_gmic_image_is_filled_with(images[c], w, h, d, s, c*base_pixel_multiplicator+2+1)
    assert untouched_image_names == image_names

def test_gmic_image_attributes_visibility():
    import gmic
    import struct
    a = gmic.GmicImage(struct.pack('1f', 1))
    for required_attribute in ("_width", "_height", "_depth", "_spectrum", "_is_shared", "_data"):
        assert required_attribute in dir(a)

def test_gmic_image_object_and_attribute_types():
    import gmic
    import struct
    a = gmic.GmicImage(struct.pack('1f', 1))
    assert type(a) == gmic.GmicImage
    assert type(a._width) == int
    assert type(a._height) == int
    assert type(a._width) == int
    assert type(a._depth) == int
    assert type(a._spectrum) == int
    assert type(a._is_shared) == bool
    assert type(a._data) == bytes

def test_gmic_run_parameters_fuzzying():
    import gmic
    import struct
    w = 60
    h = 80
    d = s = 1
    # 0 parameters
    with pytest.raises(TypeError):
        gmic.run()

    # 1 correct command
    gmic.run("echo_stdout 'bonsoir'")

    # 1 parameters-depending command without an image or with empty list
    gmic.run("print")
    gmic.run("print", tuple())

    # 1 correct GmicImage, 1 correct command, in wrong order
    with pytest.raises(TypeError, match=r".*argument 1 must be str, not gmic.GmicImage.*"):
        a = gmic.run(gmic.GmicImage(struct.pack('1f', 1.0)), "print")

    # 1 correct GmicImage, 1 correct command, some strange keyword
    with pytest.raises(TypeError, match=r".*hey.*is an invalid keyword argument.*"):
        a = gmic.run("print", gmic.GmicImage(struct.pack('1f', 1.0), hey=3))

    # 1 correct GmicImage, 1 correct command with flipped keywords
    gmic.run(images=gmic.GmicImage(struct.pack('1f', 1.0)), command="print")

    # 1 correct list of GmicImages, 1 correct command with flipped keywords
    gmic.run(images=(gmic.GmicImage(struct.pack('1f', 1.0)), gmic.GmicImage(struct.pack('2f', 1.0, 2.0), 2)), command="add 3")

    # 1 GmicImage, no command
    with pytest.raises(TypeError, match=r".*argument 1 must be str, not gmic.GmicImage.*"):
        gmic.run(gmic.GmicImage(struct.pack('1f', 1.0)))

    # 1 GmicImage, no correct command
    with pytest.raises(Exception, match=r".*Unknown command or filename 'hey'.*"):
        gmic.run(images=gmic.GmicImage(struct.pack('1f', 1.0)), command="hey")

    # 1 non-GmicImage, 1 correct command
    with pytest.raises(TypeError, match=r".*'int' 'images' parameter must be a .*GmicImage.* or .*list.*"):
         gmic.run(images=42, command="print")

    # 1 GmicImage, 1 correct command, one non-tuple/list of image names
    with pytest.raises(TypeError, match=r".* 'image_names' parameter must be a list.*str.*"):
        gmic.run(images=gmic.GmicImage(struct.pack('1f', 1.0)), image_names=3, command="add 4")

    # 1 iterable "list" of GmicImages but not tuple/list (here, a str), 1 correct command
    with pytest.raises(TypeError, match=r".*'str' 'images' parameter must be a .*GmicImage.* or .*list.*"):
        gmic.run(images="some iterable object", command="print")

    # 1 tuple/list of not-only GmicImages, 1 correct command
    with pytest.raises(TypeError, match=r"'str'.*object found at position 1 in 'images' list.*"):
        gmic.run(images=(gmic.GmicImage(struct.pack('1f', 1.0)), "not gmic image"), command="print")

    # 1 tuple/list of GmicImages, 1 correct command
    gmic.run(images=(gmic.GmicImage(struct.pack('1f', 1.0)), gmic.GmicImage(struct.pack('1f', 1.0))), command="print")

    # 1 tuple/list of GmicImages, no command
    with pytest.raises(TypeError, match=r".*Required argument 'command'.*not found.*"):
        gmic.run(images=(gmic.GmicImage(struct.pack('1f', 1.0)), gmic.GmicImage(struct.pack('1f', 1.0))))

    # 1 tuple/list of GmicImages, multiline whitespace-bloated correct command
    # This most probably requires compilation with libgmic>=2.8.3 to work
    gmic.run(images=(gmic.GmicImage(struct.pack('1f', 1.0)), gmic.GmicImage(struct.pack('1f', 1.0))), command=" \n\n\r\r  print   \n\r   \t print   \n\n\r\t\t    print    \n")

    two_images = (gmic.GmicImage(struct.pack('1f', 1.0)), gmic.GmicImage(struct.pack('1f', 1.0)))
    original_two_images = (gmic.GmicImage(struct.pack('1f', 1.0)), gmic.GmicImage(struct.pack('1f', 1.0)))
    two_image_names = ("a", "b")
    original_two_image_names = ("a", "b")
    # 1 tuple/list of correct length string image_names, correct images, 1 correct command
    gmic.run(images=two_images, images_names=two_images, command="print")
    # 1 tuple/list of correct length string image_names, no images at all, 1 correct command
    gmic.run(image_names=two_image_names, command="print")
    # 1 tuple/list of correct length string image_names, empty images list, 1 correct command
    gmic.run(images=[], image_names=two_image_names, command="print")
    assert len(two_images_names) == 0
    # empty image_names, empty images list, 1 correct command
    gmic.run(images=[], image_names=[], command="print")
    # decreasing size of images
    gmic.run(images=two_images, image_names=[], command="rm[0]")
    assert len(two_images) == 1 and two_images[0] == original_two_images[0]

    # 1 tuple/list of incorrect length string image_names, correct images, 1 correct command
    # 1 tuple/list of incorrect length string image_names, correct images, 1 correct command
    # 1 non-tuple/list image_names, correct images, 1 correct command
    # 1 iterable non-tuple/list image_names, correct images, 1 correct command
    # 1 empty tuple/list image_names, correct images, 1 correct command
    # 1 empty tuple/list image_names, correct images, 1 correct command
    # 1 tuple/list of image_names with not only strings, correct images, 1 correct command
    # 1 tuple/list of image_names with 'bytes' strings, correct images, 1 correct command

def test_gmic_image_rich_compare():
    import gmic
    import struct

    a = gmic.GmicImage(struct.pack('2f', 1.0, 2.0), 2, 1)
    a2 = gmic.GmicImage(struct.pack('2f', 1.0, 2.0), 2, 1)
    a3 = gmic.GmicImage(struct.pack('2f', 1.0, 2.0), 1, 2)
    b = gmic.GmicImage(struct.pack('1f', 3.0))
    b2 = gmic.GmicImage(struct.pack('1f', 3.0))

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
    for operator, representation in zip(['__gt__', '__ge__', '__lt__', '__le__'], ['>', '>=', '<', '<=']):
        assert getattr(b, operator)(b) == NotImplemented

def test_gmic_image_memory_exhaustion_initialization_resilience():
    import gmic
    import struct
    # out of memory
    with pytest.raises(MemoryError):
        gmic.GmicImage(struct.pack('8f', (0.0,)*494949*2000*393938*499449), 494949, 2000, 393938, 499449)

# todo: test GmicImage to GmicImage copy (several times) and deletion of the first GmicImage and independent buffer and other attributes subsistance
