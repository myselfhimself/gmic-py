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

print(im)

import struct

im2 = gmic.GmicImage(struct.pack("6f", 1, 2, 3, 4, 5, 6), 3, 2, 1)

print(im2)

print(im2._data)
print(len(im2._data))


floats = struct.unpack("6f", im2._data)
print(floats)

print(im2(y=1))

for z in range(im2._depth):
    for y in range(im2._height):
        for x in range(im2._width):
            for c in range(im2._spectrum):
                print((x, y, z, c), "=", im2(x, y, z, c))


gmic.run("display", images=im2)

# The G'MIC images list (and image names)

gmic.run("display", im2)
images_list = [im2]
gmic.run("add 1 display", images_list)

print(images_list)

print(im2 == images_list[0])

## Image names
gmic.run("sp apples sp earth print")  # No names given
# TODO continue + fix: https://github.com/myselfhimself/gmic-py/issues/81

## Wrapping up - stylized fruits example
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


g.run("display output tuto2_stylization.png", result_images)

# II- Montage pass
g.run("frame 3,3,255 montage X display output tuto2_montage.png", result_images)
