# About the OpenCV gmic-py + camera example

If you `pip install gmic`, the `gmic` (aka `gmic-py`) precompiled version you will install does not contain OpenCV.

## Building your own `gmic-py` with OpenCV support 

For this example to work, you must build your own `gmic-py` wheel on a computer with `libopencv-dev` installed. `gmic-py`'s setup file for wheels will auto-detect its existence thanks to `pkg-config` (for MacOS/Linux OSes) and link to it. 
Here is the [OpenCV existence test in setup.py on Github](https://github.com/myselfhimself/gmic-py/blob/63f23552f830bd0fc7b3f5bcd5fc0509fe368405/setup.py#L65). 

In short, for building:

``sh
# See docs/compiling.rst or https://gmic-py.readthedocs.io/en/latest/compiling.html for information on the requirements
sudo apt-get install libfftw3-dev libcurl4-openssl-dev libpng-dev liblz-dev libgomp1 libtiff-dev libjpeg-dev wget
# Here is the required libopencv
sudo apt-get install libopencv-dev
bash build_tools.bash 1_clean_and_regrab_gmic_src
bash build_tools.bash 4_build_wheel
cd dist/
pip install *.whl
``

## Running the example
Once you have an OpenCV `gmic-py` wheel installed in your (virtual) Python environment, just plug in your web camera and run the example with `python` (or `python3`) .
