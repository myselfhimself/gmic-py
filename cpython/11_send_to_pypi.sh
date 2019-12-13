pip install twine
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmcCJGE0M2VjNGQ1LWIxNjYtNGU3Yy1iYTliLTgwNTU3ZjA2MDY5YwACNXsicGVybWlzc2lvbnMiOiB7InByb2plY3RzIjogWyJnbWljIl19LCAidmVyc2lvbiI6IDF9AAAGIMGxJOG-7GYZAKfYWozw0gq5wtTRxUWSSd605rMOj53-
export TWINE_REPOSITORY_URL=https://upload.pypi.org/legacy/
TWINE=twine

[ -d "dist/" ] && $TWINE upload dist/*
[ -d "wheelhouse/" ] && $TWINE upload wheelhouse/*manylinux*

