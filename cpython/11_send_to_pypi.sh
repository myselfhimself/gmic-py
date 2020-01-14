set -x
pip install twine
export TWINE_USERNAME=__token__
export TWINE_PASSWORD="$TWINE_PASSWORD_GITHUB_SECRET" # See: Github Workflow scripts
export TWINE_REPOSITORY_URL=https://upload.pypi.org/legacy/
TWINE=twine

# Do not reupload same-version wheels our source archives
TWINE_OPTIONS="--skip-existing --verbose"

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
  for a in `ls wheelhouse/* | grep -E 'manylinux|macosx'`; do # Keep /* wildcard for proper relative paths!!
    $TWINE upload $a $TWINE_OPTIONS
  done
fi
