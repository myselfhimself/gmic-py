Jupyter/IPython support
===========================
Since version 2.9.1, `gmic-py` has been improved so that you can use `gmic` as a daily tool from any the following IPython-based shells and possibly more:

* `IPython <https://ipython.org/>`_ is an open-source framework improving Python shell experience in consoles, web browsers and desktop user interfaces.

* `Jupyter <https://jupyter.org/>`_ is a sub-project of the IPython-based initiative providing amongst others `JupyterLab` (aka `Jupyter Notebooks`), a web-browser application for editing scientifical Python scripts in runnable sub-steps.

* `Jupyter QtConsole <https://qtconsole.readthedocs.io/en/stable/>`_ is an implementation of the JupyterLab as as desktop application using the Qt GUI framework.
* `Google Colab <https://colab.research.google.com/>`_ is a Google alternative to `JupyterLab`, also leveraging the IPython technology.

How-to
########

Installing
***********
Unless you are using a local `JupyterLab` (ie. web interface) or `Jupyter QtConsole` from your own virtual-environment where `gmic-py` can be pre-installed using `pip install gmic`, here is an example command to install `gmic-py`:

.. code-block:: sh

    !pip install gmic # or gmic==2.9.1-alpha6

.. code-block::

    Collecting gmic==2.9.1-alpha1
      Downloading https://files.pythonhosted.org/packages/c9/43/f8cbc667ff1e8eb556897c256da6b6317c94dc8e6b9b930a0af0b5690d2f/gmic-2.9.1a1-cp36-cp36m-manylinux2014_x86_64.whl (8.7MB)
         |████████████████████████████████| 8.8MB 2.8MB/s
    Collecting wurlitzer
      Downloading https://files.pythonhosted.org/packages/0c/1e/52f4effa64a447c4ec0fb71222799e2ac32c55b4b6c1725fccdf6123146e/wurlitzer-2.0.1-py2.py3-none-any.whl
    Installing collected packages: wurlitzer, gmic
    Successfully installed gmic-2.9.1a1 wurlitzer-2.0.1


Using
*****

The following examples have nothing special compared to a regular `gmic-py` usage and were tested on Google Colab, a web type of Jupyter/IPython notepad.

.. code-block:: python

    import gmic
    # You might optionnally see a message as follows:
    # gmic-py: wurlitzer found (for G'MIC stdout/stderr redirection) and enabled automatically through IPython '%load_ext wurlitzer'.
    images = []
    gmic.run("300,400,1,3 fx_camouflage 9,12,100,30,46,33,75,90,65,179,189,117,255,246,158 display", images)
    # A matplotlib or other type of image view should pop inline
    # Expected text output:
    # [gmic]-1./ Display image [0], from point (150,200,0) (console output only, no display available).
    # [0] = '[unnamed]':
    #   size = (300,400,1,3) [1406 Kio of floats].
    #   data = (95.8,95.8,95.8,95.8,95.8,95.8,95.8,95.8,95.8,95.8,95.8,95.8,(...),75.4,75.4,75.4,75.4,75.4,75.4,75.4,75.4,75.4,75.4,75.4,75.4).
    #   min = 30, max = 255, mean = 111.497, std = 51.1507, coords_min = (125,0,0,0), coords_max = (167,18,0,0).

.. gmicpic:: 300,400,1,3 fx_camouflage 9,12,100,30,46,33,75,90,65,179,189,117,255,246,158

.. code-block:: python

    import gmic
    images = []
    # Note that the "sample" command relies exclusively on gmic.eu online images reachability
    # So the following might not work if you are using a remote JupyterLab or Google Colab shell
    # depending on your platforms' proxy parameters
    gmic.run("sp apples print", images)
    # No image view should pop (the print command only prints textual information?
    # Outputs:
    # [gmic]-1./ Print image [0] = 'apples'.
    # [0] = 'apples':
    #   size = (640,400,1,3) [3000 Kio of floats].
    #   data = (20,22,20,20,20,22,22,22,22,22,22,20,(...),1,1,1,1,1,1,1,1,1,1,1,1).
    #   min = 1, max = 250, mean = 58.5602, std = 59.8916, coords_min = (317,306,0,1), coords_max = (430,135,0,0).
    print(images)
    # Outputs:
    # [<gmic.GmicImage object at 0x7f23fc2f6d30 with _data address at 0x7f23fae17010, w=640 h=400 d=1 s=3 shared=0>]

.. gmicpic:: sp apples

Implementation details
######################
The core tricks of `gmic-py`'s support for IPython-based web-based graphical shells are:

1. for text display (eg. for the `display <https://gmic.eu/tutorial/_display.shtml>`_ and `print <https://gmic.eu/reference.shtml#print>`_ commands: G'MIC standard output redirection towards the IPython user output. For this the `Python wurlitzer cross-platform module <https://github.com/minrk/wurlitzer>`_ has been used and added as a `gmic-py` permanent dependency, leveraging its IPython enabling macro, if an IPython shell is detected.

2. for non-popping G'MIC image display window: transparent replacement of G'MIC `display <https://gmic.eu/tutorial/_display.shtml>`_ command calls into `output <https://gmic.eu/reference.shtml#output>`_ calls as `PNG` format into your (or the host) computer's temporary directory, followed by IPython or Matplotlib display calls. For this, a pure C/Python simple adaptor code has been added.

For desktop UI implementations such as `Jupyter QtConsole <https://jupyter.org/qtconsole/stable/>`_, since your operating systems' `DISPLAY` environment variable is set, above point 1. is still relevant, but the G'MIC native display will probably pop up instead of the `PNG` trick.

The Jupyter support in `gmic-py` can be disabled before module compilation by unsetting the `gmic_py_jupyter_ipython_display` compiler variable. See `setup.py <https://github.com/myselfhimself/gmic-py/blob/13c3b72f1de2f759bc830a048f24bf55b11c3d0e/setup.py#L32>`_.
