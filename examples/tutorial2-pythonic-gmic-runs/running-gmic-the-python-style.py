# You should run first: pip install gmic
# Make sure to checkout the README.md in this script's directory

import gmic

# The G'MIC module - for debugging mostly
print(dir(gmic))

print(gmic.__spec__)
print(gmic.__version__)
print(gmic.__build__)

help(gmic)


# The G'MIC interpreter
gmic.run("sp apples rodilius 3 display")
gmic.run("sp earth blur 5 display")

g1 = gmic.Gmic()
g1.run("sp apples rodilius 3 display")
del g1
g2 = gmic.Gmic()
g2.run("sp earth blur 5 display")
del g2

g = gmic.Gmic()
g.run("sp apples rodilius 3")
g.run("sp apples blur 5")

# The G'MIC image
im = gmic.GmicImage()
im_ = gmic.GmicImage(width=640, height=480, spectrum=3)
help(gmic.GmicImage)

print(dir(im))

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
Just in case you wanted to read your GmicImage's data as floats at once, here is a pythonic way
"""
floats = struct.unpack(
    "6f", im2._data
)  # "6f" for six floats or str(len(im2._data)/4)+"f"
print(floats)
# (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)

"""
The GmicImage class has no method to print its pixels into console nicely as you would in numpy with print(myndarray).
Now, for pixel access, numpy provides a [] coordinates accessor numpy.ndarray[x,y,z,....] to read matrix cell values.
GmicImage's pixel accessor is just the () on a GmicImage instance, that is to say, each GmicImage object is callable.
The signature for this accessor is myimage(x=0,y=0,z=0,s=0), each parameter is optional and defaults to 0.
(s stands for spectrum, it is interchangeable with c for channel in most G'MIC literature)
"""
print(im2(y=1))  # reads at x=0,y=1,z=0,s=0
# 2.0

"""
Just in case you needed it some day, here is a way to print each pixel within 4D (3D+channels aka spectrum) for loops
"""
for z in range(im2._depth):
    for y in range(im2._height):
        for x in range(im2._width):
            for c in range(im2._spectrum):
                print((x, y, z, c), "=", im2(x, y, z, c))

""" will print:
(0, 0, 0, 0) = 1.0
(1, 0, 0, 0) = 2.0
(2, 0, 0, 0) = 3.0
(0, 1, 0, 0) = 4.0
(1, 1, 0, 0) = 5.0
(2, 1, 0, 0) = 6.0
"""


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
    g.run(
        "sp {} _fx_stylize {} stylize[0] [1]".format(conf["sample"], conf["style"]),
        images_list,
    )
    print(images_list)
    result_images.append(images_list[0])


g.run("display", result_images)

# II- Montage pass
# Build a 3x3-bordered pixels frame around images, white, and make an automatic montage, display it and save to file
g.run("frame 3,3,255 montage X display output mymontage.png", result_images)

"""THE END
That was it for tutorial number 2! Now you know more about reusing a G'MIC interpreter handle and calling it several times on a GmicImage list. Congratulations!
Tutorial 3 will be on using PIL (or Pillow) with gmic-py.
"""
