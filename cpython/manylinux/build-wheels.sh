#!/bin/bash
# Adapted from https://github.com/pypa/python-manylinux-demo/blob/master/travis/build-wheels.sh
set -e -x

# Install a system package required by our library
yum check-update
yum install fftw-devel curl-devel libpng-devel zlib-devel libgomp wget -y || { echo "Fatal yum dependencies install error" ; exit 1; }

# Install slightly newer libpng12 includes if too old, to avoid c++11 problem listed here: https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=676157
if [ "1.2.51" \> "$(yum info libpng-devel | grep Version | cut -d':' -f2)" ]; then
    cd /tmp/
    curl -o libpng-1.2.51.tar.gz -s https://master.dl.sourceforge.net/project/libpng/libpng12/older-releases/1.2.51/libpng-1.2.51.tar.gz
    tar xzvf libpng*
    rm libpng*.tar.gz
    mv libpng* libpng12
    rm -rf /usr/include/libpng12
    mv libpng12 /usr/include/
fi

cd /io/


# Compile wheels #Choosing only Python 3 executables
for PYBIN in /opt/python/cp3*/bin; do
    # home made patching for our scripts
    export PIP3="${PYBIN}/pip"
    export PYTHON3="${PYBIN}/python"

    bash /io/build_tools.bash 1_clean_and_regrab_gmic_src

    "${PYBIN}/pip" install -r /io/dev-requirements.txt  || { echo "Fatal pip requirements download error" ; exit 1; }
    "${PYBIN}/pip" wheel /io/ -w wheelhouse/ -vvv || { echo "Fatal wheel build error" ; exit 1; }
done

find /opt/python -name auditwheel
# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    which auditwheel
    auditwheel repair "$whl" --plat $PLAT -w /io/wheelhouse/  || { echo "Fatal auditwheel repair error" ; exit 1; }
done

# Install packages and test
for PYBIN in /opt/python/cp3*/bin; do
    "${PYBIN}/pip" install gmic --no-index -f /io/wheelhouse || { echo "Fatal wheel install error" ; exit 1; }
    "${PYBIN}/python" -m pytest tests/test_gmic_install_and_run.py -vvv -rxXs || { echo "Fatal pytests suite error" ; exit 1; }
done
