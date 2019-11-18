FROM python:3

# The gmic-py package name to install can be overriden with a git URL
# Omit this line to try downloading from PyPI instead
ENV GMIC_PY_PIP_PKG="git+https://github.com/dtschump/gmic-py.git"
# Use the following form or nothing, when gmic lands on PyPI (not yet..)
# ENV GMIC_PY_PIP_PKG="gmic"

# Install dependency for compiling libgmic
RUN apt-get update; apt-get install -y libfftw3-dev

ADD test_gmic_install_and_run.py /tmp

ADD requirements.txt /tmp
ADD makecustomgmic.sh /tmp

RUN git clone --depth 1 -b master https://github.com/dtschump/gmic.git /tmp/gmic-src
RUN cd /tmp/gmic-src/src ; . /tmp/makecustomgmic.sh
RUN ls /tmp/gmic-src/src/
RUN cp /tmp/gmic-src/src/libcgmic.so /tmp
RUN ls /tmp

ENV LD_LIBRARY_PATH "${LD_LIBRARY_PATH}:/tmp:/usr/local/lib:/usr/lib/i386-linux-gnu/:/usr/lib/x86_64-linux-gnu/"
RUN ldd /tmp/libcgmic.so
RUN pip install pytest
RUN pip install -r /tmp/requirements.txt

CMD [ "py.test", "-v", "/tmp/" ]
