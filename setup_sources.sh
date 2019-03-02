#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${DIR}/build/env

DOCKER=false
DOWNLOAD=false
VERBOSE=false
DIRS=()

function usage()
{
    echo "Usage: ./setup_sources.sh [OPTIONS]"
    echo "Setup git annex sources."
    echo
    echo "Optional options:"
    echo "  -D         Setup sources using docker"
    echo "  -d         Download sources"
    echo "  -v         Be verbose"
    echo "  -h         Show usage"
}

function parse_options()
{
	local OPTIND=1
	local ORIG_ARGV
	local opt
    while getopts "Ddvh" opt; do
        case "$opt" in
        D)
            DOCKER=true
            ;;
        d)
            DOWNLOAD=true
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

DOCKER_ARGS=""
if $DOWNLOAD; then
    DOCKER_ARGS="-d"
fi
if $VERBOSE; then
    DOCKER_ARGS="${DOCKER_ARGS} -v"
    set -x
fi

if $DOCKER; then
    docker run -it \
    -v $(pwd):/ondemand-packaging \
    -e "OOD_UID=`/usr/bin/id -u`" \
    -e "OOD_GID=`/usr/bin/id -g`" \
    $BUILDBOX_IMAGE \
    /ondemand-packaging/build/inituidgid.sh \
    /ondemand-packaging/build/setuser ood \
    /ondemand-packaging/setup_sources.sh $DOCKER_ARGS
    exit $?
fi

cd $DIR

for dir in "${DIRS[@]}"; do
    for spec in $dir/*.spec; do
        d=$(dirname $spec)
        existing=()
        for link in `find $d -type l`; do
            linkbase=$(basename "$link")
            existing+=("$linkbase")
        done
        sources=()
        for source in $(spectool --list-files $spec | awk '{print $2}'); do
            sources+=("$source")
        done
        for exist in "${existing[@]}"; do
            remove=true
            for source in "${sources[@]}"; do
                sourcebase=$(basename "$source")
                if [ "$exist" = "$sourcebase" ]; then
                    remove=false
                fi
            done
            if $remove; then
                git annex drop $d/$exist
                git rm $d/$exist
            fi
        done
        for source in "${sources[@]}"; do
            sourcebase=$(basename "$source")
            if [ ! -h $d/$sourcebase ]; then
                if $DOWNLOAD; then
                    spectool -g -C $d -S $spec
                fi
            fi
            git annex whereis "$d/$sourcebase" 2>/dev/null | grep -q " web:" && continue
            git annex addurl --file "$d/$sourcebase" "$source"
            git add "$d/$sourcebase"
        done
    done
done
