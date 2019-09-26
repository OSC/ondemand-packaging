#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${DIR}/../build/env

REPO="oodpkg@repo.hpc.osc.edu:/var/www/repos/public/ondemand/build"
PKEY="~/.ssh/id_rsa"
VERBOSE=false

function usage()
{
    echo "Usage: ./make-mock-cache.sh [OPTIONS]"
    echo "Generate and upload mock cache."
    echo
    echo "Optional options:"
    echo "  -R         SCP repo destination (default: $REPO)"
    echo "  -p         SSH private key for repo destination (default: $PKEY)"
    echo "  -v         Be verbose"
    echo "  -h         Show usage"
}

function parse_options()
{
	local OPTIND=1
	local ORIG_ARGV
	local opt
    while getopts "R:p:vh" opt; do
        case "$opt" in
        R)
            REPO="$OPTARG"
            ;;
        p)
            PKEY="$OPTARG"
            ;;
        v)
            VERBOSE=true
            ;;
        h)
            usage
            exit
            ;;
        *)
            return 1
            ;;
        esac
	done

	(( OPTIND -= 1 )) || true
	shift $OPTIND || true
	ORIG_ARGV=("$@")

    if [ $# -gt 0 ]; then
        DIRS=($@)
    else
        for c in compute web-nonscl web; do
            for d in ${c}/*; do
                DIRS+=("$d")
            done
        done
    fi
}

parse_options "$@"

if $VERBOSE; then
    set -x
fi

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
mock -r epel-8-x86_64 --no-cleanup-after --init

docker exec \
-t -i \
-e "LC_CTYPE=en_US.UTF-8" \
$CONTAINER_ID \
mock -r epel-7-x86_64 --no-cleanup-after --init

docker exec \
-t -i \
-e "LC_CTYPE=en_US.UTF-8" \
$CONTAINER_ID \
tar czf /build/$MOCK_CACHE /var/lib/mock

docker kill $CONTAINER_ID

scp -i $PKEY ./$MOCK_CACHE $REPO/$MOCK_CACHE && rm -f $MOCK_CACHE
