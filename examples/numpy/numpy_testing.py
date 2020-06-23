# TEST 1: numpy(interleaved)->pyplot_display(interleaved)->gmic_from_nparray(deinterleaved)->gmic_display(deinterleaved)
import gmic

print(gmic.__spec__)
import PIL
import PIL.Image
import numpy
from numpy import asarray, array_equal
from matplotlib import pyplot

gmic.run("sp duck output image.png")
i = PIL.Image.open("image.png")  # Duck sample
ii = asarray(i)
print(ii.shape)  # (512, 512, 3)
print(ii.dtype)  # uint8

l = []
gmic.run("sp duck", l)
ll = l[0].to_numpy_array(interleave=True, astype=numpy.uint8, squeeze_shape=True)
array_equal(ll, ii)  # True
print(ll.shape)  # (512, 512, 3)
print(ll.dtype)  # uint8

pyplot.imshow(ll)
pyplot.show()  # Good colors, dimensions and orientation

pyplot.imshow(ii)
pyplot.show()  # Good colors, dimensions and orientation

j = gmic.GmicImage.from_numpy_array(ll, deinterleave=True)
gmic.run("display", j)  # Good colors, dimensions and orientation
"""
[gmic]-1./ Display image [0] = '[unnamed]', from point (256,256,0).
[0] = '[unnamed]':
  size = (512,512,1,3) [3072 Kio of floats].
  data = (225,225,223,223,225,225,225,223,225,223,223,223,(...),78,78,78,77,91,80,79,89,77,79,79,82).
  min = 8, max = 251, mean = 128.241, std = 58.9512, coords_min = (457,60,0,1), coords_max = (425,20,0,0).
"""

jj = gmic.GmicImage.from_numpy_array(ii, deinterleave=True)
gmic.run("display", jj)  # Good colors, dimensions and orientation
"""
[gmic]-1./ Display image [0] = '[unnamed]', from point (256,256,0).
[0] = '[unnamed]':
  size = (512,512,1,3) [3072 Kio of floats].
  data = (225,225,223,223,225,225,225,223,225,223,223,223,(...),78,78,78,77,91,80,79,89,77,79,79,82).
  min = 8, max = 251, mean = 128.241, std = 58.9512, coords_min = (457,60,0,1), coords_max = (425,20,0,0).
"""
