Developing, compiling, testing, releasing
=========================================

``gmic-py`` is a C/Python binding of C++ which must be compiled or pre-compiled for any target machines in order to work. Third-party frameworks for writing bindings such as `Pybind11 <https://pybind11.readthedocs.io/en/stable/>`_ or `Pyrex <https://wiki.python.org/moin/Pyrex>`_ have not been used because of the binding's simplicity.

Any Linux / Mac OS / Unix operating system with Python >= 3.6 (possibly less) should be able to compile the binding without any non-standard Python tooling. 32bit architectures are not supported since Q3 2020, in favor of pure x86_64, but the project used to compile well against the former.

TL;DR building `gmic-py` on Linux
##################################################
You can build G'MIC by forcing pip install to build it from a source tarball:

.. code-block:: sh

    pip install gmic --compile

You can build G'MIC from a Git repository clone. For this run the following lines one by one, deciding on your options:

.. code-block:: bash

    git clone https://github.com/myselfhimself/gmic-py --depth=1

    # For Centos / Redhat / Fedora..:
    yum install fftw-devel curl-devel libpng-devel zlib-devel libgomp libtiff-devel libjpeg-devel wget

    # For Ubuntu
    sudo apt-get install libfftw3-dev libcurl4-openssl-dev libpng-dev liblz-dev libgomp1 libtiff-dev libjpeg-dev wget

    # Download libgmic's preassembled source archive (equates to 2 git clone commands + 2-3 make commands..)
    bash build_tools.bash 1_clean_and_regrab_gmic_src

    # For building linux-repaired wheels, using the manylinux docker images, run:
    bash build_tools.bash 33_build_manylinux # to focus on one version, add eg. 'cp36' as a final parameter
    ls wheelhouse/ # here you have .whl files

    # For building just a non-repaired debug .so file the current machine:
    bash build_tools.bash 2b_compile_debug
    ls build/lib* # cd into any directory with a .so file and run python3 in it, to be able to 'import gmic'

    # Same but optmimized non-repaired .so file
    bash build_tools.bash 2_compile
    ls build/lib*


``gmic-py`` development to release lifecycle (overview)
########################################################
In very short, the G'MIC Python binding per-version lifecycle is as follows:
#. grab libgmic's C++ targetted version
#. tune binding code and pytest cases
#. compile and test locally
#. git push with a tag to trigger optimized releases building and sending to `G'MIC's pypi.org project <https://pypi.org/project/gmic/>`_

Go to ```gmic-py`` development to release lifecycle (detailed)`_ for more details on the right tooling to use for each step.

**Note:** Steps 1-3 correspond to the ``bash build_tools.bash 00_all_steps`` command.

Github Actions Continuous integration workflows
###############################################
Looking that the `Github project's Action's tab <https://github.com/myselfhimself/gmic-py/actions>`_ or the `.github/workflows <https://github.com/myselfhimself/gmic-py/tree/master/.github/workflows>`_ files, you will notice the following discting workflows:

* Linux debug (the fastest to yield a result)
* MacOS optimized
* Manylinux optimized
* Manylinux optimized, on Git tag push optimized with release (to pypi.org)
* MacOS optimized on Git tag push with release (to pypi.org)

All of them leverage ``build_tools.bash`` and show the needed package for each OS.


``build_tools.bash`` - a developer's Swiss army knife
######################################################
Located in the Git repository's root, `build_tools.bash <https://github.com/myselfhimself/gmic-py/blob/master/build_tools.bash>`_ is used for developing, building and releasing ``gmic-py``.

Before running `build_tools.bash`, you should install the developer requirements first:

.. code-block:: sh

    pip install -r dev-requirements.txt

Then, a running the former script without parameters or with ``--help`` shows the targeted G'MIC version and the available commands.

Centralized version for development and continuous-integration-based releasing
******************************************************************************

The targeted G'MIC version is the available version of G'MIC (according to its `source archives <https://gmic.eu/files/source/>`_ and `pre-releases <https://gmic.eu/files/prerelease/>`_) for which we are developing a binding and preparing a release. It is stored in the ``VERSION`` file (add no trailing character after the version number there!) for use by build_tools.bash, setup.py the continuous integration scripts.

Calling build_tools.bash
*************************

To call any command just append its name as a first parameter:

