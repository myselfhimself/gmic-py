set -x
pip install twine
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmcCJGE0M2VjNGQ1LWIxNjYtNGU3Yy1iYTliLTgwNTU3ZjA2MDY5YwACNXsicGVybWlzc2lvbnMiOiB7InByb2plY3RzIjogWyJnbWljIl19LCAidmVyc2lvbiI6IDF9AAAGIMGxJOG-7GYZAKfYWozw0gq5wtTRxUWSSd605rMOj53-
export TWINE_REPOSITORY_URL=https://upload.pypi.org/legacy/
TWINE=twine

# Do not reupload same-version wheels our source archives
#TWINE_OPTIONS="--skip-existing --verbose"
TWINE_OPTIONS="--verbose"

echo "TWINE UPLOAD STEP: Contents of dist/ and wheelhouse directories are:"
find dist/
find *wheel*

# Upload sdist source tar.gz archive if found
if [ -d "dist/" ]; then
  for a in `ls dist/*.tar.gz`; do
    $TWINE upload $a $TWINE_OPTIONS
  done
fi

# Upload binary python wheels if found
if [ -d "wheelhouse/" ]; then
  for a in `ls wheelhouse/ | grep -E 'manylinux|macosx'`; do
    $TWINE upload $a $TWINE_OPTIONS
  done
fi
