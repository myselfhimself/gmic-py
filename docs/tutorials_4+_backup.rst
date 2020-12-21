Tutorial 4 - segmentation and Pygame or tkinter
#################################################

This tutorial will show you two ways to implement a user interface around ``gmic-py`` using Pygame (a Python module for building video games) or tkinter (a simplistic GUI library).
Both possibilities are cross-platform, your goal will be to allow users to isolate background from foreground in a window using their mouse.

Thanks to `Pierre Bernard for his labelizerpy project <https://github.com/uftos/labelizerpy>`_, which gave inspiration for the tkinter implementation.

User stories (User scenario)
******************************
The user stories (per the agile methodologies) for our application look like this:

User story 0 - startup screen

As a user, when I run the program, I see a black canvas, and the following buttons (or shortcuts info), for:

- loading a file
- painting foreground points (aka labels)
- painting background points
- previewing a split preview
- saving my results

User story 1 - loading a picture

As a user, I click on a 'load' button and can load a single file, which fills my canvas' background.

User story 2 - toggling foreground and background mode

As a user, I can click the foreground and background mode mutually exclusively. Some text or color change shows me that I am in this mode.
I can also see a dot below my cursor when it flies over the canvas.



Tutorial 5 - numpy, PIL, Scikit-image
#######################################

TODO

