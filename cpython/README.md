# gmic-py
Python binding for G'MIC

![](https://github.com/dtschump/gmic-py/workflows/Ctypes%20GMIC%20Python%20package/badge.svg)
![](https://github.com/dtschump/gmic-py/workflows/CPython%20GMIC%20Manylinux%20build%20CentOS%20x86_64/badge.svg)
![](https://github.com/dtschump/gmic-py/workflows/CPython%20GMIC%20Python%20package%20(Source%20and%20Debian/Ubuntu%20OS%20compilation)/badge.svg)

The aim of this project is to provide an official Python 3 package of the G'MIC image processing library, with its platform-specific binaries bundled or auto-compiled.
When this matures, running `pip install gmic-py` should be all you need to get ready and use G'MIC within data-science, games, video editing, texture editing etc.. Python scripts.

This project is a work in progress and lives under the CeCILL license (similar to GNU Public License).

# TDD - making sure gmic-py works and keeps working
Development follows a test-driven development (TDD) methodology.

For now, to test the development manually you can run a `pytest` suite within `docker`:
```sh
# If you do not have docker: sudo apt-get install docker
cd tests/
sh run_test_scenario.sh
```

On November 18th, 2019 `pip install` from Github, `echo`, basic png generation and output tests work, without in-memory buffers I/O yet :) The project is just very fresh :) See [Github Actions CI tests being run here](https://github.com/dtschump/gmic-py/actions).

## Roadmap

### Q4 2019
1. Create a `pip install -e GITHUB_URL` installable Python package for GMIC, with an API very similar to the C++ library: `gmic_instance.run(...)`, `gmic(...)` and matching exception types. Binary dependencies [should be bundled as in this tutorial](https://python-packaging-tutorial.readthedocs.io/en/latest/binaries_dependencies.html).
    1. Through `Ctypes` dynamic binding on an Ubuntu docker image using Python 2-3. DONE in `ctypes/`
    1. Through custom Python/C++ binding in `cpython/`
1. Create documented examples for various application domains.

### Q1-Q2 2020
1. Move the package to official Python package repositories.
1. In a separate repository, create a Blender Plugin, leveraging the Python library and exposing:
  1. a single Blender GMIC 2D node with a text field or linkable script to add a GMIC expression
  1. as many 2D nodes as there are types of GMIC 'operators'

### Q3-Q4 2020
1. In a separate repository, create a GMIC Inkscape plugin, leveraging the Python library (possibly applying only to image objects, as the Trace bitmap tool does).

## Binding blueprint
This is an overview of how we want the gmic binding inner working:
```python3
from gmic import Gmic, run, Image, GmicException
#we give up the Gmic native List

class GmicException:
   def __init__(self, command, message):
       self.command = command
       self.message = message
   def what(self):
       pass
   def command_help(self):
       pass

class Gmic:
    def __init__(self, images=[]|tuple|iterable[Image], image_names=[]|tuple|iterable, include_stdlib=True, progress=None, is_abort=None):
        self._status = None
        self.include_stdlib = include_stdlib
        # TODO V2 = progress, is_abort
        if all params were given:
           self.run(images, image_names, include_stdlib, progress, is_abort)

    @throws GmicException
    def run(self, images=[], images_names=[], progress=None, abort=None):
        ....
        self._status = ""
        return self

    def _build_lists(self):
        self._build_gmic_images_list(self.images)
        self._build_gmic_images_names_list(self.image_names)

    def _build_gmic_images_list(self):
        """Convert and store to Gmic builtin C++ type"""
        pass

    def _build_gmic_images_names_list(self):
        """Convert and store to Gmic builtin C++ type"""
        pass

    @property
    def status(self):
       """ string result of last operation, or exception text if was raised, or user-entered text through a gmic command. 
       This is a read-only attribute, starting with underscore. See https://stackoverflow.com/a/15812738/420684
       :return str
       """
       return self._status


def run(images=[]|tuple|iterable[Image], image_names=[]|tuple|iterable[Image], include_stdlib=True, progress=None, is_abort=None):
    return Gmic(images, images_names, include_stdlib, progress, is_abort).run()
```
