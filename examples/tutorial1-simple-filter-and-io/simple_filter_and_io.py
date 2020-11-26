# THE HELP COMMAND(S)

import gmic

gmic.run("help blur")
help(gmic)
help(gmic.run)

# THE SAMPLE OR SP COMMAND
gmic.run("help sample")  # or "help sp"

gmic.run("sample apples")  # nothing shows this is normal, see next

# THE DISPLAY COMMAND
gmic.run("sample apples display")

# THE OUTPUT <SOMEFILE> COMMAND
gmic.run(
    "sample earth output myearth.png"
)  # outputs the result of the earth sample to a path you want (.png, .jpeg, .tiff, .bmp, .pbm and more are supported)

# THE INPUT <SOMEFILE> COMMAND (simple and short form)
gmic.run("input myearth.png display")  # opens myearth.png and then trying a display
gmic.run(
    "myearth.png display"
)  # here is the short form, where 'input' can be omitted. Note that the 'display' command is not obligatory, it is left for you as a proof that it works.

# LOADING AND SAVING MULTIPLE IMAGES
gmic.run(
    "sample earth sample apples output myimages.png display"
)  # saves to myimages_000000.png  myimages_000001.png. The display command is optional.
gmic.run(
    "myimages_000000.png  myimages_000001.png display"
)  # loads myimages_000000.png  myimages_000001.png and displays them. Note the 'input' command name was omitted.

# APPLYING A SIMPLE FILTER
""" Filters and commands are listed at: https://gmic.eu/reference/
To get inspiration for commands to run, you may also head to the G'MIC gallery https://gmic.eu/gallery/ and click the images to see corresponding commands
"""
# Some example commands
gmic.run(
    "sample apples blur 4 display"
)  # blur's documentation with a nice preview is also at https://gmic.eu/reference/blur.html not just through the "help blur" command
gmic.run(
    "sample apples rodilius 10 display"
)  # more at https://gmic.eu/reference/rodilius.html

# SELECTING IMAGES BY INDEX
gmic.run(
    "sample apples sample earth blur[1] 4 display"
)  # Here the blur was applied only to image with second position

# APPLYING THE FAMOUS 'STYLIZE' STYLE TRANSFER FILTER
gmic.run("sp leno display")  # this is the portrait we will want to be stylized
gmic.run(
    "_fx_stylize landscapenearantwerp display"
)  # let us be hackish and use the internal _fx_stylize function to preview one of Antwerp's painting as a future style
gmic.run("sample leno _fx_stylize landscapenearantwerp stylize[0] [1]")

# APPLYING MULTIPLE FILTERS
# ONCE
gmic.run("sample duck smooth 40,0,1,1,2 display")
# 3 TIMES
gmic.run("sample duck repeat 3 smooth 40,0,1,1,2 done display")
# SEVERAL FILTERS IN A ROW
gmic.run("sample duck repeat 3 smooth 40,0,1,1,2 done blur xy,5 rodilius , display")
