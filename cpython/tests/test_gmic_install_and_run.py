import pytest
import platform
import os

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
    arch = platform.architecture()
    plat = os.environ.get('plat', '')
    if arch[0] != '64bit' or plat == 'manylinux1_x86_64':
        pytest.skip('skipping openmp testing for 32bits or old manylinux1_x86_64 architecture :) current architecture: {}; current platform (env: "plat"): {}'.format(arch, plat))
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
        # This fail used to be an xfail :) Just more compulsory now :)
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

def test_gmic_image_construct_and_destroy():
    import re
    import gmic
    i = gmic.GmicImage(300, 500, 0, 3)
    assert re.compile(r"<gmic.GmicImage object at 0x[a-f0-9]+ with _data address 0x[0-9a-z]+, w=300 h=500 d=0 s=3>").match(repr(i))
    print(dir(i))
    i = None
    # gmic.run(buffer, 'print')


# todo: test with an empty input image list

# todo: test output pythonized objects (ex: 3 pixels raw image buffer)
