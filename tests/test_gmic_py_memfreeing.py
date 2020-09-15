import pytest
import numpy
import psutil

import struct
import sys


@pytest.fixture
def p():
    return psutil.Process()


def test_freeing_gmic_module(p):
    pp = p.memory_percent()
    import gmic

    assert sys.getrefcount(gmic) == 2
    pp2 = p.memory_percent()
    assert (pp2 - pp) / pp > 0.06  # >6 % memory increase
    del gmic
    pp3 = p.memory_percent()
    assert abs(pp3 - pp) < 0.02  # < 0.02 percent points memory variation
    print(pp, pp2, pp3)


def test_freeing_numpy_array(p):
    pp = p.memory_percent()
    a = numpy.full((400, 500, 300, 3), 4.5, numpy.float32)
    assert sys.getrefcount(a) == 2
    pp2 = p.memory_percent()
    assert (pp2 - pp) / pp > 4  # >400 % memory increase
    del a
    pp3 = p.memory_percent()
    assert abs(pp3 - pp) < 0.02  # < 0.02 percent points memory variation
    print(pp, pp2, pp3)


def test_freeing_gmic_image(p):
    import gmic

    pp = p.memory_percent()
    a = gmic.GmicImage(
        struct.pack(*(("180000000f",) + (4.5,) * 180000000)), 400, 500, 300, 3
    )
    assert sys.getrefcount(a) == 2
    pp2 = p.memory_percent()
    assert (pp2 - pp) / pp > 4  # >400 % memory increase
    del a
    pp3 = p.memory_percent()
    assert abs(pp3 - pp) < 0.02  # < 0.02 percent points memory variation
    print(pp, pp2, pp3)


def test_freeing_gmic_interpreter(p):
    import gmic

    pp = p.memory_percent()
    a = gmic.Gmic()
    assert sys.getrefcount(a) == 2
    pp2 = p.memory_percent()
    assert (pp2 - pp) / pp > 0.06  # >6 % memory increase
    del a
    pp3 = p.memory_percent()
    assert abs(pp3 - pp) < 0.02  # < 0.02 percent points memory variation
    print(pp, pp2, pp3)
