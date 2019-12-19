$PIP3 install dist/gmic*.whl --no-cache-dir
$PYTHON3 -m pytest tests/test_gmic_install_and_run.py -rxXs -vvv
$PIP3 uninstall gmic -y
