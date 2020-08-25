import gmic
from sys import argv
command = "sp {} output {}.png".format(argv[1], argv[1])
print(command)
input("?")
gmic.run(command)
