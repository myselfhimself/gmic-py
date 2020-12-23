"""A setuptools based setup module for the Gmic Python bindings binary module.
"""

from os import path, listdir, environ
import sys
import platform

from setuptools import setup, Extension, find_packages
import pkgconfig

here = path.abspath(path.dirname(__file__))
gmic_src_path = path.abspath("src/gmic/src")


# List of non-standard '-l*' compiler parameters
extra_link_args = []

# List of libs to get include directories and linkable libraries paths from for compiling
pkgconfig_list = ["zlib"]

# Macros to toggle (gmic or CImg will do C/C++ #ifdef checks on them, testing mostly only their existence)
# cimg_date and cimg_date are true variables, the value of which is checked in the C/C++ source
define_macros = [
    ("gmic_build", None),
    ("cimg_date", '""'),
    ("cimg_time", '""'),
    ("gmic_is_parallel", None),
    ("cimg_use_zlib", None),
    ("cimg_use_openmp", None),
    ("gmic_py_numpy", None),  # Numpy support
    (
        "gmic_py_jupyter_ipython_display",
        None,
    ),  # "display" statements display for Jupyter/Ipython
]

# Only require x11 if found
if pkgconfig.exists("x11"):
    define_macros += [("cimg_display", None)]
    pkgconfig_list += ["x11"]

# Only require libpng if found
if pkgconfig.exists("libpng"):
    define_macros += [("cimg_use_png", None)]
    pkgconfig_list += ["libpng"]

# Only require libtiff if found
if pkgconfig.exists("libtiff-4"):
    define_macros += [("cimg_use_tiff", None)]
    pkgconfig_list += ["libtiff-4"]

# Only require libjpeg if found
if pkgconfig.exists("libjpeg"):
    define_macros += [("cimg_use_jpeg", None)]
    pkgconfig_list += ["libjpeg"]

# Only require fftw3 if found (non-2^ size image processing fails without it)
# We do not toggle cimg_use_fftw3, it is buggy
if pkgconfig.exists("fftw3"):
    define_macros += [("cimg_use_fftw3", None)]
    pkgconfig_list += ["fftw3"]
    extra_link_args += ["-lfftw3_threads"]

# Only compile with OpenCV if exists (nice for the 'camera' G'MIC command :-D )
if pkgconfig.exists("opencv"):
    define_macros += [("cimg_use_opencv", None)]
    pkgconfig_list += ["opencv"]

packages = pkgconfig.parse(" ".join(pkgconfig_list))
libraries = packages["libraries"] + [
    "pthread"
]  # removed core-dumping 'gomp' temporarily (for manylinux builds)

library_dirs = packages["library_dirs"] + [here, gmic_src_path]
if sys.platform == "darwin":
    library_dirs += ["/usr/local/opt/llvm@6/lib"]
include_dirs = packages["include_dirs"] + [here, gmic_src_path]
if sys.platform == "darwin":
    include_dirs += ["/usr/local/opt/llvm@6/include"]
# Debugging is now set through --global-option --debug and more.
# debugging_args = [
#     "-O0",
#     "-g",
# ]  # Uncomment this for faster compilation with debug symbols and no optimization

debug_enabled = "--debug" in sys.argv

extra_compile_args = ["-std=c++11"]
if debug_enabled:
    extra_compile_args += ["-O0"]
    extra_compile_args += ["-g"]
else:
    extra_compile_args += ["-Ofast", "-flto"]
    extra_link_args += ["-flto"]

if sys.platform == "darwin":
    extra_compile_args += ["-fopenmp", "-stdlib=libc++"]
    extra_link_args += [
        "-lomp",
        "-nodefaultlibs",
        "-lc++",
    ]  # options inspired by https://github.com/explosion/spaCy/blob/master/setup.py
elif sys.platform == "linux":  # Enable openmp for 32bit & 64bit linuxes
    extra_compile_args += ["-fopenmp"]
    extra_link_args += ["-lgomp"]

print("Define macros:")
print(define_macros)

print("Include dirs:")
print(include_dirs)

# Static CPython gmic.so embedding libgmic.so.2
gmic_module = Extension(
    "gmic",
    include_dirs=include_dirs,
    libraries=libraries,
    library_dirs=library_dirs,
    sources=["gmicpy.cpp", path.join(gmic_src_path, "gmic.cpp")],
    define_macros=define_macros,
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
    language="c++",
)

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Grab the version from the VERSION file, which is also include in MANIFEST.in
# Technique highlighted here: https://packaging.python.org/guides/single-sourcing-package-version/
with open(path.join(".", "VERSION")) as version_file:
    version = version_file.read().strip()

setup(
    name="gmic",
    version=version,
    description="Binary Python3 bindings for the G'MIC C++ image processing library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/myselfhimself/gmic-py",
    author="David Tschumperlé, Jonathan-David Schröder G'MIC GREYC IMAGE Team of CNRS, France",
    author_email="David.Tschumperle@ensicaen.fr, jonathan.schroder@gmail.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Other Audience",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Artistic Software",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Software Development",
        "License :: OSI Approved :: CEA CNRS Inria Logiciel Libre License, version 2.1 (CeCILL-2.1)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="image processing gmic g'mic voxel 2d 3d filter",  # Optional
    py_modules=["gmic"],
    python_requires=">=3.0, <4",
    install_requires=["wurlitzer"],  # For Jupyter / IPython notebooks support
    project_urls={
        "Bug Reports": "https://github.com/myselfhimself/gmic-py/issues",
        "Funding": "https://libreart.info/en/projects/gmic",
        "Say Thanks!": "https://twitter.com/gmic_ip",
        "Source": "https://github.com/myselfhimself/gmic-py",
        "Documentation": "https://gmic-py.readthedocs.io",
    },
    ext_modules=[gmic_module],
)
