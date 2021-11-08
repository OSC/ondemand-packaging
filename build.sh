#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${DIR}/build/env

WORK_DIR=
OUTPUT_DIR=
CONCURRENCY=1
DISTRIBUTIONS="el7 el8"
GPG_NAME='OnDemand Release Signing Key'
GPG_PUBKEY_PATH=''
SHOW_TASKS=false
DEB=""
TASK='run:rpm'
CLEAN_OUTPUT=true
CLEAN_WORK=true
ATTACH=false
CLEAN_DOCKER=true
CONTAINER="ondemand-packaging-$(whoami)"
PACKAGES=()
GPG_SIGN=true
SKIP_DOWNLOAD=false
GIT_TAG=''
INIT='/usr/sbin/init'
ret=0
if [ ! -f ${DIR}/.gpgpass ]; then
    echo '!!! GPG SIGNING DISABLED : .gpgpass not found !!!'
    GPG_SIGN=false
fi
if [ ! -f ${DIR}/ondemand.sec ]; then
    echo '!!! GPG SIGNING DISABLED : ondemand.sec not found !!!'
    GPG_SIGN=false
fi
DEBUG=false

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
    echo "  -D D-V     Build Debian/Ubuntu packages for DIST-DISTVERSION, eg ubuntu-20.04"
    echo "  -j NUM     Set build concurrency. Default: 1"
    echo "  -d NAMES   Build only for given distributions. This is a space-separated list"
    echo "             of distribution names."
    echo "             Default: $DISTRIBUTIONS"
    echo "  -G NAME    GPG key name"
    echo "             Default: $GPG_NAME"
    echo "  -g         GPG public key path"
    echo "  -S         Skip GPG signing"
    echo "  -T         Show all tasks"
    echo "  -t TASK    Task to run, Default: $TASK"
    echo "  -C         Do not clean up output directory"
    echo "  -W         Do not clean up work directory"
    echo "  -A         Attach after build"
    echo "  -c         Do not clean up docker image"
    echo "  -u         Use unique container name"
    echo "  -V         Git tag to build"
    echo "  -s         Skip source download"
    echo "  -v         Show debug information"
    echo "  -h         Show usage"
}

function echo_blue()
{
    echo -e "\033[0;34m${1}\033[0m"
}

function echo_red()
{
    echo -e "\033[0;31m${1}\033[0m"
}

function echo_green()
{
    echo -e "\033[0;32m${1}\033[0m"
}

function kill_container()
{
    local CONTAINER="$1"
    echo_blue "Killing container ${CONTAINER}"
    docker kill $CONTAINER 1>/dev/null
}

function parse_options()
{
	local OPTIND=1
	local ORIG_ARGV
	local opt
    while getopts "w:o:D:j:d:G:g:STt:CWAcuV:svh" opt; do
        case "$opt" in
        w)
        	WORK_DIR="$OPTARG"
        	;;
        o)
        	OUTPUT_DIR="$OPTARG"
        	;;
        D)
          DEB="$OPTARG"
          TASK='run:deb'
          INIT='/sbin/init'
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
        g)
            GPG_PUBKEY_PATH="$OPTARG"
            ;;
        S)
            GPG_SIGN=false
            ;;
        T)
        	SHOW_TASKS=true
        	;;
        t)
            TASK="$OPTARG"
            ;;
        C)
            CLEAN_OUTPUT=false
            ;;
        W)
            CLEAN_WORK=false
            ;;
        A)
            ATTACH=true
            ;;
        c)
            CLEAN_DOCKER=false
            ;;
        u)
            CONTAINER="${CONTAINER}-$(uuidgen)"
            ;;
        V)
            GIT_TAG="$OPTARG"
            ;;
        s)
            SKIP_DOWNLOAD=true
            ;;
        v)
            DEBUG=true
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
if [ $? -ne 0 ]; then
    echo "Error parsing options"
    exit 1
fi

if tty -s; then
	TTY_ARGS="-t -i"
else
	TTY_ARGS=
fi

if $DEBUG; then
    RAKE_FLAGS=''
else
    RAKE_FLAGS='-q'
fi

