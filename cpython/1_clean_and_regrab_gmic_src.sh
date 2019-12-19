set -e
GMIC_VERSION=2.8.1
GMIC_ARCHIVE_NAME=gmic_${GMIC_VERSION}*.tar.gz
GMIC_URL=https://gmic.eu/files/source/gmic_${GMIC_VERSION}.tar.gz
rm -rf dist/
rm -rf src/
mkdir src -p
$PIP3 install -r dev-requirements.txt
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
rm -f ${GMIC_ARCHIVE_NAME}
mv gmic-${GMIC_VERSION}*/ gmic
cd ..
echo
echo "src/ dir now contains fresh gmic source ($GMIC_VERSION):"
find src/
