Quickstart
===========
Here is how to fiddle with gmic-py in five minutes.

``gmic-py`` is a cross-platform Python binding for the G'MIC C++ library.
G'MIC is nowadays mostly used for its image processing domain-specific language (DSL), or through its plug-ins for graphical software.
In our case, only the language is available, but it is very powerful though!

Using ``gmic-py`` always boils down to five steps:
#. install the module
#. import it
#. (instantiate a G'MIC language interpreter)
#. evaluate a G'MIC expression against G'MIC samples or your own images
#. retrieve your output images

1. Install ``gmic-py``
#######################
This works on Linux or Mac OS for now. You need no compiler, just Python >= 3.6.

In your favorite shell, run:

.. code-block:: sh

    pip install gmic

This will install the G'MIC pre-compiled module for Python:

.. code-block::

    Collecting gmic
      Downloading gmic-2.9.0-cp36-cp36m-manylinux2014_x86_64.whl (8.8 MB)
         |████████████████████████████████| 8.8 MB 6.8 MB/s
    Installing collected packages: gmic
    Successfully installed gmic-2.9.0

2. Run a simple G'MIC effect and view it
#########################################

You are now ready to work, open a Python 3 terminal or edit your own ``.py`` file and type in the following:

.. code-block:: python

    import gmic
    gmic.run("sp earth blur 4")

What that does is:

#. import the ``gmic`` Python module
#. create a default G'MIC language interpreter and give it an expression to evaluate:

    * ``sp earth`` will load a sample image from G'MIC library, named ``earth``
    * ``blur 4`` will apply a ``blur`` effect to the image(s) before, here with a force of 4.

The G'MIC language's commands are all listed in its `reference documentation on gmic.eu <https://gmic.eu/reference.shtml>`_. `Here is for the ``blur`` command itself. <https://gmic.eu/reference.shtml#blur>`_
If you are on Linux (sorry, not Mac OS), you will see a window popping up with the following image:

.. gmicpic:: sp earth blur 4

If you would like to use your own file instead, just write its path first instead of ``sp earth``:

.. code-block:: python

    gmic.run("/home/me/myimage.jpg blur 4")

3. Save your result to a file
##############################

Whether you are on Linux or MacOS you can also save your image with the ``output`` G'MIC command.

.. code-block:: python

    import gmic
    gmic.run("sp earth blur 4 output myblurredearth.png") # will save in the current working directory

4. Dealing with GmicImage sets
###############################

Now you may want to use your images without having to save them first!

**TODO**

5. Working with Python Numpy/PIL input images
##############################################

**TODO**