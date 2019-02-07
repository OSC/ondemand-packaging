#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

WORK_DIR=
OUTPUT_DIR=
CONCURRENCY=1
DISTRIBUTIONS="el6 el7"
GPG_NAME='OnDemand Release Signing Key'
SHOW_TASKS=false
CLEAN_DOCKER=true
BUILDBOX_IMAGE='ohiosupercomputer/ondemand_buildbox:0.0.2'
PACKAGES=()
GPG_SIGN=true
if [ ! -f ${DIR}/.gpgpass ]; then
    echo '!!! GPG SIGNING DISABLED : .gpgpass not found !!!'
    GPG_SIGN=false
fi
if [ ! -f ${DIR}/ondemand.sec ]; then
    echo '!!! GPG SIGNING DISABLED : ondemand.sec not found !!!'
    GPG_SIGN=false
fi

function usage()
{
    echo "Usage: ./build.sh [OPTIONS] PACKAGE [PACKAGE]"
    echo "Build RPM packages."
    echo
    echo "Required options:"
    echo "  -w DIR     Path to work directory (for temporary files)"
    echo "  -o DIR     Path in which to store build products"
    echo
    echo "Optional options:"
    echo "  -j NUM     Set build concurrency. Default: 1"
    echo "  -d NAMES   Build only for given distributions. This is a space-separated list"
    echo "             of distribution names."
    echo "             Default: $DISTRIBUTIONS"
    echo "  -G NAME    GPG key name"
    echo "             Default: $GPG_NAME"
    echo "  -T         Show all tasks"
    echo "  -D         Do not clean up docker image"
    echo "  -h         Show usage"
}

function parse_options()
{
	local OPTIND=1
	local ORIG_ARGV
	local opt
    while getopts "w:o:j:d:G:TDh" opt; do
        case "$opt" in
        w)
        	WORK_DIR="$OPTARG"
        	;;
        o)
        	OUTPUT_DIR="$OPTARG"
        	;;
        j)
        	CONCURRENCY=$OPTARG
        	;;
        d)
        	DISTRIBUTIONS="$OPTARG"
        	;;
        G)
            GPG_NAME="$OPTARG"
            ;;
        T)
        	SHOW_TASKS=true
        	;;
        D)
            CLEAN_DOCKER=false
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

	if [[ ${#ORIG_ARGV[@]} = 0 ]]; then
		SHOW_TASKS=true
	fi

	if ! $SHOW_TASKS; then
		if [[ "$WORK_DIR" = "" ]]; then
			echo "ERROR: please specify a work directory with -w."
			exit 1
		fi
		if [[ "$OUTPUT_DIR" = "" ]]; then
			echo "ERROR: please specify an output directory with -o."
			exit 1
		fi
        if [ $# -gt 0 ]; then
            PACKAGES=($@)
        else
            read -p "Are you use you want to release ALL packages? (y/n): "
            if [[ $REPLY =~ ^[Nn]$ ]]; then
                exit 0
            fi
            packages=()
            for c in compute web-nonscl web; do
                for p in ${DIR}/${c}/*; do
                    PACKAGES+=("$p")
                done
            done
        fi
	fi
}

parse_options "$@"

if tty -s; then
	TTY_ARGS="-t -i"
else
	TTY_ARGS=
fi

CONTAINER="ondemand-packaging-$(whoami)"
for p in "${PACKAGES[@]}"; do
    set -x
    docker run \
    --detach --rm \
    --name $CONTAINER \
    --privileged \
    --cap-add=SYS_ADMIN \
    -v "${DIR}:/ondemand-packaging:ro" \
    -v "${p}:/package:ro" \
    -v "$WORK_DIR:/work" \
    -v "$OUTPUT_DIR:/output" \
    -e "DISTRO=${distro}" \
    -e "PACKAGE=${p}" \
    -e "OOD_UID=`/usr/bin/id -u`" \
    -e "OOD_GID=`/usr/bin/id -g`" \
    -e "LC_CTYPE=en_US.UTF-8" \
    $BUILDBOX_IMAGE \
    /usr/sbin/init

    for distro in $DISTRIBUTIONS ; do
        echo "BULID: package=${p} distro=${distro}"
        docker exec \
        $TTY_ARGS \
        -e "DISTRO=${distro}" \
        -e "PACKAGE=${p}" \
        -e "GPG_SIGN=${GPG_SIGN}" \
        -e "GPG_NAME=${GPG_NAME}" \
        -e "OOD_UID=`/usr/bin/id -u`" \
        -e "OOD_GID=`/usr/bin/id -g`" \
        -e "LC_CTYPE=en_US.UTF-8" \
        $CONTAINER \
        /ondemand-packaging/build/inituidgid.sh \
        /ondemand-packaging/build/setuser ood \
        rake -f /ondemand-packaging/build/Rakefile run
        echo "EXIT: $?"
    done
    if $CLEAN_DOCKER ; then
        docker kill $CONTAINER
    fi
done

exit 0
