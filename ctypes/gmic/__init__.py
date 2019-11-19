from ctypes import *
def run(somestring):
    so = cdll.LoadLibrary("/tmp/libcgmic.so")
    so.gmic_call(somestring.encode(), None, None, None)
