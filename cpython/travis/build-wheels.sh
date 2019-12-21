#!/bin/bash
# Adapted from https://github.com/pypa/python-manylinux-demo/blob/master/travis/build-wheels.sh
set -e -x

# Install a system package required by our library
yum check-update
yum install fftw-devel curl-devel libpng-devel zlib-devel libgomp wget -y

cd /io/


# Compile wheels #Choosing only Python 3 executables
for PYBIN in /opt/python/cp3*/bin; do
    # home made patching for our scripts
    export PIP3="${PYBIN}/pip"
    export PYTHON3="${PYBIN}/python"

    bash /io/1_clean_and_regrab_gmic_src.sh

    "${PYBIN}/pip" install -r /io/dev-requirements.txt
    "${PYBIN}/pip" wheel /io/ -w wheelhouse/
done

find /opt/python -name auditwheel
# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    which auditwheel
    auditwheel repair "$whl" --plat $PLAT -w /io/wheelhouse/
done

# Install packages and test
for PYBIN in /opt/python/cp3*/bin; do
    "${PYBIN}/pip" install gmic --no-index -f /io/wheelhouse
    "${PYBIN}/python" -m pytest tests/test_gmic_install_and_run.py -vvv -rxXs
done
