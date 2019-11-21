import sys
print(sys.path)
import os
print(os.environ)

import gmicpy
print(gmicpy)

gmicpy.run('echo_stdout "hello world"')

png_filename = "a.png"
gmicpy.run('input "(0,128,255)" -output ' + png_filename)
a_png = pathlib.Path(png_filename)
