# gmic-py
Python binding for G'MIC

The aim of this project is to provide an official Python 3 package of the G'MIC image processing library, with its platform-specific binaries bundled or auto-compiled.
When this matures, running `pip install gmic-py` should be all you need to get ready and use G'MIC within data-science, games, video editing, texture editing etc.. Python scripts.

This project is a work in progress and lives under the CeCILL license (similar to GNU Public License).

# TDD - making sure gmic-py works and keeps working
Development follows a test-driven development (TDD) methodology.

For now, to hand-test the development you can run a `pytest` suite within `docker`:
```sh
# If you do not have docker: sudo apt-get install docker
cd tests/
sh run_test_scenario.sh
```

On November 7th, 2019 all tests fail :) The project is just very fresh :)

## Roadmap

### Q4 2019
1. Create a `pip install -e GITHUB_URL` installable Python package for GMIC, with an API very similar to the C++ library: `gmic_instance.run(...)`, `gmic(...)` and matching exception types. Binary dependencies [should be bundled as in this tutorial](https://python-packaging-tutorial.readthedocs.io/en/latest/binaries_dependencies.html).
1. Create documented examples for various application domains.

### Q1-Q2 2020
1. Move the package to official Python package repositories.
1. In a separate repository, create a Blender Plugin, leveraging the Python library and exposing:
  1. a single Blender GMIC 2D node with a text field or linkable script to add a GMIC expression
  1. as many 2D nodes as there are types of GMIC 'operators'

### Q3-Q4 2020
1. In a separate repository, create a GMIC Inkscape plugin, leveraging the Python library (possibly applying only to image objects, as the Trace bitmap tool does).
