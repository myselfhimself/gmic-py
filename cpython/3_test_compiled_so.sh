pip3 uninstall gmic -y; cd ./build/lib.linux-x86_64-*/ ; pip3 install -r ../../tests/requirements.txt ; pwd; ls; python3 -m pytest ../../tests/test_gmic_install_and_run.py ; cd ../..
