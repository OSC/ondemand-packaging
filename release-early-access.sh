#!/bin/bash

BASE_PATH="/var/www/repos/public/ondemand"

function usage()
{
  echo "Usage release-early-access.sh -r RELEASE"

  echo "Required options:"
  echo "  -r RELEASE    early-access to release (eg: '4.0')"
}

while getopts "r:" opt; do
  case "${opt}" in
    r)
      RELEASE="${OPTARG}"
      ;;
    *)
      usage
      exit
      ;;
  esac
done
shift $((OPTIND-1))

if [[ -z "$RELEASE" ]]; then
  echo "Must set -r RELEASE"
  exit 1
fi

LOCK_FILE="/var/lib/oodpkg/release-early-access-${RELEASE}.lock"

(
  flock -x -w 30 200
    EARLY_ACCESS_PATH="${BASE_PATH}/early-access/${RELEASE}"
    RELEASE_PATH="${BASE_PATH}/${RELEASE}"

    rsync -av --delete "${EARLY_ACCESS_PATH}/" "${RELEASE_PATH}/"
) 200>"${LOCK_FILE}"

RETVAL=$?

exit $RETVAL
