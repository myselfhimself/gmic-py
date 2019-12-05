$PIP3 install twine
for a in `ls dist`; do
  $PYTHON3 -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/$a --verbose
done
