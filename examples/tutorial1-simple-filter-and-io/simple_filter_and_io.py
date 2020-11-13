import gmic

# A LITTLE THEORY ABOUT G'MIC COMMANDS SIGNATURE, PIPING AND SUBSETS
# For this section, you do not need to code or run anything at this point. Just meditate.
"""
G'MIC provides more that 500 commands or filters. Which can get updated from the internet by running the "update" or "up" command.
This spares you from updating your gmic binary runtime frequently. Instead, a database of many G'MIC commands gets refreshed on your machine from gmic.eu.

G'MIC stores images internally in the x,y,z,c space (or width, height, depth, channels), allowing you to work with 2D greyscale images, 2D color images, or voxels (3D points) for many applications.

For executing expressions, the G'MIC language parser allows you to pipe commands from left to right:
    <command 1> <command 2> <command 3>
where the result(s) of command 1 is piped as the input of command 2 which outputs in turn to command 3.

In G'MIC each command outputs most of the time a G'MIC Image (or G'MIC Image list if several images are there).

G'MIC commands thus take as input: G'MIC image(s) (or "buffers"), coming from their left side, and also scalar parameters (integers, flots, strings..):
    <former command's output images> <command 1> <command 1 scalar parameters>
Example:
    input myimage.png blur 3,20 

Here is a more complex example with more commands piping, where the G'MIC List of 2 G'MIC Images is passed modified in place from left to right:
    input image1.png image2.png blur 4 sharpen 30 smooth 200 display

You can add a '-' prefix before your G'MIC commands to make them stand out a little more. It changes absolutely nothing for the result.
    -input image1.png image2.png -blur 4 -sharpen 30 -smooth 200 -display

If you want any command in your chain to use only a subset of the leftside results, use the [] index postfix, it will keep the images in your list in place though
    -input image1.png image2.png blur[1] 3 display[0]
The above command will actually blur image2.png but display image1.png only, which is unblurred

Note that G'MIC is a full fledged scripting language, so you can do for, while, if, functions etc with it.

The gmic.eu website and the https://discuss.pixls.us/c/software/gmic community are good friends to learn and ask about G'MIC.
"""

# THE HELP <SOMECOMMAND> COMMAND

gmic.run("help blur")

# Outputs
"""


  gmic: GREYC's Magic for Image Computing: command-line interface
        (https://gmic.eu)
        Version 2.9.1

        Copyright (c) 2008-2020, David Tschumperlé / GREYC / CNRS.
        (https://www.greyc.fr)

    blur (+):
        std_deviation>=0[%],_boundary_conditions,_kernel |
        axes,std_deviation>=0[%],_boundary_conditions,_kernel

      Blur selected images by a quasi-gaussian or gaussian filter (recursive implementation).
      (eq. to 'b').

      'boundary_conditions' can be { 0=dirichlet | 1=neumann }.
      'kernel' can be { 0=quasi-gaussian (faster) | 1=gaussian }.
      When specified, argument 'axes' is a sequence of { x | y | z | c }.
      Specifying one axis multiple times apply also the blur multiple times.
      Default values: 'boundary_conditions=1' and 'kernel=0'.

      Example: [#1]  image.jpg +blur 5,0 +blur[0] 5,1

               [#2]  image.jpg +blur y,10%

      Tutorial: https://gmic.eu/tutorial/_blur.shtml

"""

# THE SAMPLE OR SP COMMAND
# If you see network errors for this section, you should change your firewall settings or just skip using the sample command for now
# Jump to the section about input instead, which allows you to load your own images, and replace the "sample <samplename>" commands
# by "input someimagefilepathonyourcomputer" instead.

gmic.run("help sample") # or "help sp"
"""
  gmic: GREYC's Magic for Image Computing: command-line interface
        (https://gmic.eu)
        Version 2.9.1

        Copyright (c) 2008-2020, David Tschumperlé / GREYC / CNRS.
        (https://www.greyc.fr)

    sample:
        _name1={ ? | apples | balloons | barbara | boats | bottles | butterfly | \
         cameraman | car | cat | cliff | chick | colorful | david | dog | duck | eagle | \
         elephant | earth | flower | fruits | gmicky | gmicky_mahvin | gmicky_wilber | \
         greece | gummy | house | inside | landscape | leaf | lena | leno | lion | \
         mandrill | monalisa | monkey | parrots | pencils | peppers | portrait0 | \
         portrait1 | portrait2 | portrait3 | portrait4 | portrait5 | portrait6 | \
         portrait7 | portrait8 | portrait9 | roddy | rooster | rose | square | swan | \
         teddy | tiger | tulips | wall | waterfall | zelda },_name2,...,_nameN,_width={ \
         >=0 | 0 (auto) },_height = { >=0 | 0 (auto) } |
        (no arg)

      Input a new sample RGB image (opt. with specified size).
      (eq. to 'sp').

      Argument 'name' can be replaced by an integer which serves as a sample index.

      Example: [#1]  repeat 6 sample done
"""

gmic.run("sample apples") # A display window would pop up in gmic's command line executable, but not in Python that is intended!

# THE DISPLAY COMMAND
gmic.run("sample apples display") # This will pop up a display window showing your image, without it needing to be saved anyway on your drive

# THE OUTPUT <SOMEFILE> COMMAND
gmic.run("sample earth output myearth.png") # outputs the result of the earth sample to a path you want (.png, .jpeg, .tiff, .bmp, .pbm and more are supported)

# THE INPUT <SOMEFILE> COMMAND (simple and short form)
gmic.run("input myearth.png display") # opens myearth.png and then trying a display
gmic.run("myearth.png display") # here is the short form, where 'input' can be omitted. Note that the 'display' command is not obligatory, it is left for you as a proof that it works.

# LOADING AND SAVING MULTIPLE IMAGES
gmic.run("sample earth sample apples output myimages.png display") # saves to myimages_000000.png  myimages_000001.png. The display command is optional.
gmic.run("myimages_000000.png  myimages_000001.png display") # loads myimages_000000.png  myimages_000001.png and displays them. Note the 'input' command name was omitted.

# APPLYING A SIMPLE FILTER
""" Filters and commands are listed at: https://gmic.eu/reference/
To get inspiration for commands to run, you may also head to the G'MIC gallery https://gmic.eu/gallery/ and click the images to see corresponding commands
"""
# Some example commands
gmic.run("sample apples blur 4 display") # blur's documentation with a nice preview is also at https://gmic.eu/reference/blur.html not just through the "help blur" command
gmic.run("sample apples rodilius 10 display") # more at https://gmic.eu/reference/rodilius.html

# SELECTING IMAGES BY INDEX
gmic.run("sample apples sample earth blur[1] 4 display") # Here the blur was applied only to image with second position

# APPLYING THE FAMOUS 'STYLIZE' STYLE TRANSFER FILTER
gmic.run("sp leno display") # this is the portrait we will want to be stylized
gmic.run("_fx_stylize landscapenearantwerp display") # let us be hackish and use the internal _fx_stylize function to preview one of Antwerp's painting as a future style
gmic.run("sample leno _fx_stylize landscapenearantwerp stylize .")
