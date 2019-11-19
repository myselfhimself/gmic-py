g++ gmicpy.cpp -o gmicpy.so -I /usr/include/python3.5m/ -I . -L /usr/lib/i386-linux-gnu/ -L . -lpython3.5m -lgmic -std=c++11 -shared

ln -s libgmic.so libgmic.so.2

LD_LIBRARY_PATH=. ldd gmicpy.so
LD_LIBRARY_PATH=. python3 testgmicpy.py



