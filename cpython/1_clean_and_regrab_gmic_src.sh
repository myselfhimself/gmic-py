GMIC_VERSION=2.8.0
rm -rf dist/
rm -rf src/
mkdir src -p
python3 setup.py clean --all
wget https://gmic.eu/files/source/gmic_${GMIC_VERSION}.tar.gz -P src/
tar xzvf src/gmic_${GMIC_VERSION}.tar.gz -C src/
# Keep only gmic source's src directory
cd src/gmic*/
rm -rf $(ls | grep -v src)
cd src
ls | grep -vE "gmic\.cpp|gmic\.h|gmic_stdlib\.h|CImg\.h" | xargs rm -rf
ls
cd ../..
rm -f gmic_${GMIC_VERSION}.tar.gz*
mv gmic-${GMIC_VERSION} gmic
cd ..
