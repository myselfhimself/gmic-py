$PIP3 install wheel || (echo "Fatal wheel package install error" && exit 1)
$PYTHON3 setup.py bdist_wheel || (echo "Fatal wheel build error" && exit 1)
echo "Not doing any auditwheel repair step here, development environment :)"
