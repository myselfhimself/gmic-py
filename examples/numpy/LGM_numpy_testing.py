import gmic
import PIL
import PIL.Image
import numpy
from numpy import asarray, array_equal
from matplotlib import pyplot

l = []
gmic.run("sp duck", l)
gmic.run("display", l)

ll = l[0].to_numpy_array(interleave=True, astype=numpy.uint8, squeeze_shape=True)
print(ll.shape)
print(ll.dtype)

pyplot.imshow(ll)
pyplot.show()
