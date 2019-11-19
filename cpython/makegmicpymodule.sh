g++ gmicpy.cpp -o gmicpy.so -I . -L /usr/lib/i386-linux-gnu/ -L . -lgmic -std=c++11 -shared $INCLUDES $LIBS

ln -s libgmic.so libgmic.so.2

LD_LIBRARY_PATH=. ldd gmicpy.so
LD_LIBRARY_PATH=. python3 testgmicpy.py



