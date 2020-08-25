import os.path

from docutils import nodes
from docutils.parsers.rst import Directive

import gmic


class GmicPic(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = False
    DIR_NAME = "gmic_images"

    def run(self):
        gmic_command = self.arguments[0]
        input_image = os.path.join(self.DIR_NAME, "earth.png")
        image_node = nodes.image(uri=self.generate_gmic_output(input_image + " blur 4"))
        #paragraph_node = nodes.paragraph(text='Hello World!')
        return [image_node]

    def generate_gmic_output(self, gmic_command):
        output_path = os.path.join(self.DIR_NAME, "hop.png")

        gmic.run(gmic_command + " output " + output_path)
        return output_path 

def setup(app):
    app.add_directive("gmicpic", GmicPic)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
