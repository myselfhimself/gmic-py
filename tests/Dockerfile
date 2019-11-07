FROM python:3

ADD simple_python_script.py /
ADD requirements.txt /
RUN [ "pip", "install", "-r", "requirements.txt" ]
CMD [ "py.test", "-v", "."]
