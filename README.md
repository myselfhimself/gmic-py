# gmic-py
Python binding for G'MIC

This work is under the CeCILL license (similar to GNU Public License).

## Roadmap

### Q4 2019
1. Create a Python package for GMIC, with an API very similar to the C++ library: `gmic_instance.run(...)`, `gmic(...)` and exception types.
1. Create examples for various application domains.

### Q1-Q2 2020
1. In a separate repository, create a Blender Plugin, leveraging the Python library and exposing:
  1. a single Blender GMIC 2D node with a text field or linkable script to add a GMIC expression
  1. as many 2D nodes as there are types of GMIC 'operators'

### Q3-Q4 2020
1. In a separate repository, create a GMIC Inkscape plugin, leveraging the Python library (possibly applying only to image objects, as the Trace bitmap tool does).
  
