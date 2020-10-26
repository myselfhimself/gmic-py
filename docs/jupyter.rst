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

    !pip install gmic # or gmic==2.9.1-alpha5


Implementation details
######################
The core tricks of `gmic-py`'s support for IPython-based web-based graphical shells are:

1. for text display (eg. for the `display <https://gmic.eu/tutorial/_display.shtml>`_ and `print <https://gmic.eu/reference.shtml#print>`_ commands: G'MIC standard output redirection towards the IPython user output. For this the `Python wurlitzer cross-platform module <https://github.com/minrk/wurlitzer>`_ has been used and added as a `gmic-py` permanent dependency, leveraging its IPython enabling macro, if an IPython shell is detected.

2. for non-popping G'MIC image display window: transparent replacement of G'MIC `display <https://gmic.eu/tutorial/_display.shtml>`_ command calls into `output <https://gmic.eu/reference.shtml#output>`_ calls as `PNG` format into your (or the host) computer's temporary directory, followed by IPython or Matplotlib display calls. For this, a pure C/Python simple adaptor code has been added.

The Jupyter support in `gmic-py` can be disabled before module compilation by unsetting the `gmic_py_jupyter_ipython_display` compiler variable. See `setup.py <https://github.com/myselfhimself/gmic-py/blob/13c3b72f1de2f759bc830a048f24bf55b11c3d0e/setup.py#L32>`_.