if $CLEAN_OUTPUT && [ $PACKAGES != 'attach' ]; then
    if [ -d $OUTPUT_DIR ]; then
        echo_blue "Cleaning output directory: ${OUTPUT_DIR}"
        rm -rf ${OUTPUT_DIR}/*
    fi
fi

if $CLEAN_WORK && [ $PACKAGES != 'attach' ]; then
    if [ -d $WORK_DIR ]; then
        echo_blue "Cleaning work directory: ${WORK_DIR}"
        rm -rf ${WORK_DIR}/*
    fi
fi

if [ ! -d $WORK_DIR ]; then
    echo_blue "Creating work directory: ${WORK_DIR}"
    mkdir -p $WORK_DIR
fi
if [ ! -d $OUTPUT_DIR ]; then
    echo_blue "Creating output directory: ${OUTPUT_DIR}"
    mkdir -p $OUTPUT_DIR
fi

if $DEBUG; then
    set -x
fi

if [ "x${GPG_PUBKEY_PATH}" != "x" ]; then
    echo_blue "Staging ${GPG_PUBKEY_PATH}"
    cp -f $GPG_PUBKEY_PATH ${DIR}/stage/
    export GPG_PUBKEY=$(basename $GPG_PUBKEY_PATH)
else
    export GPG_PUBKEY=''
fi

for p in "${PACKAGES[@]}"; do
    if [ ! -d $p -a $p != 'attach' ]; then
        echo_red "Package ${p} is not a directory"
        continue
    fi
    GIT_ANNEX=false
    if which git-annex 2>/dev/null 1>/dev/null ; then
        for f in `git-annex find --include='*' ${p} 2>/dev/null`; do
            GIT_ANNEX=true
            break
        done
    fi
    if $GIT_ANNEX; then
        echo_blue "Unlocking git-annex sources at ${p}"
        git-annex get $p 1>/dev/null
        git-annex unlock $p 1>/dev/null
    fi

    if docker inspect $CONTAINER 2>/dev/null 1>/dev/null ; then
        if $CLEAN_DOCKER; then
            kill_container $CONTAINER
            START_CONTAINER=true
        else
            START_CONTAINER=false
        fi
    else
        START_CONTAINER=true
    fi

    if [ "x$DEB" != "x" ]; then
      export DIST=$(echo $DEB | cut -d'-' -f1)
      export DISTVERSION=$(echo $DEB | cut -d'-' -f2)
      export DISTRIBUTIONS=$DEB
      source ${DIR}/build/env
      export BUILDBOX_IMAGE=$DEB_BUILDBOX_IMAGE
    fi

    if $START_CONTAINER; then
        echo_blue "Starting container ${CONTAINER} using image $BUILDBOX_IMAGE"
        CONTAINER_ID=$(docker run \
        --detach --rm \
        --name $CONTAINER \
        --privileged \
        --cap-add=SYS_ADMIN \
        -v "${DIR}:/ondemand-packaging:ro" \
        -v "${p}:/package:ro" \
        -v "$WORK_DIR:/work" \
        -v "$OUTPUT_DIR:/output" \
        $BUILDBOX_IMAGE \
        $INIT)
        echo_green "Container started with ID ${CONTAINER_ID}"
    fi

    if [ "$p" == 'attach' ]; then
        DISTRIBUTIONS=''
        ATTACH=true
    fi

    for distro in $DISTRIBUTIONS ; do
        echo_blue "Build STARTED: package=${p} distro=${distro} task=${TASK}"
        docker exec \
        $TTY_ARGS \
        -e "DISTRO=${distro}" \
        -e "PACKAGE=${p}" \
        -e "GPG_SIGN=${GPG_SIGN}" \
        -e "GPG_NAME=${GPG_NAME}" \
        -e "GPG_PUBKEY=${GPG_PUBKEY}" \
        -e "GIT_TAG=${GIT_TAG}" \
        -e "SKIP_DOWNLOAD=${SKIP_DOWNLOAD}" \
        -e "BUILDBOX_IMAGE=${BUILDBOX_IMAGE}" \
        -e "OOD_UID=`/usr/bin/id -u`" \
        -e "OOD_GID=`/usr/bin/id -g`" \
        -e "DEBUG=${DEBUG}" \
        -e "LC_CTYPE=en_US.UTF-8" \
        $CONTAINER \
        /ondemand-packaging/build/inituidgid.sh \
        /ondemand-packaging/build/setuser ood \
        rake ${RAKE_FLAGS} -f /ondemand-packaging/build/Rakefile ${TASK}
        if [ $? -ne 0 ]; then
            echo_red "Build FAILED: package=${p} distro=${distro}"
            ret=1
        else
            echo_green "Build SUCCESS: package=${p} distro=${distro}"
        fi
    done
    if $GIT_ANNEX; then
        echo_blue "Locking git-annex sources at ${p}"
        git-annex lock --force $p 1>/dev/null
    fi
    if $ATTACH ; then
        docker exec \
        $TTY_ARGS \
        -e "DISTRO=${distro}" \
        -e "PACKAGE=${p}" \
        -e "GPG_SIGN=${GPG_SIGN}" \
        -e "GPG_NAME=${GPG_NAME}" \
        -e "GIT_TAG=${GIT_TAG}" \
        -e "SKIP_DOWNLOAD=${SKIP_DOWNLOAD}" \
        -e "OOD_UID=`/usr/bin/id -u`" \
        -e "OOD_GID=`/usr/bin/id -g`" \
        -e "DEBUG=${DEBUG}" \
        -e "LC_CTYPE=en_US.UTF-8" \
        $CONTAINER \
        /ondemand-packaging/build/inituidgid.sh \
        /ondemand-packaging/build/setuser ood \
        /bin/bash
    fi
    if $CLEAN_DOCKER ; then
        kill_container $CONTAINER
    fi
done

exit $ret
