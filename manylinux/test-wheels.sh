#!/bin/bash
# Adapted from https://github.com/pypa/python-manylinux-demo/blob/master/travis/build-wheels.sh
# Add --debug after the executable name to prevent optimization
set -e -x

export OMP_NUM_THREADS=16  # Fix for https://github.com/myselfhimself/gmic-py/issues/47

PYBIN_PREFIX=${PYBIN_PREFIX:-cp3}
cd /io/

# Install packages and test
for PYBIN in /opt/python/$PYBIN_PREFIX*/bin; do
    # Skip Python35 executables, slated for end of support in september 2020 https://devguide.python.org/#status-of-python-branches
    if [[ $PYBIN == *"cp35"* ]]; then
        continue
    fi
    # skip Python39 making scikitimage error, see https://github.com/myselfhimself/gmic-py/runs/1176958436?check_suite_focus=true
    if [[ $PYBIN == *"cp39"* ]]; then
        continue
    fi

    "${PYBIN}/pip" install gmic --no-index -f /io/wheelhouse || { echo "Fatal wheel install error" ; exit 1; }
    # TODO reenable tests for 2.9.1!
    #"${PYBIN}/python" -m pytest tests/test_gmic_py.py tests/test_gmic_numpy.py -vvv -rxXs || { echo "Fatal pytests suite error" ; exit 1; }
    "${PYBIN}/pip" uninstall gmic -y || { echo "Fatal gmic uninstall error" ; exit 1; }
done
