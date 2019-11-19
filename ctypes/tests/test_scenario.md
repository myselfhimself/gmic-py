# Test Driven Development testing scenario
## Vision
Test pip download, installation and simple use of Python G'MIC library on an Ubuntu/Python 3 OS

## Testing steps
Those testing steps are to be scripted first, they will fail less and less:
1. Create a Python3/Debian Docker image
1. Pip install from Github URL
1. Copy some pictures onto image
1. Copy some testing script image that imports the gmic-py library and runs a simple task using pictures
1. Run the script, monitor results
