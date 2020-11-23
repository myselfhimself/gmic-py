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

print(
    gmic.__spec__
)  # path were your compiled G'MIC Python loaded shared library lives. Mostly useful to people installing gmic-py several times.
print(gmic.__version__)  # version of the embedded the libgmic C++ interpreter
print(
    gmic.__build__
)  # flags that were used for compilation. This allows to understand fast if your gmic-py provides jpeg, png, tiff support
# interesting flags are: openMP is for parallel computing
# fftw3 is needed for spectrum-based computing and managing images with dimensions not in power of 2
# OpenCV is by default not linked to gmic-py, although you could rebuild gmic-py easily and use it

help(
    gmic
)  # shows an introduction about gmic-py. Note that this is less instructive than running gmic.run("help <somecommand>") for example.


# The G'MIC interpreter
"""gmic.run is a function which spawns a G'MIC interpreter object for you, lets it interpret your command, then deletes the interpreter object.
For those literate in computer science, there is no singleton design pattern in use at all."""
gmic.run("sp apples rodilius 3 display")
gmic.run("sp earth blur 5 display")

"""In pure Python, the above two lines would be the same as doing (being unsure of when garbage collection for memory-living G'MIC interpreters would happen):
"""
g1 = gmic.Gmic()
g1.run("sp apples rodilius 3 display")
del g1
g2 = gmic.Gmic()
g2.run("sp earth blur 5 display")
del g2
""" gmic.Gmic() instantiates a G'MIC intepreter class, and makes it read its configuration and set up internal variables and operating system capabilities detection etc.. This is a bit heavy and you may not want to repeat too it many times!
For simplicity though, most gmic-py beginner tutorials just write gmic.run() which is akin to the more famous 'gmic' CLI executable.

Here is the better way to evaluate several commands in a row using a single G'MIC interpreter instance:
"""

g = (
    gmic.Gmic()
)  # First create a G'MIC interpreter instance using the Gmic class, and attach to a variable by a simple assignment
g.run(
    "sp apples rodilius 3"
)  # Reuse your variable as many times as you want, and call its run() method.
g.run(
    "sp apples blur 5"
)  # Here you are, a 2nd call, where the G'MIC interpreter was not recreated for nothing!

"""
Note that the G'MIC interpreter do not store states between calls, that is that the input and result images from each last call are forgotten.
Passing in a pure-Python list of G'MIC images is the way to keep track of your images in memory. This will be shown a bit further in the next two sections.
Especially, as the run() method actually takes 3 parameters:
- a command(s) string, 
- an optional list of G'MIC images,
- an optional list of G'MIC image names.
You can read more about this by running help(gmic.Gmic) or visiting the API reference: https://gmic-py.readthedocs.io/en/latest/gmic.html#gmic.Gmic
"""

# The G'MIC image
"""
After discovering the gmic.Gmic interpreter, the G'MIC Image is the other building block of gmic-py (of the G'MIC C++). Here is how to create one from scratch with no data:
"""
im = gmic.GmicImage()
help(gmic.GmicImage)  # Some mini-doc on how to call the GmicImage class
"""Now let us take a look at its properties (attributes):"""
print(dir(im))
"""
['__call__', '__class__', '__copy__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '_data', '_data_str', '_depth', '_height', '_is_shared', '_spectrum', '_width', 'from_PIL', 'from_numpy', 'from_numpy_helper', 'from_skimage', 'to_PIL', 'to_numpy', 'to_numpy_helper', 'to_skimage']

Here the most important attributes you see are:
- _data is a read-only 'bytes' buffer, which G'MIC reads and writes as a list of interleaved 32bit float. Interleaving and non-interleaving is a big topic, and G'MIC seems to an exception compared to many other graphics processing libraries: it stores pixel channel values, channel after channel. For example, for a 3x1 pixels RGB image, the _data would look like: R1R2R3G1G2G3B1B2B3 instead or R1G1B1R2G2B2R3G3B3.
- _width, _height, _depth, _spectrum: read-only integers. G'MIC works in 3D if needed and stores its channels (eg. RGB, HSV, or a few million other channels) in the _spectrum dimensions. So an RGB 1024x768 screenshot would have those attributes as: 1024, 768, 1, 3. Any dimension must >=1.
- from_* and to_* methods are for converting to and from other graphics libraries!! (as long as you install them first in your virtual environment or machine). Indeed, gmic-py was designed so that you spend more time using other famous tools you already love (numpy and PIL namely..) than working with the infamous gmic-py! Interoperability FTW!

Here are less important methods:
- _data_str: is not so important, but for your curiosity, it helps to decode the _data attribute as a unicode string!!! (in same some people wanted to store text in a G'MIC Image... the "parse_gui" command does this actually)
- _is_shared is never used in Python, it helps avoiding duplicate data to an image, when two interpreters work on it.
"""


