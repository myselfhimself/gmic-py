Getting started
===============
Here is how to fiddle with gmic-py in five minutes.

gmic-py is a cross-platform Python binding for the G'MIC C++ library.
G'MIC is nowadays mostly used either through its domain-specific G'MIC image processing language, or through its plug-ins for graphical software.
Thanks to gmic-py you can fiddle interactively with the C++ API in the middle of any of your Python code.

Using gmic-py always boils down to importing the gmic python module, running G'MIC-language commands inside a one-time or reusable interpreter.
```
import gmic
print(dir(gmic))
gmic.run("sp earth blur 4")
```

.. gmicpic:: sp earth blur 4 output earthy.png
.. gmicpic:: sp leno blur 4
