# TL;DR ? Just run bash build_tools.bash [--help]

BLACK_FORMATTER_VERSION=20.8b1
PYTHON3=${PYTHON3:-python3}
PIP3=${PIP3:-pip3}
PYTHON_VERSION=$($PYTHON3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)

WIN_DLL_DIR="win_dll" # Directory where gmic-py dependents .dll files will be stored

# Detect if Python is a debug build, per https://stackoverflow.com/a/647312/420684
# Useful for testing leaks within the compiled .so library
if python -c "import sys; sys.exit(int(hasattr(sys, 'gettotalrefcount')))"; then
  PYTHON_DEBUG=
else
  PYTHON_DEBUG="y"
fi

# Choose web browser executable (Linux or MacOS)
BROWSER=xdg-open
if ! command -v xdg-open &> /dev/null
then
    BROWSER=open
fi

# Guess target G'MIC version from VERSION file's contents
if [ -f "VERSION" ]; then
    FILE_BASED_GMIC_VERSION=$(cat VERSION)
    GMIC_SRC_VERSION=$(cat VERSION | grep -oE "[0-9]\.[0-9]\.[0-9][a-z]?(_pre(release)?(0-9+)?)?")
fi
GMIC_VERSION=${GMIC_VERSION:-$GMIC_SRC_VERSION}
GMIC_PY_PACKAGE_VERSION=${FILE_BASED_GMIC_VERSION:-$GMIC_VERSION}
if [ -z "$GMIC_VERSION" ]; then
    echo "You must set some target G'MIC version in the VERSION file or by setting the GMIC_VERSION environment variable."
    exit 1
fi

[[ "$GHA_QUIET" == "1" ]] || echo "🐯 Targeting G'MIC $GMIC_VERSION (gmic.eu) as package $GMIC_PY_PACKAGE_VERSION🐯"

export OMP_NUM_THREADS=16  # Fix for https://github.com/myselfhimself/gmic-py/issues/47

function __get_src_version () {
    echo $GMIC_VERSION
}

function __get_py_package_version () {
    echo $GMIC_PY_PACKAGE_VERSION
}


function 00_all_steps () {
    # See related but defunct Dockerfile at https://github.com/myselfhimself/gmic-py/blob/fc12cb74f4b02fbfd83e9e9fba44ba7a4cee0d93/Dockerfile
    21_check_c_style && 23_check_python_style && 2_compile && 3_test_compiled_so && 4_build_wheel && 5_test_wheel && 6_build_sdist && 7_test_sdist
    echo "This is the final file tree:"
    find .
}

