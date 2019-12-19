$PIP3 install dist/gmic*.tar.gz --verbose
$PYTHON3 -m pytest tests/test_gmic_install_and_run.py -vvv -rxXs
$PIP3 uninstall gmic -y
