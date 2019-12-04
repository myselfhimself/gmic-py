pip3 install dist/gmic*.tar.gz --verbose
python3 -m pytest tests/test_gmic_install_and_run.py
pip3 uninstall gmic -y
