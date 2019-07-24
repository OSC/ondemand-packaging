#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${DIR}/../build/env

CONTAINER_ID=$(docker run \
--detach --rm \
--privileged \
--cap-add=SYS_ADMIN \
-v "${DIR}:/build:rw" \
$BUILDBOX_IMAGE \
/usr/sbin/init)

docker exec \
-t -i \
-e "LC_CTYPE=en_US.UTF-8" \
$CONTAINER_ID \
mock -r epel-7-x86_64 --init

docker exec \
-t -i \
-e "LC_CTYPE=en_US.UTF-8" \
$CONTAINER_ID \
mock -r epel-6-x86_64 --init

docker exec \
-t -i \
-e "LC_CTYPE=en_US.UTF-8" \
$CONTAINER_ID \
tar czf /build/mock-cache.tar.gz /var/cache/mock

docker kill $CONTAINER_ID
