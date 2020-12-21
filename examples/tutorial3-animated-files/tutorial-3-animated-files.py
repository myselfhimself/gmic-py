import gmic
import shutil

# Paper flipbook example from a GIF file
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

    im = Image.open(GIF_FILENAME)

    for frame in ImageSequence.Iterator(im):
        images_list.append(gmic.GmicImage.from_PIL(frame))

# Skip first green frame
images_list = images_list[1:]
# The G'MIC equivalent would be using 'remove' or 'keep'
# remove: https://gmic.eu/reference/remove.html
# keep: https://gmic.eu/reference/keep.html
# g.run("remove[0]", images_list)
# or
# g.run("keep[1--1]", images_list)

# Display all frames at once (no change to images list)
g.run("display", images_list)

# Alternative for debugging
# Commenting it for now, as it replaces your images_list with a 1-item images list
# g.run("_document_gmic display", images_list)

# Playback
g.run("animate", images_list)

# Adding a random stars pass
g.run("stars , animate", images_list)

# Adding a growing blur pass (blur strength = 5 x current frame index)
# $! is the number of frames
# $> is the current frame's index
g.run("repeat $! blur[$>] {$>*2} done animate", images_list)


# Make a montage for DIN A4 shape with 10 pixels per mm density

# frame_xy and frame G'MIC commands are synonyms
g.run("frame_xy 40,3 append_tiles 4, resize_ratio2d 2100,2970 display.", images_list)
# g.run("frame_xy 40,3 append_tiles ,4 rotate 90 resize_ratio2d 2100,2970 output flipbook.png", images_list)

# With implicit subprocess call to ImageMagick's convert if installed

# gmic https://upload.wikimedia.org/wikipedia/commons/c/cb/2016-09-16_20-30-00_eclipse-lunaire-ann2.gif remove[0] repeat $! blur[$>] {$>*5} stars , done frame 40,3 append_tiles ,4 rotate 90 resize_ratio2d 2100,2970 output flipbook.png
# Or with PIL sequence editor
# TODO
#
# # Example of a longer GIF requiring multiple pages
# gmic.run(
#     "https://gmic.eu/gallery/img/codesamples_full_1.gif remove[0] repeat $! blur[$>] {$>*5} done frame 40,3 append_tiles 2,2 display rotate 90 resize_ratio2d 2100,2970 display"
# )
#
# # Example of live window demo
# gmic.run(
#     "w[] https://gmic.eu/gallery/img/codesamples_full_1.gif remove[0] repeat $! blur[$>] {$>*5} w[$>] done"
# )
#
# # ---------------
#
# # TODO AVI non-linear video editor example
# # Using PyAv https://scikit-image.org/docs/dev/user_guide/video.html#pyav which embed libffmpeg on all OSes
