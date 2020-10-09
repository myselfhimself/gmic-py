import os

import pytest
import gmic
import numpy

from test_gmic_py import (
    gmic_instance_types,
    assert_gmic_images_are_identical,
    assert_non_empty_file_exists,
)


def test_toolkit_gmic_from_scikit():
    from skimage import data, io, filters
    from skimage.data import download_all

    download_all()  # grabbing more data for proper 3d conversion testing

    image = data.lfw_subset()
    print(image.shape)
    print(image)
    io.imshow(image)
    io.show()

    # skimage shape is (height, width, spectrum)
    # gmic will flip them

    gi = gmic.GmicImage.from_numpy_array(image, deinterleave=True)
    gmic.run("display", gi)


def test_toolkit_gmic_to_scikit():
    pass

def test_toolkit_to_numpy_no_preset_interleave():
    import struct
    import random
    w = 5
    h = 4
    d = 3
    c = 2 #eg. just red and green
    nb_floats = w*h*d*c
    c0 = list(range(w*h*d)) # color1 range in [0:126]
    c1 = list(range(127,127+w*h*d)) # color2 range in [127:255]
    print(len(c1)+len(c0))
    gmic_image_buffer = struct.pack('{}f'.format(nb_floats), *tuple(c0 + c1))
    non_interleaved_gmicimage = gmic.GmicImage(gmic_image_buffer, w,h,d,c)
    for x in range(w):
        for y in range(h):
            for z in range(d):
                # ensure we have built a properly deinterleaved G'MIC image
                assert 0 <= non_interleaved_gmicimage(x,y,z,0) < 128
                assert 126 < non_interleaved_gmicimage(x,y,z,1) < 255

    untouched_interleaving_numpy_array = non_interleaved_gmicimage.to_numpy_array(interleave=False)
    # ensure shape is not altered
    assert untouched_interleaving_numpy_array.shape == (w,h,d,c)
    assert untouched_interleaving_numpy_array.dtype == numpy.float32
    for x in range(w):
        for y in range(h):
            for z in range(d):
                # Ensure the G'MIC to numpy conversion without interleaving keeps same array values order
                assert 0 <= untouched_interleaving_numpy_array[x,y,z,0] < 128
                assert 255 < untouched_interleaving_numpy_array[x,y,z,1] > 127

    interleaved_numpy_array = non_interleaved_gmicimage.to_numpy_array()
    assert interleaved_numpy_array == non_interleaved_gmicimage.to_numpy_array(interleave=False)
    assert interleaved_numpy_array.shape == (w,h,d,c)
    assert interleaved_numpy_array.dtype == numpy.float32
    for x in range(w):
        for y in range(h):
            for z in range(d):
                assert 0 <= untouched_interleaving_numpy_array[x,y,z][0] < 128
                assert 255 < non_interleaved_gmicimage[x,y,z][1] > 127

def test_toolkit_to_numpy_no_preset_no_deinterleave():
    pass

def test_toolkit_to_numpy_with_gmic_preset():
    pass

def test_toolkit_from_numpy_with_gmic_preset():
    pass


# TODO remove this
if __name__ == "__main__":
    test_toolkit_gmic_from_scikit()
