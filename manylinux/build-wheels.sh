#!/bin/bash
# Adapted from https://github.com/pypa/python-manylinux-demo/blob/master/travis/build-wheels.sh
# Add --debug after the executable name to prevent optimization
set -e -x

export OMP_NUM_THREADS=16  # Fix for https://github.com/myselfhimself/gmic-py/issues/47

PYBIN_PREFIX=${PYBIN_PREFIX:-cp3}

# Install a system package required by our library
yum check-update || { echo "yum check-update failed but manylinux build-wheels script will continue" ; }
yum install fftw-devel curl-devel libpng-devel zlib-devel libgomp wget -y || { echo "Fatal yum dependencies install error" ; exit 1; }

# # Install slightly newer libpng12 includes if too old, to avoid c++11 problem listed here: https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=676157
# if [ "1.2.51" \> "$(yum info libpng-devel | grep Version | cut -d':' -f2 | awk '{print $1}' | uniq)" ]; then
#     cd /tmp/
#     ls -l
#     curl -o libpng-1.2.51.tar.gz -s "https://master.dl.sourceforge.net/project/libpng/libpng12/older-releases/1.2.51/libpng-1.2.51.tar.gz?viasf=1"
#     ls -l
#     tar xzvf libpng*
#     rm libpng*.tar.gz
#     mv libpng* libpng12
#     rm -rf /usr/include/libpng12
#     mv libpng12 /usr/include/
# fi

# Allow building Pillow from source if needed (on old Centos builds)
# Requirements inspired from Pillow's official Docker recipes at https://github.com/python-pillow/docker-images/blob/master/centos-6-amd64/Dockerfile
yum install ghostscript libtiff-devel libjpeg-devel zlib-devel freetype-devel lcms2-devel libwebp-devel openjpeg2-devel tkinter tcl-devel tk-devel libffi-devel -y

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
# Bundle external shared libraries into the wheels
for whl in wheelhouse/*gmic*$PYBIN_PREFIX*$PLAT*.whl; do
    which auditwheel
    auditwheel repair "$whl" --plat $PLAT -w /io/wheelhouse/  || { echo "Fatal auditwheel repair error" ; exit 1; }
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
