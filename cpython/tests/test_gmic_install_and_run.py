import pytest

def test_import_gmic():
    import gmic

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
    gmic.run('input "(0,128,255)" -output ' + png_filename)
    a_png = pathlib.Path(png_filename)
    # Ensure generated png file exists and is non empty
    assert a_png.exists()
    assert a_png.stat().st_size > 0
    a_png.unlink()


def test_run_gmic_cli_simple_demo_png_output():
    """ Ensure that zlib is properly linked and ensures that either
    the png library used or the 'convert' tool of the imagemagick suite, for saving png"""
    import gmic
    import pathlib
    png_filename = "demo.png"
    gmic.run('testimage2d 512 -output ' + png_filename)
    a_png = pathlib.Path(png_filename)
    # Ensure generated png file exists and is non empty
    assert a_png.exists()
    assert a_png.stat().st_size > 0
    a_png.unlink()


def test_run_gmic_cli_simple_3pixels_bmp_output():
    """ Ensure that the native bmp file output works"""
    import gmic
    import pathlib
    bmp_filename = "a.bmp"
    gmic.run('input "(0,128,255)" -output ' + bmp_filename)
    a_bmp = pathlib.Path(bmp_filename)
    # Ensure generated bmp file exists and is non empty
    assert a_bmp.exists()
    assert a_bmp.stat().st_size > 0
    a_bmp.unlink()




# todo: test with an empty input image list

# todo: test output pythonized objects (ex: 3 pixels raw image buffer)

# todo: test exceptions raising