function 01_reload_gmic_env () {
    4_build_wheel && pip uninstall -y gmic && pip install $(ls -rt dist/*.whl | tail -1)
}

function 10a_make_version_tag () {
    echo "This will create tag v$GMIC_PY_PACKAGE_VERSION"
    echo "Ctrl-C here to skip creation. Enter anything to continue and add a compulsory tag message."
    read ii
    git tag -a v$GMIC_PY_PACKAGE_VERSION
    git tag -l
    echo "Push tag now ? (Ctrl + C / Enter)"
    read ii
    git push origin v$GMIC_PY_PACKAGE_VERSION
}

function 10b_delete_version_tag () {
    if ! [[ -z "$(git tag -l | grep -o v$GMIC_PY_PACKAGE_VERSION )" ]]; then
        git tag -d v$GMIC_PY_PACKAGE_VERSION
	echo Deleted tag v$GMIC_PY_PACKAGE_VERSION locally
    fi
    echo "Delete tag online too? (Ctrl+C / Enter)"
    read ii
    git push origin :v$GMIC_PY_PACKAGE_VERSION
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

# Now replaced by git submodule, kept for legacy
function 1_clean_and_regrab_gmic_src () {
    set -x
    GMIC_ARCHIVE_GLOB=gmic_${GMIC_VERSION}.tar.gz
    # GMIC_ARCHIVE_GLOB=gmic_${GMIC_VERSION}*.tar.gz
    if [[ $GMIC_VERSION == *"pre"* ]]; then
        GMIC_URL=https://gmic.eu/files/prerelease/gmic_${GMIC_VERSION}.tar.gz
    else
        GMIC_URL=https://gmic.eu/files/source/gmic_${GMIC_VERSION}.tar.gz
    fi

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

function 2_compile () {
    set -x

    $PIP3 install -r dev-requirements.txt || { echo "Fatal pip install of dev-requirements.txt error" ; exit 1; }
    $PYTHON3 setup.py build 2>&1 || { echo "Fatal setup.py build error" ; exit 1; }
    set +x
}

function 2b_compile_debug () {
    set -x

    $PIP3 install -r dev-requirements.txt || { echo "Fatal pip install of dev-requirements.txt error" ; exit 1; }
    $PYTHON3 setup.py --verbose build --debug 2>&1 || { echo "Fatal setup.py build error" ; exit 1; }
    set +x
}

function 20_reformat_all () {
    # for daily developer use
    22_reformat_c_style
    24_reformat_python_style
}

function 21_check_c_style () {
    [ -x "$(command -v clang-format)" ] || { echo "Install clang-format for C/C++ formatting check" ; exit 1; }
    clang-format gmicpy.cpp > gmicpy.cpp_formatted
    clang-format gmicpy.h > gmicpy.h_formatted
    diff gmicpy.cpp gmicpy.cpp_formatted
    diff gmicpy.h gmicpy.h_formatted
    rm gmicpy.cpp_formatted gmicpy.h_formatted
}

function 22_reformat_c_style () {
    [ -x "$(command -v clang-format)" ] || { echo "Install clang-format for C/C++ reformatting" ; exit 1; }
    clang-format -i gmicpy.cpp && clang-format -i gmicpy.h && echo 'C/C++ formatting with clang-format ✔️'
}

function 23i_install_black_python_formatter () {
    python -c "import black" &>/dev/null || pip install black==$BLACK_FORMATTER_VERSION
}

function 23_check_python_style () {
    23i_install_black_python_formatter
    black --version
    black --check setup.py tests/ examples/
}

function 24_reformat_python_style () {
    23i_install_black_python_formatter
    black setup.py tests/ examples/ && echo 'Python formatting using black ✔️'
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
    set -x
    # Example usage: <this_script.bash> 3_test_compiled_so my_pytest_expr ====> pytest <the pytest file> -k my_pytest_expr
    # Example usage: <this_script.bash> 3_test_compiled_so my_pytest_expr -x --pdb ====> pytest <the pytest file> -k my_pytest_expr -x --pdb
    PYTEST_EXPRESSION_PARAM=
    if ! [ -z "$1" ]; then
        PYTEST_EXPRESSION_PARAM="-k ${@:1}"
    fi

    # No python path must be set for the case 5_test_wheel
    # Otherwise add the path of directory containing .so (debugging or optimized version)
    if [ -z "$TEST_WHEEL" ]; then
	pip uninstall gmic -y
        if ! [ -z "$PYTHON_DEBUG" ]; then
            export PYTHONPATH=$(readlink -f ./build/lib*$PYTHON_VERSION*debug*/)
        else
            export PYTHONPATH=$(readlink -f ./build/lib*$PYTHON_VERSION/)
        fi
    else
	export PYTHONPATH=""
    fi
    $PYTHON3 -c "import gmic; print(gmic.__spec__)"
    ls -l $PYTHONPATH

    TEST_FILES="${TEST_FILES:-tests/test_gmic_py.py tests/test_gmic_numpy.py tests/test_gmic_numpy_toolkits.py tests/test_gmic_py_memfreeing.py}"

    REQUIREMENTS="-r dev-requirements.txt  -r test-requirements.txt"
    if ! [ -z "$MSYSTEM" ]; then #windows / msys2 related
        REQUIREMENTS="-r dev-requirements.txt  -r test-requirements-win.txt"
    fi
    #TEST_FILES="${TEST_FILES:-tests/test_gmic_py_memfreeing.py}"
    FAILED_SUITES=0
    $PIP3 install $REQUIREMENTS; pwd; ls; 

    for TEST_FILE in $TEST_FILES; do
        $PYTHON3 -m pytest $TEST_FILE $PYTEST_EXPRESSION_PARAM -vvv -rxX || { echo "Fatal error while running pytest suite $TEST_FILE" ; FAILED_SUITES=$((FAILED_SUITES+1)) ; }
    done
    cd ../..
    if [ "$FAILED_SUITES" -gt "0" ]; then
        echo "Fatal error: $FAILED_SUITES pytest suites failed. Exiting.";
       	exit 1;
    else
        return 0;
    fi
    export PYTHONPATH=""
    set +x
}

function 3b_test_compiled_so_no_numpy () {
    TEST_FILES="tests/test_gmic_py.py" 3_test_compiled_so
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
        PYTEST_EXPRESSION_PARAM="-k $1"
        PYTEST_NB_THREADS=
    else
        PYTEST_EXPRESSION_PARAM=
        PYTEST_NB_THREADS="-n 4"
    fi
    find ~/.config/gmic
    $PIP3 uninstall gmic -y; cd ./build/lib*$PYTHON_VERSION*/ ; export PYTHONPATH=`pwd` ; $PIP3 install -r ../../{test,dev}-requirements.txt ; pwd; ls; $PYTHON3 -m pytest ../../tests/test_gmic_py_filters_io.py $PYTEST_EXPRESSION_PARAM $PYTEST_NB_THREADS -vvv -rxXs || { echo "Fatal error while running pytests" ; exit 1 ; } ; cd ../..
    find ~/.config/gmic
}    

