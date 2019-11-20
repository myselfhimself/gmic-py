#!/bin/sh

COMPILE_COMMAND="g++ -fPIC gmicpy.cpp -o gmicpy.so -I . -L /usr/lib/i386-linux-gnu/ -L . -lgmic -std=c++11 -shared $INCLUDES $LIBS"

echo WILL COMPILE WITH $COMPILE_COMMAND

$COMPILE_COMMAND