# Let us see how a GmicImage is  represented as a string:
print(im)
"""<gmic.GmicImage object at 0x7f5d6a028a70 with _data address at 0x26d0180, w=1 h=1 d=1 s=1 shared=0>"""
# So we have juste create a GmicImage with default parameters, that is an empty buffer _data, and dimensions width=height=depth=spectrum=1 and no sharing.

"""If you know numpy, GmicImages look like numpy's ndarrays, though the former are much less practical to manipulate!!! They are actually a very superficial binding of G'MIC's C++ gmic_image / cimg image class. To instantiate a GmicImage, you can pass in a bytes buffer, as well as optional dimensions: width, height, depth. Numpy does that as well.
Here is a complex way to create a GmicImage from random data:"""
import struct  # a handy pure-Python module to parse and build buffers

# Here we set up a GmicImage with 6 floats and dimensions 3x2x1
im2 = gmic.GmicImage(struct.pack("6f", 1, 2, 3, 4, 5, 6), 3, 2, 1)
# Let us print that image
print(im2)
"""
<gmic.GmicImage object at 0x7f5d6a028b10 with _data address at 0x26d0f20, w=3 h=2 d=1 s=1 shared=0>
"""
# You may print the _data buffer and its length, if you are very curious:
print(im2._data)
"""
b'\x00\x00\x80?\x00\x00\x00@\x00\x00@@\x00\x00\x80@\x00\x00\xa0@\x00\x00\xc0@'
"""
print(len(im2._data))
"""
24 # Remember a 3x2x1 G'MIC Image makes up 6 floats (always 32 bits or 4-bytes long), so 6x4=24 bytes
"""

"""
The GmicImage class has no method to print its pixels into console nicely as you would in numpy with print(myndarray).
Now, for pixel access, numpy provides a [] coordinates accessor numpy.ndarray[x,y,z,....] to read matrix cell values.
GmicImage's pixel accessor is just the () on a GmicImage instance, that is to say, each GmicImage object is callable.
The signature for this accessor is myimage(x=0,y=0,z=0,s=0), each parameter is optional and defaults to 0.
(s stands for spectrum, it is interchangeable with c for channel in most G'MIC literature)
"""
print(im2(y=1))  # reads at x=0,y=1,z=0,s=0
# 2


# You may also want to view your image with your eyes:
gmic.run(
    "display", images=im2
)  # Or try gmic.run("print", im2) or gmic.run("output myimage.png", im2) if your environment has no display
"""
[gmic]-1./ Display image [0] = '[unnamed]', from point (1,1,0).
[0] = '[unnamed]':
  size = (3,2,1,1) [24 b of floats].
  data = (1,2,3;4,5,6).
  min = 1, max = 6, mean = 3.5, std = 1.87083, coords_min = (0,0,0,0), coords_max = (2,1,0,0).
"""

