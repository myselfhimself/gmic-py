Those three scripts leveraging gmic-py >= 2.9.0, numpy, Pillow and matplotlib showcase the numpy support of gmic-py.
Note that numpy/PIL/Pillow image dimensions (height, width) are naturally flipped with G'MIC's image dimensions (width, height),
because of numpy's algebraic notation tradition.
Note also that G'MIC's GmicImage type encodes images in float32/pixel (or voxel) channel value in a deinterleaved style eg. line1-RRRRGGGGBBBB-line2-RRR...
A video demo of the numpy support at early stages can be found in our [Libre Graphics Meeting 2020 presentation on Youtube here](https://www.youtube.com/watch?v=qbJv7QScs3s).
