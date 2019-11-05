#!/bin/sh

docker build -t gmic-py-test-scenario .
docker run gmic-py-test-scenario
