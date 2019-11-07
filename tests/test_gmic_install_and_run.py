import pytest

def test_install_gmic_py():
    # per https://github.com/jgonggrijp/pip-review/issues/44#issuecomment-277720359
    import subprocess
    import sys
    exit_code = subprocess.call([sys.executable, '-m', 'pip', 'install', 'gmic-py'])
    assert exit_code == 0

def test_import_gmic_py():
    import gmic_py

def test_run_gmic_cli_helloworld(capsys):
    import gmic_py
    # Using pytest stderr capture per https://docs.pytest.org/en/latest/capture.html#accessing-captured-output-from-a-test-function
    captured = capsys.readouterr()
    result = gmic_py.run('echo "hello world"')
    assert "[gmic]-0./ Start G'MIC interpreter." in captured
    assert "hello world" in captured

def test_run_gmic_cli_simple_3pixels_png_output():
    import gmic_py
    import pathlib
    png_filename = "a.png"
    gmic_py.run('input "(1,2,3)" -output ' + png_filename)
    a_png = pathlib.Path(png_filename)
    # Ensure generated png file exists and is non empty
    assert a_png.exists()
    assert a.png.stat().st_size > 0
    a_png.unlink()

# todo: test exceptions raising

