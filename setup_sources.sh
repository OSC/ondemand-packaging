#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${DIR}/build/env

DOCKER=false

function usage()
{
    echo "Usage: ./setup_sources.sh [OPTIONS]"
    echo "Setup git annex sources."
    echo
    echo "Optional options:"
    echo "  -D         Setup sources using docker"
    echo "  -h         Show usage"
}

function parse_options()
{
	local OPTIND=1
	local ORIG_ARGV
	local opt
    while getopts "Dh" opt; do
        case "$opt" in
        D)
            DOCKER=true
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
}

parse_options "$@"

if $DOCKER; then
    docker run -it \
    -v $(pwd):/ondemand-packaging \
    -e "OOD_UID=`/usr/bin/id -u`" \
    -e "OOD_GID=`/usr/bin/id -g`" \
    $BUILDBOX_IMAGE \
    /ondemand-packaging/build/inituidgid.sh \
    /ondemand-packaging/build/setuser ood \
    /ondemand-packaging/setup_sources.sh
    exit $?
fi

cd $DIR

if [ $# -gt 0 ]; then
    dirs=($@)
else
    specs=()
    for c in compute web-nonscl web; do
        for d in ${c}/*; do
            dirs+=("$d")
        done
    done
fi

for dir in "${dirs[@]}"; do
    for spec in $dir/*.spec; do
        d=$(dirname $spec)
        for source in $(spectool --list-files $spec | awk '{print $2}'); do
            sourcebase=$(basename "$source")
            [ -h $d/$sourcebase ] || continue
            git annex whereis "$d/$sourcebase" 2>/dev/null | grep -q " web:" && continue
            git annex addurl --file "$d/$sourcebase" "$source"
        done
    done
done
