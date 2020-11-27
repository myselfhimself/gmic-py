import gmic
import shutil

# Flipbook example from a GIF file
# ----------------------------------
g = gmic.Gmic()
images_list = []
GIF_FILENAME = "moonphases.gif"

# If 'convert' is installed
if shutil.which("convert"):
    g.run(GIF_FILENAME, images_list)
else:
    # If convert is absent
    # PIL and numpy must be installed for this to work
    import numpy
    from PIL import Image, ImageSequence

    im = Image.open("moonphases.gif")

    for frame in ImageSequence.Iterator(im):
        images_list.append(gmic.GmicImage.from_PIL(frame))

gmic.run("display", images_list)

"""
Goal make a flipbook to be printed on DIN A4 Paper, then cut and flipped by hand
"""

# With implicit subprocess call to ImageMagick's convert if installed
# gmic https://upload.wikimedia.org/wikipedia/commons/c/cb/2016-09-16_20-30-00_eclipse-lunaire-ann2.gif remove[0] repeat $! blur[$>] {$>*5} stars , done frame 40,3 append_tiles ,4 rotate 90 resize_ratio2d 2100,2970 output flipbook.png
# Or with PIL sequence editor
# TODO

# Example of a longer GIF requiring multiple pages
gmic.run(
    "https://gmic.eu/gallery/img/codesamples_full_1.gif remove[0] repeat $! blur[$>] {$>*5} done frame 40,3 append_tiles 2,2 display rotate 90 resize_ratio2d 2100,2970 display"
)

# Example of live window demo
gmic.run(
    "w[] https://gmic.eu/gallery/img/codesamples_full_1.gif remove[0] repeat $! blur[$>] {$>*5} w[$>] done"
)

# ---------------

# TODO AVI non-linear video editor example
# Using PyAv https://scikit-image.org/docs/dev/user_guide/video.html#pyav which embed libffmpeg on all OSes
