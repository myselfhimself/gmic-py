# TEST 2: numpy(deinterleaved)->gmic_from_nparray(deinterleaved)->gmic_display(deinterleaved)
import gmic
import PIL
import PIL.Image
from numpy import asarray, array_equal

gmic.run("sp duck output image.png")
i = PIL.Image.open("image.png")
ii = asarray(i)
print(ii.shape)  # (512, 512, 3)
print(ii.dtype)  # uint8

l = []
gmic.run("sp duck", l)
ll = l[0].to_numpy_array(
    interleave=False, astype=int, squeeze_shape=True
)  # default astype=float32, default squeeze_shape=True
print(ll.shape)  # (512, 512, 3)
print(ll.dtype)  # int64
array_equal(
    ll, ii
)  # False; uint8 vs. int64 match but deinterleave vs interleave unmatch

j = gmic.GmicImage.from_numpy_array(ll, deinterleave=False)
gmic.run("display", j)  # Good orientation, color, size
"""
[gmic]-1./ Display image [0] = '[unnamed]', from point (256,256,0).
[0] = '[unnamed]':
  size = (512,512,1,3) [3072 Kio of floats].
  data = (225,225,223,223,225,225,225,223,225,223,223,223,(...),78,78,78,77,91,80,79,89,77,79,79,82).
  min = 8, max = 251, mean = 128.241, std = 58.9512, coords_min = (457,60,0,1), coords_max = (425,20,0,0).
"""

jj = gmic.GmicImage.from_numpy_array(ii, deinterleave=True)
gmic.run("display", jj)  # Good orientation, color, size
"""
[gmic]-1./ Display image [0] = '[unnamed]', from point (256,256,0).
[0] = '[unnamed]':
  size = (512,512,1,3) [3072 Kio of floats].
  data = (225,225,223,223,225,225,225,223,225,223,223,223,(...),78,78,78,77,91,80,79,89,77,79,79,82).
  min = 8, max = 251, mean = 128.241, std = 58.9512, coords_min = (457,60,0,1), coords_max = (425,20,0,0).
"""
