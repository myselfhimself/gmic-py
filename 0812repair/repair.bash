#!/bin/bash

set -x
OUTPUTDIR=$(readlink -f .)
TEMPDIR=$(readlink -f out)
DISTINFODIR="gmic-2.9.1a5.dist-info"
LIBSPATH=$TEMPDIR
EXCLUDEFILEPATH=/tmp/exclude-list-gmic
PIP3=${PIP3:-pip}
PYTHON3=${PYTHON3:-python}
PYARCH="cp$($PYTHON3 --version | sed -e 's/[a-z .]*//gi' | cut -c1-2)"

cat >$EXCLUDEFILEPATH <<EOL
libgcc_s.so.1
libstdc++.so.6
libm.so.6
libdl.so.2
librt.so.1
libc.so.6
libnsl.so.1
libutil.so.1
libpthread.so.0
libresolv.so.2
libX11.so.6
libXext.so.6
libXrender.so.1
libICE.so.6
libSM.so.6
libGL.so.1
libgobject-2.0.so.0
libgthread-2.0.so.0
libglib-2.0.so.0
EOL

test $# -lt 1 && echo "Usage: $0 somearchive.whl [libspath override (default:gmic.libs)]" && exit 1
test -z $(which copydeps) && $PIP3 install copydeps
COPYDEPS=$($PYTHON3 -c "import copydeps; print(copydeps.__spec__.origin)")
rm -rf $TEMPDIR
mkdir -p $TEMPDIR
unzip $1 -d $TEMPDIR
cd $TEMPDIR
echo TEMPDIR\'s CONTENTS:
ls -lhart
if ! test -z $2; then
   LIBSPATH=$TEMPDIR/$2
   echo LIBSPATH changed to: $LIBSPATH
fi
test ! -d $LIBSPATH && echo Error: could not find LIBSPATH: $LIBSPATH && exit 1 
cd $LIBSPATH
for so in $(ls *.so); do
#copydeps gmic.cpython-37m-x86_64-linux-gnu.so --exclude exclude-list-gmic --dot foo.dot -d .
    $PYTHON3 $COPYDEPS $so --exclude $EXCLUDEFILEPATH -d .
done
cd $TEMPDIR
find -type f | sed 's/\.\///g' | xargs -IAAA sh -c "sha256sum AAA | cut -d' ' -f1; ls -s AAA" | xargs -n 3 | awk '{ print $3",sha256="$1","$2 }' | grep -v RECORD > *.dist-info/RECORD
echo "$DISTINFODIR/RECORD,," >> *.dist-info/RECORD
cat >$DISTINFODIR/WHEEL <<EOF
Wheel-Version: 1.0
Generator: bdist_wheel (0.36.1)
Root-Is-Purelib: false
Tag: $PYARCH-${PYARCH}m-manylinux2014_x86_64
EOF

ls
zip $1_repaired * -r
mv $1_repaired $OUTPUTDIR
cd $OUTPUTDIR
ls -lhart $1_repaired
set +x
