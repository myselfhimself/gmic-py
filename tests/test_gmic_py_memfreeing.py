import pytest
import numpy
import psutil

import os
import struct
import sys


@pytest.fixture
def p():
    return psutil.Process()


@pytest.fixture
def gmicpylog():
    os.environ["GMIC_PY_DEBUG"] = "1"
    yield
    del os.environ["GMIC_PY_DEBUG"]


def test_freeing_gmic_module(p):
    pp = p.memory_percent()
    import gmic

    assert sys.getrefcount(gmic) in (7, 5)  # numpy has getrefcount=41!!
    pp2 = p.memory_percent()
    assert (pp2 - pp) / pp < 1.3  # <130 % memory increase
    del gmic
    pp3 = p.memory_percent()
    print(pp, pp2, pp3)
    assert (pp3 - pp) / pp < 1.3  # <130 % memory decrease


def test_freeing_numpy_array(p):
    pp = p.memory_percent()
    a = numpy.full((400, 500, 300, 3), 4.5, numpy.float32)
    assert sys.getrefcount(a) == 2
    pp2 = p.memory_percent()
    assert (pp2 - pp) / pp > 4  # >400 % memory increase
    del a
    pp3 = p.memory_percent()
    print(pp, pp2, pp3)
    assert pp3 - pp < 0.04  # < +4 percent points memory variation


def test_freeing_gmic_image(p, gmicpylog, capfd):
    # observe memory variation + proper tp_alloc and tp_dealloc calling
    import gmic

    pp = p.memory_percent()

    a = gmic.GmicImage(
        struct.pack(*(("180000000f",) + (4.5,) * 180000000)), 400, 500, 300, 3
    )

    outerr = capfd.readouterr()
    # assert "PyGmicImage_alloc\n" == outerr.out

    assert sys.getrefcount(a) == 2
    pp2 = p.memory_percent()
    # assert (pp2 - pp) / pp > 4  # >400 % memory increase

    del a
    outerr = capfd.readouterr()
    # assert "PyGmicImage_dealloc\n" == outerr.out

    pp3 = p.memory_percent()
    print(pp, pp2, pp3)
    # assert pp3 - pp <= 0.04 # < +4 percent points memory variation


def test_freeing_gmic_interpreter(p, gmicpylog, capfd):
    # even though PyGmic.tp_dealloc gets called, it seems impossible to measure freed memory here
    import gmic

    pp = p.memory_percent()
    a = gmic.Gmic()

    outerr = capfd.readouterr()
    # assert "PyGmic_alloc\n" == outerr.out

    assert sys.getrefcount(a) == 2
    pp2 = p.memory_percent()
    assert (pp2 - pp) / pp > 0.005 and (
        pp2 - pp
    ) / pp < 0.2  # >0.5 % <20 % memory variation
    del a

    outerr = capfd.readouterr()
    # assert "PyGmic_dealloc\n" == outerr.out

    pp3 = p.memory_percent()
    print(pp, pp2, pp3)
    assert pp3 - pp < 0.25  # < +25 percent points memory variation
