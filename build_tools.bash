# TL;DR ? Just run bash build_tools.bash --help

PYTHON3=${PYTHON3:-python3}
PIP3=${PIP3:-pip3}
PYTHON_VERSION=$($PYTHON3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
GMIC_VERSION=${GMIC_VERSION:-2.9.0}

function 00_all_steps () {
    1_clean_and_regrab_gmic_src && 2_compile && 3_test_compiled_so && 4_build_wheel && 5_test_wheel && 6_build_sdist && 7_test_sdist
    echo "This is the final file tree:"
    find .
}

function 11_send_to_pypi () {
    set -x
    pip install twine
    export TWINE_USERNAME=__token__
    export TWINE_PASSWORD="$TWINE_PASSWORD_GITHUB_SECRET" # See: Github Workflow scripts
    export TWINE_REPOSITORY_URL=https://upload.pypi.org/legacy/
    TWINE=twine
    
    # Do not reupload same-version wheels our source archives
    TWINE_OPTIONS="--skip-existing --verbose"
    
    echo "TWINE UPLOAD STEP: Contents of dist/ and wheelhouse directories are:"
    find dist/
    find *wheel*
    
    # Upload sdist source tar.gz archive if found
    if [ -d "dist/" ]; then
      for a in `ls dist/*.tar.gz`; do
        $TWINE upload $a $TWINE_OPTIONS
      done
    fi
    
    # Upload binary python wheels if found
    if [ -d "wheelhouse/" ]; then
      for a in `ls wheelhouse/* | grep -E 'manylinux|macosx'`; do # Keep /* wildcard for proper relative paths!!
        $TWINE upload $a $TWINE_OPTIONS
      done
    fi
    set +x
}

function 1_clean_and_regrab_gmic_src () {
    set -x
    GMIC_ARCHIVE_GLOB=gmic_${GMIC_VERSION}.tar.gz
    # GMIC_ARCHIVE_GLOB=gmic_${GMIC_VERSION}*.tar.gz
    GMIC_URL=https://gmic.eu/files/source/gmic_${GMIC_VERSION}.tar.gz
    #GMIC_URL=https://gmic.eu/files/prerelease/gmic_prerelease.tar.gz
    rm -rf dist/
    rm -rf src/
    mkdir src -p
    $PIP3 install -r dev-requirements.txt
    $PYTHON3 setup.py clean --all
    if ! [ -f "$GMIC_ARCHIVE_GLOB" ]; then
        wget ${GMIC_URL} -P src/ --no-check-certificate || { echo "Fatal gmic src archive download error" ; exit 1; }
    fi
    tar xzvf src/${GMIC_ARCHIVE_GLOB} -C src/ || { echo "Fatal gmic src archive extracting error" ; exit 1; }
    mv src/gmic*/ src/gmic
    # cd src/gmic

    # rm -rf $(ls | grep -v src)
    # cd src
    # #ls | grep -vE "gmic\.cpp|gmic\.h|gmic_stdlib\.h|CImg\.h" | xargs rm -rf
    # ls
    # cd ../../..
    # pwd
    # echo
    echo "src/ dir now contains fresh gmic source ($GMIC_VERSION):"
    find src/
    set +x
}

function 1b_clean_and_regrab_gmic_src_and_make_cli () {
    1_clean_and_regrab_gmic_src
    cd src/gmic/src
    OPT_LIBS=" -O0 " make OPENCV_CFLAGS='' OPENCV_LIBS="" cli && mv gmic ../../.. && echo "Compiled gmic cli executable now at: $(readlink -f gmic)"
    cd ../../..
}

function 22_docker_run_all_steps () {
    docker build --rm -t testpython3 .
    docker run testpython3
}

function 2_compile () {
    set -x
    $PIP3 install -r dev-requirements.txt || { echo "Fatal pip install of dev-requirements.txt error" ; exit 1; }
    $PYTHON3 setup.py build 2>&1 || { echo "Fatal setup.py build error" ; exit 1; }
    set +x
}

function 33_build_manylinux () {
    # Feel free to preset the following variables before running this script
    # Default values allow for local running on a developer machine :)
    if [ -z "$DOCKER_IMAGE" ]
    then
      DOCKER_IMAGE="quay.io/pypa/manylinux1_x86_64"
    fi
    if [ -z "$PLAT" ]
    then
      PLAT="manylinux1_x86_64"
    fi
    if [ -z "$PRE_CMD" ]
    then
      PRE_CMD=
    fi
    
    docker pull $DOCKER_IMAGE
    docker run --rm -e PLAT=$PLAT -v `pwd`:/io $DOCKER_IMAGE find /io
    docker run --rm -e PLAT=$PLAT -v `pwd`:/io $DOCKER_IMAGE $PRE_CMD /bin/bash /io/manylinux/build-wheels.sh || { echo "Many linux build wheels script failed. Exiting" ; exit 1; }
    ls wheelhouse/
}

function 3_test_compiled_so () {
    # Example usage: <this_script.bash> 3_test_compiled_so my_pytest_expr ====> pytest <the pytest file> -k my_pytest_expr
    PYTEST_EXPRESSION_PARAM=
    if ! [ -z "$1" ]; then
        PYTEST_EXPRESSION_PARAM="-k $1"
    fi
    $PIP3 uninstall gmic -y; cd ./build/lib*$PYTHON_VERSION*/ ; LD_LIBRARY_PATH=.:$LD_LIBRARY_PATH ; $PIP3 install -r ../../dev-requirements.txt ; pwd; ls; $PYTHON3 -m pytest ../../tests/test_gmic_py.py $PYTEST_EXPRESSION_PARAM -vvv -rxXs || { echo "Fatal error while running pytests" ; exit 1 ; } ; cd ../..
}    

function 31_test_compiled_so_filters_io () {
    if ! [ -f ./build/lib*$PYTHON_VERSION*/*.so ]; then
	echo "Run 2_compile step first"; exit 1
    fi
    if ! [ -x "$(command -v gmic)" ]; then
	echo "gmic CLI executable is not in PATH or current directory, compile and increase its visibility first"; exit 1
    fi
    # Example usage: <this_script.bash> 3_test_compiled_so_filters_io
    if [ -d ./build/lib*$PYTHON_VERSION*/test-images ]; then
        rm -rf ./build/lib*$PYTHON_VERSION*/test-images
    fi
    if ! [ -z "$1" ]; then
        PYTEST_EXPRESSION_PARAM="-k test_gmic_filter_io[$1]"
        PYTEST_NB_THREADS=
    else
        PYTEST_EXPRESSION_PARAM=
        PYTEST_NB_THREADS="-n 4"
    fi
    find ~/.config/gmic
    $PIP3 uninstall gmic -y; cd ./build/lib*$PYTHON_VERSION*/ ; LD_LIBRARY_PATH=.:$LD_LIBRARY_PATH ; $PIP3 install -r ../../dev-requirements.txt ; pwd; ls; $PYTHON3 -m pytest ../../tests/test_gmic_py_filters_io.py $PYTEST_EXPRESSION_PARAM $PYTEST_NB_THREADS -vvv -rxXs || { echo "Fatal error while running pytests" ; exit 1 ; } ; cd ../..
    find ~/.config/gmic
}    

function 4_build_wheel () {
    $PIP3 install wheel || { echo "Fatal wheel package install error" ; exit 1 ; }
    $PYTHON3 setup.py bdist_wheel || { echo "Fatal wheel build error" ; exit 1 ; }
    echo "Not doing any auditwheel repair step here, development environment :)"
}

function 5_test_wheel () {
    $PIP3 install dist/gmic*.whl --no-cache-dir
    $PYTHON3 -m pytest tests/test_gmic_py.py -rxXs -vvv
    $PIP3 uninstall gmic -y
}

function --help () {
    echo "Usage: $0 function_name"
    echo "Functions:"
    grep "^function" $0
}

if [ $# -gt 0 ]; then
    # Call the first arg<->function name, inject to it the 2 and more parameters
    $"$1" "${@:2}"
else
    --help
fi