.. code-block:: sh

    $ bash build_tools.bash <the command name>
    $ # For example:
    $ bash build_tools.bash1_clean_and_regrab_gmic_src # Will grab the libgmic C++ code

Rapid sub-commands overview and explanations
*********************************************

Exhaustive commands documentation will not be covered hereafter. In order to understand them, you should look at their implementations within the bash script and their use within the `.github/worfklows/ <https://github.com/myselfhimself/gmic-py/tree/master/.github/workflows>`_ Github Action continuous integration recipes. In it, one function equates to one command.

* ``00_all_steps``: Use this if you are a beginner with ``build_tools.bash`` and have time on a Linux machine with a Python virtual environment, it will grab G'MIC's C++ source, compile, test and bundle it without making any release. More experienced developer in the project will likely run single steps only. This can also be run from a Docker image, `although the related Dockerfile now only survives in Git history <https://github.com/myselfhimself/gmic-py/blob/fc12cb74f4b02fbfd83e9e9fba44ba7a4cee0d93/Dockerfile>_` because it is used very rarely.
* ``1_clean_and_regrab_gmic_src``: download libgmic's C++ code into the src/ directory (which is emptied beforehand)
* ``11_send_to_pypi``: send built wheels (``.whl``) to pypi.org using twine
* ``2_compile``: compile with optimization (long). On Linux a ``.so`` file is generated in the build/ directory.
* ``2b_compile_debug``: compile without optimization (fast) and with debug symbols.
* ``20_reformat_all``: reformat both Python and C code (note this is not done after compile time in ``manylinux`` to avoid crashes). You usually run this by hand before doing a Git commit.
* ``21_check_c_style``: using `clang-format <https://clang.llvm.org/docs/ClangFormat.html>`_.
* ``22_reformat_c_style``: using ``clang-format``.
* ``23i_install_black_python_formatter``: installed a locked version of the `black <https://black.readthedocs.io/en/stable/>`_ Python formatter and checker.
* ``23_check_python_style``: using ``black``.
* ``24_reformat_python_style``: using ``black``.
* ``33_build_manylinux``: build ``gmic-py`` with optimized compiling using the PEP 571 standard for old Linux distributions. This technique nicknamed `manylinux <https://github.com/pypa/manylinux>`_ ships with a Docker image we use on Github Actions. Rarely run locally because it is super long, but this is safe as it is dockerized. Check for your built wheels in the `wheels/` directory.
* ``3_test_compiled_so``: runs pytest cases from ``tests/`` onto your ``build/lib*`` shared ``gmic-py`` library.
* ``3b_test_compiled_so_no_numpy``: similar by omitting the Numpy-support test suite.
* ``31_test_compiled_so_filters_io``: very long experimental test suite with G'MIC ``gmic`` cli command vs ``gmic-py`` module output images result comparison.
* ``4_build_wheel``: build a .whl wheel without embedding external shared libraries (ie. doing a "repair" step as needed on Linuxes, but not on MacOS or Windows). When run, head over to the `build/dist*` directory.
* ``5_test_wheel``: runs pytest cases over the last built wheel.


Recommended compilers
#####################

For proper `OpenMP <https://www.openmp.org/>`_ support - which is highly recommended, our build bots use GCC for Linux (CLang should work) and CLang version 6 (not newer) on MacOS.

For the upcoming Windows support, MSYS2 - mimicking the UNIX standards - will be the envisioned environment, instead of MSVC. The former compiler works already best with G'MIC (C++).

Library requirements
#####################
``gmic-py`` embeds `libgmic C++ library <https://gmic.eu/libgmic.shtml>`_ and has the same library needs as the latter. Namely zlib and libpng, optionally libfftw3, libjpeg, libtiff, OpenMP. ``gmic-py``'s `setup.py file <https://github.com/myselfhimself/gmic-py/blob/master/setup.py>`_ shows the use of the Unix-compatible `pkgconfig <https://pypi.org/project/pkgconfig/>`_ module, for available libraries detection and toggling in order to run a smooth compilation with you having to tune compile flags at all.

Note that our releases are all built against: zlib, libpng, libopenmp, libtiff, libjpeg, similarly to libgmic releases. Libgmic IS embedded inside the ``gmic-py`` binding.

Optimized vs. debugging
########################
For testing and daily development, ``gmic-py`` can be compiled faster with no optimization and with debug symbols attached. This is down through a hackish ``--debug`` flag.
This is what is run through

