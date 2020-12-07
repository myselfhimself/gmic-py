#!/bin/bash
# Adapted from https://github.com/pypa/python-manylinux-demo/blob/master/travis/build-wheels.sh
# Add --debug after the executable name to prevent optimization
set -e -x

export OMP_NUM_THREADS=16  # Fix for https://github.com/myselfhimself/gmic-py/issues/47

PYBIN_PREFIX=${PYBIN_PREFIX:-cp3}

# Install a system package required by our library
yum check-update || { echo "yum check-update failed but manylinux build-wheels script will continue" ; }
yum reinstall ca-certificates -y # prevent libcurl CA 77 certificate error
yum install fftw-devel curl-devel openssl-devel nss-softokn-devel libcurl-devel libpng-devel zlib-devel libgomp libtiff-devel libjpeg-devel wget -y || { echo "Fatal yum dependencies install error" ; exit 1; }


cd /io/


# Compile wheels #Choosing only Python 3 executables
for PYBIN in /opt/python/$PYBIN_PREFIX*/bin; do
    # Skip Python35 executables, slated for end of support in september 2020 https://devguide.python.org/#status-of-python-branches
    if [[ $PYBIN == *"cp35"* ]]; then
        continue
    fi
    # skip Python39 making scikitimage error, see https://github.com/myselfhimself/gmic-py/runs/1176958436?check_suite_focus=true
    if [[ $PYBIN == *"cp39"* ]]; then
        continue
    fi

    # home made patching for our scripts
    export PIP3="${PYBIN}/pip"
    export PYTHON3="${PYBIN}/python"

    bash /io/build_tools.bash 1_clean_and_regrab_gmic_src

    "${PYBIN}/pip" install -r /io/dev-requirements.txt  || { echo "Fatal pip requirements download error" ; exit 1; }
    "${PYBIN}/pip" wheel /io/ -w wheelhouse/ -vvv || { echo "Fatal wheel build error" ; exit 1; }
done

find /opt/python -name auditwheel
$PIP3 uninstall auditwheel -y
$PIP3 install git+https://github.com/thomaslima/auditwheel.git@a9092a0e739204866c2cb35550bbf2348aa009bb
# Bundle external shared libraries into the wheels
for whl in wheelhouse/*gmic*$PYBIN_PREFIX*-linux*.whl; do
    which auditwheel
    auditwheel -v repair "$whl" --plat $PLAT -w /io/wheelhouse/  2>&1 | tee -a /io/REPAIRLOG || { echo "Fatal auditwheel repair error" ; exit 1; }
done

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
