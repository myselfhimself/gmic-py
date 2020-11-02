import os
import pytest

import gmic
from PIL import Image, ImageDraw


def draw_cross(im):
    draw = ImageDraw.Draw(im)
    draw.line((0, 0) + im.size, fill=128)
    draw.line((0, im.size[1], im.size[0], 0), fill=128)


def make_sample_file(extension):
    filename = "{}_format_io_test.{}".format(extension, extension)

    with open(filename, "w+") as f:
        im = Image.new(mode="RGB", size=(200, 200))
        draw_cross(im)
        im.save(f)

    yield filename

    os.unlink(filename)


@pytest.fixture
def sample_jpg_filename():
    yield make_sample_file("jpg")


@pytest.fixture
def sample_tiff_filename():
    yield make_sample_file("tiff")


@pytest.fixture
def sample_png_filename():
    yield make_sample_file("png")


def test_jpeg_io(sample_jpg_filename):
    pass


def test_png_io(sample_png_filename):
    pass


def test_tiff_io(sample_tiff_filename):
    pass
