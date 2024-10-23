#!/bin/bash
PATH_PROJECT=$1
PYDEFACE_VERSION=37-2e0c2d
for FILE in ${PATH_PROJECT}/*/anat/*T1w.nii.gz; do
    # get the filename:
	FILE_BASENAME="$(basename -- $FILE)"
    # get the parent directory:
	FILE_PARENT="$(dirname "$FILE")"
    # run defacing:
    docker run --rm -v ${FILE_PARENT}:/input:rw  poldracklab/pydeface:${PYDEFACE_VERSION} \
        pydeface /input/${FILE_BASENAME} --force
done