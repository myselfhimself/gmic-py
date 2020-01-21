set -x
GMIC_VERSION=prerelease
GMIC_ARCHIVE_NAME=gmic_${GMIC_VERSION}*.tar.gz
#GMIC_URL=https://gmic.eu/files/source/gmic_${GMIC_VERSION}.tar.gz
GMIC_URL=https://gmic.eu/files/prerelease/gmic_prerelease.tar.gz
rm -rf dist/
rm -rf src/
mkdir src -p
$PIP3 install -r dev-requirements.txt
$PYTHON3 setup.py clean --all
wget ${GMIC_URL} -P src/ --no-check-certificate || { echo "Fatal gmic src archive download error" ; exit 1; }
tar xzvf src/${GMIC_ARCHIVE_NAME} -C src/ || { echo "Fatal gmic src archive extracting error" ; exit 1; }
# Keep only gmic source's src directory
mv src/gmic*/ src/gmic
cd src/gmic*/
rm -rf $(ls | grep -v src)
cd src
ls | grep -vE "gmic\.cpp|gmic\.h|gmic_stdlib\.h|CImg\.h" | xargs rm -rf
ls
cd ../..
rm -f ${GMIC_ARCHIVE_NAME}
mv gmic-${GMIC_VERSION}*/ gmic
cd ..
echo
echo "src/ dir now contains fresh gmic source ($GMIC_VERSION):"
find src/
