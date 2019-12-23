# Run this from the cpython/ directory only :)

# Feel free to preset the following variables before running this script
# Default values allow for local running on a developer machine :)
if [ -z "$DOCKER_IMAGE" ]
then
  DOCKER_IMAGE="quay.io/pypa/manylinux1_x86_64"
fi
if [ -z "$PLAT" ]
then
  PLAT="manylinux1_x86_64"
fi
if [ -z "$PRE_CMD" ]
then
  PRE_CMD=
fi

docker pull $DOCKER_IMAGE
docker run --rm -e PLAT=$PLAT -v `pwd`:/io $DOCKER_IMAGE find /io
docker run --rm -e PLAT=$PLAT -v `pwd`:/io $DOCKER_IMAGE $PRE_CMD /bin/bash /io/manylinux/build-wheels.sh
ls wheelhouse/
