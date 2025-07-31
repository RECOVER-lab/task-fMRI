#!/bin/bash

IMAGE=$(jq -r '.custom["gear-builder"].image' manifest.json)
CURDIR=$(pwd)
BASEDIR=$(dirname "$CURDIR")

# Command:
docker run --rm -it --entrypoint='/bin/bash'\
	--gpus "device=${GPU:0}" \
	-e FLYWHEEL=/flywheel/v0\
        -v /home/holder/.config/flywheel:/root/.config/flywheel \
	-v ${BASEDIR}/input:/flywheel/v0/input \
	-v ${BASEDIR}/fsl-6.0.7.1:/opt/fsl-6.0.7.1 \
	-v ${BASEDIR}/output:/flywheel/v0/output\
	$IMAGE

