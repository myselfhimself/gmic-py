[![G'MIC Logo](https://gmic.eu/img/logo4.jpg)](https://gmic.eu)
[![Python Logo](https://www.python.org/static/community_logos/python-logo-master-v3-TM-flattened.png)](https://www.python.org)

#### 
#### Python binding for G'MIC - A Full-Featured Open-Source Framework for Image Processing
##### https://gmic.eu

---------------------------

# gmic-py
[![PyPI version shields.io](https://img.shields.io/pypi/v/gmic.svg)](https://pypi.python.org/pypi/gmic/)
[![PyPI download monthly](https://img.shields.io/pypi/dm/gmic.svg)](https://pypi.python.org/pypi/gmic/)
[![PyPI license](https://img.shields.io/pypi/l/gmic.svg)](https://pypi.python.org/pypi/gmic/)
[![PyPI format](https://img.shields.io/pypi/format/gmic.svg)](https://pypi.python.org/pypi/gmic/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/gmic.svg)](https://pypi.python.org/pypi/gmic/)
[![PyPI implementation](https://img.shields.io/pypi/implementation/gmic.svg)](https://pypi.python.org/pypi/gmic/)
[![PyPI status](https://img.shields.io/pypi/status/gmic.svg)](https://pypi.python.org/pypi/gmic/)
![Read the Docs](https://img.shields.io/readthedocs/gmic-py)

![CPython GMIC Optimized Python package (Source and Debian/Ubuntu OS compilation)](https://github.com/myselfhimself/gmic-py/workflows/CPython%20GMIC%20Optimized%20Python%20package%20(Source%20and%20Debian/Ubuntu%20OS%20compilation)/badge.svg)
![CPython GMIC Manylinux 2010 & 2014 x86_64 Optimized No-release](https://github.com/myselfhimself/gmic-py/workflows/CPython%20GMIC%20Manylinux%202010%20&%202014%20x86_64%20Optimized%20No-release/badge.svg)
![CPython GMIC Debug Python package (Source and Debian/Ubuntu OS compilation)](https://github.com/myselfhimself/gmic-py/workflows/CPython%20GMIC%20Debug%20Python%20package%20(Source%20and%20Debian/Ubuntu%20OS%20compilation)/badge.svg)
![CPython GMIC MacOS Optimized Build](https://github.com/myselfhimself/gmic-py/workflows/CPython%20GMIC%20MacOS%20Optimized%20Build/badge.svg)

`gmic-py` is the official Python 3 binding for the [G'MIC C++ image processing library](https://gmic.eu) purely written with Python's C API.
Its Python package name on [pypi.org](https://pypi.org/project/gmic/) is just `gmic`.
This project lives under the CeCILL license (similar to GNU Public License).


You can use the `gmic` Python module for projects related to desktop or server-side graphics software, numpy, video-games, image procesing.

![gmic-py 2.9.2 release plan](docs/_static/images/292_plan.png)

[gmic-blender](https://github.com/myselfhimself/gmic-blender) is a Blender3d add-on bundling `gmic-py` and allowing you use a new `gmic` module from there without installing anything more.

## Quickstart
First install the G'MIC Python module in your (virtual) environment.

```sh
pip install gmic
```

G'MIC is a language processing framework, interpreter and image-processing scripting language. 
Here is how to load `gmic`, and evaluate some G'MIC commands with an interpreter.
```python
import gmic
gmic.run("sp earth blur 4") # On Linux a window shall open-up with a blurred earth
gmic.run("sp rose fx_bokeh 3,8,0,30,8,4,0.3,0.2,210,210,80,160,0.7,30,20,20,1,2,170,130,20,110,0.15,0 output rose_with_bokeh.png") # Save a rose with bokeh effect to file
```

Longer tutorials are available in the [documentation](https://gmic-py.readthedocs.io/).

## Documentation
Full documentation is being written at [https://gmic-py.readthedocs.io/](https://gmic-py.readthedocs.io/).

## Supported platforms
`gmic-py` works for Linux and Mac OS x 64bits architecture x Python >= 3.6. Windows support is planned for Q4 2020.

In case your environment is a type of Unix, but compiling from source is needed, note that the `pip` installer will download `gmic-py`'s source and most possibly compile it very well.
See the `CONTRIBUTING.md` file and the [documentation](https://gmic-py.readthedocs.io/) for tips on building `gmic-py` for your own OS.

## Examples
### Applying a simple filter

```python
import gmic
gmic.run("sample apples rodilius 10 display") # more at https://gmic.eu/reference/rodilius.html
```

[Example tutorial 1](https://gmic-py.readthedocs.io/en/latest/tutorials.html#applying-a-one-or-more-filter-s)
![Apple with rodilius effect](examples/tutorial1-simple-filter-and-io/rodilius_apple.png)

## Numpy integration
`gmic-py` supports `GmicImage` input/output with `numpy`, `scikit-image` and `Pillow` (`PIL`) if any of those are installed.

```python
import numpy
from matplotlib import pyplot as plt
import gmic

images = []
gmic.run("sp apples blur_x 30 fx_freaky_bw 90,20,0,0,0,0", images) # horizontal blur+special black&white
numpy_im = images[0].to_numpy_helper(interleave=True,permute="yxzc", squeeze_shape=True, astype=numpy.uint8)
plt.imshow(numpy_im, plt.get_cmap('gray'))
plt.show()
```

[Read more in the Quickstart tutorial](https://gmic-py.readthedocs.io/en/latest/gettingstarted.html#working-with-the-numpy-support)
![Numpy + Matplotlib](docs/_images/gmic_apples_gray.png)


### Creating a flipbook from a GIF file
Filtering GIF images, montage'd into an A4 sheet paper.

[Example tutorial 3](https://gmic-py.readthedocs.io/en/latest/tutorials.html#tutorial-3-filtering-gif-and-videos)
![Example flipping](examples/tutorial3-animated-files/tutorial3_flipbook.gif)

### Using your camera with G'MIC's optional OpenCV linking
If your machine has `libopencv` installed and your gmic-py was compiled from source (ie. `python setup.py build`), it will be dynamically linked.

[Example script](examples/opencv-camera/gmic-py-opencv-camera.py)

![Live example](examples/opencv-camera/gmic-py-opencv-camera.gif)

