# Run this from the cpython/ directory only :)
DOCKER_IMAGE="quay.io/pypa/manylinux1_x86_64"
PLAT="manylinux1_x86_64"
PRE_CMD=

docker pull $DOCKER_IMAGE
docker run --rm -e PLAT=$PLAT -v `pwd`:/io $DOCKER_IMAGE find /io
docker run --rm -e PLAT=$PLAT -v `pwd`:/io $DOCKER_IMAGE $PRE_CMD /bin/bash /io/travis/build-wheels.sh
ls wheelhouse/