function 4_build_wheel () {
    rm -rf .egg-info # https://stackoverflow.com/questions/18085571/pip-install-error-setup-script-specifies-an-absolute-path#comment94579634_39198529

    $PIP3 install wheel || { echo "Fatal wheel package install error" ; exit 1 ; }
    $PYTHON3 setup.py bdist_wheel || { echo "Fatal wheel build error" ; exit 1 ; }

    if [ -z "WHEEL_REPAIR" ]; then
        echo "Not doing any auditwheel repair step here, development environment :)"
    elif ! [ -z "$MSYSTEM" ]; then
	echo "about to repair wheel for windows using wheel_repair.py"
	echo ".dll ldd for info, before repair attempt:"
	ldd build/lib.*/gmic-*.dll
	#4c_copy_windows_dlls_for_repair
	pip install -r dev-requirements-win.txt
        LAST_WHEEL=`ls -Art dist/*.whl | tail -n 1`
	$PYTHON3 wheel_repair.py $LAST_WHEEL -d "D:/a/_temp/msys/msys64/mingw64/bin/"
    fi
}

function 4b_build_windows_portable_wheel () {
   WHEEL_REPAIR=1 4_build_wheel
}


function 4c_copy_windows_dlls_for_repair () {
    set -x
    # Inspired by gmic CLI Windows build instructions at https://gmic.eu/download.html#windows
    mkdir -p $WIN_DLL_DIR
    DLLS_TO_COPY=$(ldd build/lib.*/gmic-*.dll | grep -Eio "/mingw64/bin/.*.dll" | paste -s -d' ')
    echo "DLLs to be copied into wheel are: $DLLS_TO_COPY"
    cp $DLLS_TO_COPY $WIN_DLL_DIR || { echo "Could not copy dlls to $WIN_DLL_DIR" ; exit 1 ; }
    find $WIN_DLL_DIR
    set +x
}

function 5_test_wheel () {
    set -x
    export PYTHONPATH=""
    $PIP3 install `ls -Art dist/*.whl | tail -n 1` --no-cache-dir
    TEST_WHEEL=1 3_test_compiled_so ${@:1}
    $PIP3 uninstall gmic -y
    set +x
}

function 5b_test_wheel_dlls_repaired () {
    set -x
    LAST_WHEEL=`ls -Art wheelhouse/*.whl | tail -n 1`
    unzip -l $LAST_WHEEL
    PACKED_DLLS_FOUND=`unzip -l $LAST_WHEEL | grep -Eio "[a-z].*\.dll" | grep -v gmic-cpython | paste -s -d' '`
    if [ -z "$PACKED_DLLS_FOUND" ]; then
        echo "Error: non-gmic DLLs not found in wheel."; exit 1
    else
        echo "Found non-gmic DLLs in wheel: $PACKED_DLLS_FOUND"
    fi

    export PYTHONPATH=""
    $PIP3 uninstall gmic -y
    $PIP3 install $LAST_WHEEL --no-cache-dir
    TEST_WHEEL=1 3_test_compiled_so ${@:1}
    $PIP3 uninstall gmic -y
 
    set +x
}

function 6_make_full_doc () {
    # Use this for generating doc when gmicpy.cpp has been changed
    20_reformat_all && 2b_compile_debug && 4_build_wheel && pip uninstall -y gmic && pip install `ls -Art dist/*.whl | tail -n 1` && cd docs && pip install -r requirements.txt && touch *.rst && make html && $BROWSER _build/html/index.html && cd ..
}

function 6b_make_doc_without_c_recompilation () {
    if ! [ -z "$1" ]; then
        FILES_TO_TOUCH="$1"
    else
        FILES_TO_TOUCH=
    fi
    pip uninstall -y gmic && pip install `ls -Art dist/*.whl | tail -n 1` && cd docs && pip install -r requirements.txt && touch $FILES_TO_TOUCH && make html && $BROWSER _build/html/index.html && cd ..
}

function --help () {
    # declares an array with the emojis we want to support
    EMOJIS=(🍇 🍈 🍉 🍊 🍋 🍌 🍍 🥭 🍎 🍏 🍐 🍑 🍒 🍓 🥝 🍅 🥥 🥑 🍆 🥔 🥕 🌽 🌶 🥒 🥬 🥦)
    
    # selects a random element from the EMOJIS set

    echo "☀️  G'MIC Python Binding Development & Build Tools ☀️ "
    echo "Usage: $0 function_name"
    echo "Functions:"
    for a in $(grep "^function" $0 | cut -d' ' -f2) ; do
        SELECTED_EMOJI=${EMOJIS[$RANDOM % ${#EMOJIS[@]}]};
        echo $SELECTED_EMOJI $a
    done
}

if [ $# -gt 0 ]; then
    # Call the first arg<->function name, inject to it the 2 and more parameters
    $"$1" "${@:2}"
else
    --help
fi
