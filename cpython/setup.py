"""A setuptools based setup module for the Gmic Python bindings binary module.
"""

from os import path, listdir, environ
import sys
import platform

from setuptools import setup, Extension, find_packages
import pkgconfig


here = path.abspath(path.dirname(__file__))
gmic_src_path = path.abspath('src/gmic/src')

# List of non-standard '-l*' compiler parameters
extra_link_args = []

# List of libs to get include directories and linkable libraries paths from for compiling
pkgconfig_list = ['zlib']

# Macros to toggle (gmic or CImg will do C/C++ #ifdef checks on them, testing mostly only their existence)
# cimg_date and cimg_date are true variables, the value of which is checked in the C/C++ source
define_macros = [('gmic_build', None), ('cimg_date', '""'), ('cimg_time', '""'), ('gmic_is_parallel', None), ('cimg_use_zlib', None)]

# Only require x11 if found
if pkgconfig.exists('x11'):
    define_macros += [('cimg_display', None)]
    pkgconfig_list += ['x11']

# Only require libpng if found
if pkgconfig.exists('libpng'):
    define_macros += [('cimg_use_png', None)]
    pkgconfig_list += ['libpng']

# Only require fftw3 if found (non-2^ size image processing fails without it)
# We do not toggle cimg_use_fftw3, it is buggy
if pkgconfig.exists('fftw3'):
    define_macros += [('cimg_use_fftw3', None)]
    pkgconfig_list += ['fftw3']
    extra_link_args += ['-lfftw3_threads']

# Only compile with OpenCV if exists (nice for the 'camera' G'MIC command :-D )
if pkgconfig.exists('opencv'):
    define_macros += [('cimg_use_opencv', None)]
    pkgconfig_list += ['opencv']


# Disable libcurl only on manylinuxes, because of a buggy audithweel repair constraint
# See https://github.com/pypa/manylinux/issues/411
# On any other platform, use libcurl if installed, else G'MIC falls back nicely to installed curl executable
if 'manylinux' not in environ.get('PLAT','') and pkgconfig.exists('libcurl'):
    define_macros += [('cimg_use_curl', None)]
    pkgconfig_list += ['libcurl']

packages = pkgconfig.parse(" ".join(pkgconfig_list))
libraries = packages['libraries'] + ['pthread'] # removed core-dumping 'gomp' temporarily (for manylinux builds)

library_dirs = packages['library_dirs'] + [here, gmic_src_path]
if sys.platform == 'darwin':
    library_dirs += ['/usr/local/opt/llvm@6/lib']
include_dirs = packages['include_dirs'] + [here, gmic_src_path]
if sys.platform == 'darwin':
    include_dirs += ['/usr/local/opt/llvm@6/include']
debugging_args = ['-O0', '-g'] # Uncomment this for faster compilation with debug symbols and no optimization

extra_compile_args = ['-std=c++11'] + debugging_args
if sys.platform == 'darwin':
    extra_compile_args += ['-fopenmp', '-stdlib=libc++']
    extra_link_args += ['-lomp', '-nodefaultlibs', '-lc++'] #options inspired by https://github.com/explosion/spaCy/blob/master/setup.py
elif sys.platform == 'linux': # Enable openmp for 32bit & 64bit linuxes
    extra_compile_args += ['-fopenmp']
    extra_link_args += ['-lgomp']

print("Define macros:")
print(define_macros)

