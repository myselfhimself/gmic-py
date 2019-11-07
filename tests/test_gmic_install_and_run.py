import pytest

def test_install_gmic_py():
    # per https://github.com/jgonggrijp/pip-review/issues/44#issuecomment-277720359
    import subprocess
    import sys
    import os
    exit_code = subprocess.call([sys.executable, '-m', 'pip', 'install', os.environ.get('GMIC_PY_PIP_PKG', 'gmic-py'), '--no-cache-dir'])
    assert exit_code == 0

def test_import_gmic_py():
    import gmic_py

def test_run_gmic_cli_helloworld(capsys):
    import gmic_py
    # Using pytest stderr capture per https://docs.pytest.org/en/latest/capture.html#accessing-captured-output-from-a-test-function
    captured = capsys.readout()
    result = gmic_py.run('v - echo_stdout "hello world"')
    assert "hello world\n" in captured

def test_run_gmic_cli_simple_3pixels_png_output():
    import gmic_py
    import pathlib
    png_filename = "a.png"
    gmic_py.run('input "(0,128,255)" -output ' + png_filename)
    a_png = pathlib.Path(png_filename)
    # Ensure generated png file exists and is non empty
    assert a_png.exists()
    assert a.png.stat().st_size > 0
    a_png.unlink()

# todo: test with an empty input image list

# todo: test output pythonized objects (ex: 3 pixels raw image buffer)

# todo: test exceptions raising

