import pytest

FLOAT_SIZE_IN_BYTES = 4

def test_import_gmic():
    import gmic

def test_catch_exceptions():
    import gmic
    try:
        gmic.run('a badly formatted command')
    except Exception as e:
        # For now, all C++ exceptions must be transformed into a SystemError
        assert type(e) == SystemError
        assert len(str(e)) > 0

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

def test_run_gmic_cli_helloworld(capfd):
    import gmic
    # Using pytest stderr capture per https://docs.pytest.org/en/latest/capture.html#accessing-captured-output-from-a-test-function
    gmic.run('echo_stdout "hello world"')
    outerr = capfd.readouterr()
    assert "hello world\n" == outerr.out

def test_run_gmic_cli_simple_3pixels_png_output():
    import gmic
    import pathlib
    png_filename = "a.png"
    gmic.run('input "(0,128,255)" output ' + png_filename)
    a_png = pathlib.Path(png_filename)
    # Ensure generated png file exists and is non empty
    assert a_png.exists()
    assert a_png.stat().st_size > 0
    a_png.unlink()


def test_run_gmic_cli_simple_demo_png_output_and_input():
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


def test_run_gmic_cli_simple_3pixels_bmp_output():
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
    with pytest.raises(TypeError) as excinfo:
        # This used to segfault / fail with core dump
        i = gmic.GmicImage(None, 1, 3)

    with pytest.raises(TypeError) as excinfo:
        # This used to segfault / fail with core dump
        a = gmic.GmicImage(struct.pack('8f', 1, 3, 5, 7, 2, 6, 10, 14), 4, 2, 1, 1)
        a('wrong', 'parameters')

    # # Testing default parameters + 1 keyword
    # c = gmic.GmicImage(struct.pack('8f', 1, 3, 5, 7, 2, 6, 10, 14), shared=True)
    # assert "1" == repr(c)
    # assert re.compile(r"<gmic.GmicImage object at 0x[a-f0-9]+ with _data address at 0x[0-9a-z]+, w=1 h=1 d=1 s=1 shared=1>").match(repr(c))

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

def assert_get_proper_print_regex(w,h,scale_divide_factor,search_str):
    import re
    import time
    assert re.compile(r"size = \({},{},1,1\) \[{} b of floats\](.*)\n(.*)\n(.*)min = 0".format(int(w/scale_divide_factor),int(h/scale_divide_factor),int(w*h*FLOAT_SIZE_IN_BYTES/scale_divide_factor)), flags=re.MULTILINE).search(search_str) is not None

def test_gmic_image_generation_and_gmic_multiple_resize_run(capfd):
    import gmic
    import struct
    import re
    w = 4
    h = 4
    command_to_apply = "blur 0" #resize 50%,50%
    struct_pack_params = (str(w*h)+'f',) + (0,)*w*h
    i = gmic.GmicImage(struct.pack(*struct_pack_params), w, h, 1, 1, shared=False)
    gmic.run("{} print".format(command_to_apply), i)
    outerr = capfd.readouterr()
    assert_get_proper_print_regex(w, h, scale_divide_factor=1, search_str=outerr.err)
    # This second run should be idempotent in terms of resulting image size.. but if fails for now :-/
    i = gmic.GmicImage(struct.pack(*struct_pack_params), w, h, 1, 1, shared=False)
    outerr = capfd.readouterr()
    gmic.run("{} print".format(command_to_apply), i)
    assert_get_proper_print_regex(w, h, scale_divide_factor=1, search_str=outerr.err)
    # Multiple inline resizes
    outerr = capfd.readouterr()
    gmic.run("{} {} print".format(command_to_apply, command_to_apply), i)
    assert_get_proper_print_regex(w, h, scale_divide_factor=16, search_str=outerr.err)

# todo: test with an empty input image list

# todo: test output pythonized objects (ex: 3 pixels raw image buffer)