# The G'MIC images list (and image names)
"""Ooops!!! In the former section, we forgot to talk about G'MIC's intepreter images list parameter and started using it!!
Just for now, here is a little trick which we have done.
gmic.run() or gmic.Gmic().run() or gmic.Gmic() all have the same signature (commands, images, image_names), and their second parameter, the 'images' parameter accepts mostly only lists of GmicImage objects, which list will be emptied and refilled in place... OR a single GmicImage, which will be read only (no in-place modification)"""
# So:
gmic.run("display", im2)  # is a read-only operation, we can pass a single GmicImage
# But the proper way is to put your single image in a list
images_list = [im2]
gmic.run("add 1 display", images_list)  # add value 1 to each pixel then display
# Note above that the min and max value are properly shifted by 1, compared to our first 'display' of im2, before in that same tutorial:
"""
gmic.run("add 1 display", images_list) # add value 1 to each pixel then display
[gmic]-1./ Display image [0] = '[unnamed]', from point (1,1,0).
[0] = '[unnamed]':
  size = (3,2,1,1) [24 b of floats].
  data = (2,3,4;5,6,7).
  min = 2, max = 7, mean = 4.5, std = 1.87083, coords_min = (0,0,0,0), coords_max = (2,1,0,0).
"""
print(images_list)
# Not all commands have the same behaviour in terms or adding, replacing or removing images in the input images list
# Here the 'add' command changes input images in place by default, so our images_list is still 1-item long
"""[<gmic.GmicImage object at 0x7fbbe9fd3d30 with _data address at 0x1c16550, w=3 h=2 d=1 s=1 shared=0>]"""

# Let us check if our images list's single item has the same content or address as the original im2 GmicImage... NO! And this is EXPECTED!
print(im2 == images_list[0])
# Maybe the C++ code changes images in place, not always though.. Because tracking images pointers and positions in the gmic_list was too complicated
# gmic-py will actually not change your images in place at all! Just empty and refill your list of GmicImages!
# This is just fine for daily non-picky work!

## Image names
# When we run the G'MIC 'display' or 'print' commands, you may notice in your console or with your mouse in the image display window, that our images so far are all 'unnamed'.
"""[gmic]-1./ Display image [0] = '[unnamed]', from point (1,1,0)."""
# This is not an issue, but you can give names if you prefer, and refer to those names for indexing:
gmic.run("sp apples sp earth print")  # No names given
# TODO continue + fix: https://github.com/myselfhimself/gmic-py/issues/81

## Wrapping up - stylized fruits example
"""
Here is an example of a stylized nature montage with some parameters injection.
To prepare this example:
- the command line command "gmic help sp" (or gmic.run("help sp")) has been used to decide which samples would nice to pick. 
- The gmic.eu Gallery page for Stylization has been used to pick image names supported by the _fx_stylize (which is a non-documented command providing famous painting samples..): https://gmic.eu/gallery/stylization.html
  - Actually, since this is a G'MIC internal command, its code can be found here: https://raw.githubusercontent.com/dtschump/gmic/master/src/gmic_stdlib.gmic (look for _fx_stylize)
- The List of Commands page from the G'MIC only reference, https://gmic.eu/reference/list_of_commands.html especially the stylize command page: https://gmic.eu/reference/stylize.html
"""
import gmic

g = gmic.Gmic()

# I- Stylization pass
nature_config = [
    {"sample": "apples", "style": "convergence"},
    {"sample": "fruits", "style": "redwaistcoat"},
    {"sample": "flower", "style": "lesdemoisellesdavignon"},
]

result_images = []
for conf in nature_config:
    images_list = []
    # we use stylize's default parameters, hence the '.' character
    # the keep[0] command keeps only the first image in the images list
    g.run(
        "sp {} _fx_stylize {} stylize .".format(conf["sample"], conf["style"]),
        images_list,
    )
    print(images_list)
    result_images.append(images_list[0])


g.run("display", result_images)

# II- Montage pass
# Build a 3x3-bordered pixels frame around images, white, and make an automatic montage, display it and save to file
g.run("frame 3,3,255 montage X display output mymontage.png")

"""THE END
That was it for tutorial number 2! Now you know more about reusing a G'MIC interpreter handle and calling it several times on a GmicImage list. Congratulations!
Tutorial 3 will be on using PIL (or Pillow) with gmic-py.
"""
