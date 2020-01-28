# This is a ubuntu/debian distribution 
FROM python:3

# Install dependency for compiling libgmic
RUN apt-get update; apt-get install -y libfftw3-dev libcurl4-openssl-dev libpng-dev zlib1g-dev libomp-dev
ENV PYTHON3 python3
ENV PIP3 pip3

RUN mkdir -p /tmp/tests
COPY ./tests/. /tmp/tests/
RUN ls /tmp/tests/

ADD VERSION /tmp/
ADD dev-requirements.txt /tmp/
ADD *.sh /tmp/
RUN ls /tmp
ADD *.cpp /tmp/
ADD *.py /tmp/
ADD *.in /tmp/
ADD *.cfg /tmp/
ADD *.md /tmp/

RUN ls /tmp
WORKDIR /tmp
RUN ls
CMD [ "bash", "00_all_steps.sh" ]
