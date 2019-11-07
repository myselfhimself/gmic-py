FROM python:3

# The gmic-py package name to install can be overriden with a git URL
# Omit this line to try downloading from PyPI instead
ENV GMIC_PY_PIP_PKG="git+https://github.com/dtschump/gmic-py.git"
# Use the following form or nothing, when gmic lands on PyPI (not yet..)
# ENV GMIC_PY_PIP_PKG="gmic"

ADD test_gmic_install_and_run.py /tmp

ADD requirements.txt /tmp
RUN [ "pip", "install", "-r", "/tmp/requirements.txt" ]

CMD [ "py.test", "-v", "/tmp/" ]
