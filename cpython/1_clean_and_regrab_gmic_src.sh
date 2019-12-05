GMIC_VERSION=2.8.1
GMIC_URL=https://gmic.eu/files/prerelease/gmic_2.8.1_pre191205.tar.gz
GMIC_ARCHIVE_NAME=gmic_2.8.1_pre191205.tar.gz
#GMIC_ARCHIVE_NAME=gmic_${GMIC_VERSION}.tar.gz
#GMIC_URL=https://gmic.eu/files/source/gmic_${GMIC_VERSION}.tar.gz
rm -rf dist/
rm -rf src/
mkdir src -p
$PYTHON3 setup.py clean --all
wget ${GMIC_URL} -P src/ --no-check-certificate
tar xzvf src/${GMIC_ARCHIVE_NAME} -C src/
# Keep only gmic source's src directory
cd src/gmic*/
rm -rf $(ls | grep -v src)
cd src
ls | grep -vE "gmic\.cpp|gmic\.h|gmic_stdlib\.h|CImg\.h" | xargs rm -rf
ls
cd ../..
rm -f gmic_${GMIC_VERSION}.tar.gz*
mv gmic-${GMIC_VERSION}*/ gmic
cd ..
