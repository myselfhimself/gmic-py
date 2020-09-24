# See accompanying tutorial https://discuss.pixls.us/t/developing-and-fiddling-with-the-gmic-python-binding/20406/2
import gmic

gmic.run('200,200,1,3 text "HELLO WORLD",50%,50%,13,1,255,147,23 display')

# Use the 'output' command for outputting to a file
gmic.run('200,200,1,3 text "HELLO WORLD",50%,50%,13,1,255,147,23 output helloworld.png')
