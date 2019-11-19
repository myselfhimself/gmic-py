echo WILL COMPILE WITH g++ gmicpy.cpp -o gmicpy.so -I . -L /usr/lib/i386-linux-gnu/ -L . -lgmic -std=c++11 -shared $INCLUDES $LIBS
g++ gmicpy.cpp -o gmicpy.so -I . -L /usr/lib/i386-linux-gnu/ -L . -lgmic -std=c++11 -shared $INCLUDES $LIBS