From ``setup.py``:

.. code-block:: python

    debug_enabled = "--debug" in sys.argv

For releases, an optimized build is generated, just by omitting the ``--debug`` flag.

For debugging segfaults or other situations, you can run `gdb python` and explore with the gdb command line.
You can also use CLion (or any C++ editor), load the C source and Python script of your own using the `gmic` module, run your Python script in Debug mode or with some blocking `input()` or other pure-python breakpoing for example, and `attach with your C++ IDE to the latest Python process run <https://www.jetbrains.com/help/clion/attaching-to-local-process.html>`_. Here is a `similar very barebone way of debugging with IPython and lldb (or gdb) <http://johntfoster.github.io/posts/debugging-cc%2B%2B-libraries-called-by-python.html>`_.

On the fly compiling with pip
##############################

You can compile automatically through a ``pip`` which will run the ``setup.py`` compiling steps for you,
it will download ``gmic-py``'s source from its most stable origin: pypi.org.

.. code-block:: sh

    pip install --no-binary gmic

Compiling from a git clone
###########################
Compiling locally from a Git clone is usually done with GCC/CLang and gets inspiration from libgmic's own Makefile. There are no special tricks, but Python tools are used best instead of direct compiler calling.

.. code-block:: sh

    setup.py build # will need a pip install pkgconfig first

Which is done by ``build_tools.bash 2_compile`` or ``2b_compile_debug`` variant as well.

Though you will libgmic's source first. See the next section instead for doing first things first.

``gmic-py`` development to release lifecycle (detailed)
#######################################################
1. once for all, install developer's requirements in a project own virtual environment:

.. code-block:: sh

    pip install -r dev-requirements.txt

2. change the targetted G'MIC version number (we follow libgmic's versioning) in VERSION. ``build_tools.bash``, ``setup.py`` and the Github Actions workflow files will all rely on this central piece of data!

.. code-block:: sh

    echo "2.9.1" > VERSION

**Note:** this version can be overriden on a per-command basis for ``build_tools.bash`` by setting the ``GMIC_VERSION`` environment variable. Read ``build_tools.bash`` code for details.

3. grab the related libgmic C++ source

.. code-block:: sh

    bash build_tools.bash 1_clean_and_regrab_gmic_src

4. edit ``gmicpy.cpp`` ``gmicpy.h`` ``setup.py`` the pytest ``tests/``
5. edit the documentation in ``docs/`` (it gets deployed to readthedocs.io on each Git push)
6. rebuild documentation for previewing:

.. code-block:: sh

    pip install sphinx # one time only
    cd docs/; make html

7. compile in debug mode

.. code-block:: sh

    bash build_tools.bash 2b_compile_debug

8. run few or all unit tests locally

.. code-block:: sh

    bash build_tools.bash 3_test_compiled_so # for all tests
    bash build_tools.bash 3b_test_compiled_so_no_numpy # for all tests, except numpy ones
    bash build_tools.bash 3b_test_compiled_so_no_numpy openmp # all tests the name of which matches the *openmp* wildcard

9. hand test interactively (outside any Python virtual environment, or using an environment with `gmic` uninstalled)

.. code-block:: sh

    cd build/lib.linux-x86_64-3.6/
    ls # shows gmic.cpython-36m-x86_64-linux-gnu.so
    python3
    # import gmic
    # gmic.run("sp earth") # etc

10. check linked shared libraries

.. code-block:: sh

    cd build/lib.linux-x86_64-3.6/
    ldd gmic.cpython-36m-x86_64-linux-gnu.so

11. Git push without any tag to trigger Github Actions for Mac OS and Linux debug and optimized builds, as well as readthedocs.io documentation building

.. code-block:: sh

    git push # (origin master) or any other Github branch

12. set a Git tag and Git push to trigger the former Github Actions + identical ones optimized with pypi.org release wheels upload

.. code-block:: sh

    git tag -a v2.9.1 # In this project, the tag must start with v for releasing
    git push # origin master or any other Github branch

13. look at `pypi.org's gmic module released contents <https://pypi.org/project/gmic/>`_
14. test online releases by hand (in a Python environment without gmic installed)

.. code-block:: sh

    pip install gmic # or gmic==2.9.1 in our case
    python3
    # import gmic
    # gmic.run("sp earth") # etc
    py.test tests/