# Static CPython gmic.so embedding libgmic.so.2
gmic_module = Extension('gmic',
                    include_dirs = include_dirs,
                    libraries = libraries,
                    library_dirs = library_dirs,
                    sources = ['gmicpy.cpp', path.join(gmic_src_path, 'gmic.cpp')],
                    define_macros=define_macros,
                    extra_compile_args = extra_compile_args,
                    extra_link_args = extra_link_args,
                    language='c++')

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Grab the version from the VERSION file, which is also include in MANIFEST.in
# Technique highlighted here: https://packaging.python.org/guides/single-sourcing-package-version/
with open(path.join('.', 'VERSION')) as version_file:
    version = version_file.read().strip()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    # This is the name of your project. The first time you publish this
    # package, this name will be registered for you. It will determine how
    # users can install this project, e.g.:
    #
    # $ pip install sampleproject
    #
    # And where it will live on PyPI: https://pypi.org/project/sampleproject/
    #
    # There are some restrictions on what makes a valid project name
    # specification here:
    # https://packaging.python.org/specifications/core-metadata/#name
    name='gmic',  # Required

    # Versions should comply with PEP 440:
    # https://www.python.org/dev/peps/pep-0440/
    #
    # For a discussion on single-sourcing the version across setup.py and the
    # project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version = version,

    # This is a one-line description or tagline of what your project does. This
    # corresponds to the "Summary" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#summary
    description='Binary Python3 bindings for the G\'MIC C++ image processing library',  # Optional

    # This is an optional longer description of your project that represents
    # the body of text which users will see when they visit PyPI.
    #
    # Often, this is the same as your README, so you can just read it in from
    # that file directly (as we have already done above)
    #
    # This field corresponds to the "Description" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#description-optional
    long_description=long_description,  # Optional

    # Denotes that our long_description is in Markdown; valid values are
    # text/plain, text/x-rst, and text/markdown
    #
    # Optional if long_description is written in reStructuredText (rst) but
    # required for plain-text or Markdown; if unspecified, "applications should
    # attempt to render [the long_description] as text/x-rst; charset=UTF-8 and
    # fall back to text/plain if it is not valid rst" (see link below)
    #
    # This field corresponds to the "Description-Content-Type" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#description-content-type-optional
    long_description_content_type='text/markdown',  # Optional (see note above)

    # This should be a valid link to your project's main homepage.
    #
    # This field corresponds to the "Home-Page" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#home-page-optional
    url='https://github.com/dtschump/gmic-py',  # Optional

    # This should be your name or the name of the organization which owns the
    # project.
    author='David Tschumperlé, Jonathan-David Schröder G\'MIC GREYC IMAGE Team of CNRS, France',  # Optional

    # This should be a valid email address corresponding to the author listed
    # above.
    author_email='David.Tschumperle@ensicaen.fr, jonathan.schroder@gmail.com',  # Optional

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 2 - Pre-Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Artistic Software',

        # Pick your license as you wish
        'License :: OSI Approved :: CEA CNRS Inria Logiciel Libre License, version 2.1 (CeCILL-2.1)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # These classifiers are *not* checked by 'pip install'. See instead
        # 'python_requires' below.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],

    # This field adds keywords for your project which will appear on the
    # project page. What does your project relate to?
    #
    # Note that this is a string of words separated by whitespace, not a list.
    keywords='image processing gmic g\'mic voxel 2d 3d filter',  # Optional

    # When your source code is in a subdirectory under the project root, e.g.
    # `src/`, it is necessary to specify the `package_dir` argument.
    #package_dir={'': ''},  # Optional

    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    #
    # Alternatively, if you just want to distribute a single Python file, use
    # the `py_modules` argument instead as follows, which will expect a file
    # called `my_module.py` to exist:
    #
    #   py_modules=["my_module"],
    #
    #packages=find_packages(where='src'),  # Required
    py_modules=["gmic"],

    # Specify which Python versions you support. In contrast to the
    # 'Programming Language' classifiers above, 'pip install' will check this
    # and refuse to install the project if the version does not match. If you
    # do not support Python 2, you can simplify this to '>=3.5' or similar, see
    # https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires
    python_requires='>=3.0, <4',

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    #install_requires=['peppercorn'],  # Optional

    # List additional groups of dependencies here (e.g. development
    # dependencies). Users will be able to install these using the "extras"
    # syntax, for example:
    #
    #   $ pip install sampleproject[dev]
    #
    # Similar to `install_requires` above, these must be valid existing
    # projects.
    # extras_require={  # Optional
    #     'dev': ['check-manifest'],
    #     'test': ['coverage'],
    # },

    # If there are data files included in your packages that need to be
    # installed, specify them here.
    #
    # If using Python 2.6 or earlier, then these have to be included in
    # MANIFEST.in as well.
    # package_data={  # Optional
    #     'sample': ['package_data.dat'],
    # },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    #
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    #data_files=[('my_data', ['data/data_file'])],  # Optional

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    #
    # For example, the following would provide a command called `sample` which
    # executes the function `main` from this package when invoked:
    # entry_points={  # Optional
    #     'console_scripts': [
    #         'sample=sample:main',
    #     ],
    # },

    # List additional URLs that are relevant to your project as a dict.
    #
    # This field corresponds to the "Project-URL" metadata fields:
    # https://packaging.python.org/specifications/core-metadata/#project-url-multiple-use
    #
    # Examples listed include a pattern for specifying where the package tracks
    # issues, where the source is hosted, where to say thanks to the package
    # maintainers, and where to support the project financially. The key is
    # what's used to render the link text on PyPI.
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/dtschump/gmic-py/issues',
        'Funding': 'https://libreart.info/en/projects/gmic',
        'Say Thanks!': 'https://twitter.com/gmic_ip',
        'Source': 'https://github.com/dtschump/gmic-py',
    },

    ext_modules = [gmic_module]
)

