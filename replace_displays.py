import gmic
import tempfile
import uuid
import os
import re
import glob


commands_line = "sp lena sp leno display blur 4 display"
commands_line_with_outputs = ""
debug_commands = ""

last_pos = 0
tempdir = tempfile.gettempdir()
prefixes = []
for x in re.finditer('display', commands_line):
    last_prefix = os.path.join(tempdir, str(uuid.uuid1()) + ".png")
    last_prefix_glob = last_prefix.replace('.png', '_*.png')
    prefixes.append(last_prefix_glob)
    commands_line_with_outputs += commands_line[last_pos: x.start()] + "output " + last_prefix
    last_pos = x.end()

gmic.run(commands_line_with_outputs)

files_batches = []
for prefix in prefixes:
    files_batch = glob.glob(prefix)
    print("hey",files_batch,prefix)
    files = " ".join(files_batch)
    files_batches.append(files_batch)
    debug_commands += files + " display "

print(commands_line_with_outputs)
print(files_batches)

print(debug_commands)
for i in files_batches:
    gmic.run(" ".join(i) + " display")

files_batches
