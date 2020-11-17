import gmic

"""
The Python binding for G'MIC or gmic-py (although you "pip install gmic" and "import gmic") is quite rudimentary and tries to bring
together the advantages of the 'gmic' command line tool (a sort of G'MIC language evaluator) with the speed and API-similarity of G'MIC C++.

Below we will cover a bit of what is missing for your full understanding of gmic-py and optimizing processing speed a bit. This will maybe be boring, but investing time there will allow you to spare CPU time and avoid superfluous file reads-writes, especially if you use gmic-py in some bigger back-end or front-end application.

One thing which will be dealt with only in tutorial 3 though, is the interaction of gmic-py with third-party numpy-based libraries and IPython-based environments. If you are impatient, jump to that next tutorial right away. Note though, that some of knowledge of how the GmicImage class works is needed, so you might want to read the related section below beforehand. 

In this tutorial, let us see how the 3 building blocks of gmic-py can be used together: the interpreter, single images, and images lists.
In tutorial 1, you have used the G'MIC interpreter mostly, without noticing how it was intantiated, but used file input and output to avoid Python-level images management. 

"""

# The G'MIC module - for debugging mostly
print(dir(gmic))
"""
['Gmic', 'GmicException', 'GmicImage', '__build__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__', '__version__', 'run']
"""

"""
- Gmic - the G'MIC language intepreter class
- run - shortcut to gmic.Gmic().run for beginners to kick-off to run G'MIC expressions right away
- GmicException - an generic exception thrown by most G'MIC classes (along with standard Python exceptions, such as ValueError etc)
- GmicImage - a wrapper around C++'s gmic_image class (a CImg alias)

"""

print(gmic.__spec__) # path were your compiled G'MIC Python loaded shared library lives. Mostly useful to people installing gmic-py several times.
print(gmic.__version__) # version of the embedded the libgmic C++ interpreter
print(gmic.__build__) # flags that were used for compilation. This allows to understand fast if your gmic-py provides jpeg, png, tiff support
# interesting flags are: openMP is for parallel computing
# fftw3 is needed for spectrum-based computing and managing images with dimensions not in power of 2
# OpenCV is by default not linked to gmic-py, although you could rebuild gmic-py easily and use it

help(gmic) # shows an introduction about gmic-py. Note that this is less instructive than running gmic.run("help <somecommand>") for example.


# The G'MIC interpreter

gmic.run("sp apples rodilius 3")
gmic.run("sp earth blur 5")

g = gmic.Gmic()
g.run("sp apples rodilius 3")
g.run("sp apples blur 5")

# The G'MIC image
im = gmic.GmicImage()
print(dir(im))

help(im)


# The G'MIC images list


