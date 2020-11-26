# You should run first: pip install gmic
# Make sure to checkout the README.md in this script's directory

import gmic

# THE HELP COMMAND(S)
gmic.run("help blur")
help(gmic)
help(gmic.run)

# THE SAMPLE OR SP COMMAND
gmic.run("help sample")

gmic.run("sample apples")

# THE DISPLAY COMMAND
gmic.run("sample apples display")
gmic.run("sample duck sample apples display[0]")

# THE PRINT COMMAND
gmic.run("sp leno print")

# THE OUTPUT <SOMEFILE> COMMAND
gmic.run("sample earth output myearth.png")
gmic.run("sample earth elephant output mysamples.jpeg")
gmic.run("sample earth elephant output[1] myelephant.jpeg")

# THE INPUT <SOMEFILE> COMMAND (simple and short form)
gmic.run("input myearth.png display")
gmic.run("myearth.png display")

# LOADING AND SAVING MULTIPLE IMAGES
gmic.run("sample earth sample apples output myimages.png display")
gmic.run("myimages_000000.png myimages_000001.png display")

# APPLYING A SIMPLE FILTER

gmic.run("sample apples blur 4 display")
gmic.run("sample apples rodilius 10 display")

# SELECTING IMAGES BY INDEX
gmic.run("sample apples sample earth blur[1] 4 display")

# APPLYING THE FAMOUS 'STYLIZE' STYLE TRANSFER FILTER
gmic.run("sp leno display")
gmic.run("_fx_stylize landscapenearantwerp display")
gmic.run("sample leno _fx_stylize landscapenearantwerp stylize[0] [1]")

# APPLYING MULTIPLE FILTERS
# ONCE
gmic.run("sample duck smooth 40,0,1,1,2 display")
# 3 TIMES
gmic.run("sample duck repeat 3 smooth 40,0,1,1,2 done display")
# SEVERAL FILTERS IN A ROW
gmic.run("sample duck repeat 3 smooth 40,0,1,1,2 done blur xy,5 rodilius , display")
