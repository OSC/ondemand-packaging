#!/bin/bash

RELEASE="$1"
TARGET="$2"

if [ -z "$RELEASE" ]; then
    echo "Must specify release"
    exit 1
fi

if [[ "$TARGET" == "public" ]]; then
    basedir="/var/www/repos/public/ood"
elif [[ "$TARGET" == "internal" ]]; then
    basedir="/var/www/repos/internal/osc-ondemand"
else
    echo "Target must be public or internal"
    exit 1
fi

TYPES=(web compute)
DISTS=(el6 el7)
ARCHES=(SRPMS x86_64)

for t in "${TYPES[@]}"; do
    for d in "${DISTS[@]}"; do
        for a in "${ARCHES[@]}"; do
            dir=${basedir}/${RELEASE}/${t}/${d}/${a}
            mkdir -p $dir
            chown mirror:mirror $dir
        done
    done
done
