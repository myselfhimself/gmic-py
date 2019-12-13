pip install twine
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmcCJGE0M2VjNGQ1LWIxNjYtNGU3Yy1iYTliLTgwNTU3ZjA2MDY5YwACNXsicGVybWlzc2lvbnMiOiB7InByb2plY3RzIjogWyJnbWljIl19LCAidmVyc2lvbiI6IDF9AAAGIMGxJOG-7GYZAKfYWozw0gq5wtTRxUWSSd605rMOj53-
export TWINE_REPOSITORY_URL=https://upload.pypi.org/legacy/
TWINE=twine

if [ -d "dist/" ]; then
  for a in `ls dist/`; do
    $TWINE upload $a
  done
fi

if [ -d "wheelhouse/" ]; then
  for a in `ls wheelhouse/*manylinux*`; do
    $TWINE upload $a
  done
fi

