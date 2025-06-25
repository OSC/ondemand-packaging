#!/bin/bash

BASE_PATH="/var/www/repos/public/ondemand"

function usage()
{
  echo "Usage release-staging.sh -r RELEASE"

  echo "Required options:"
  echo "  -r RELEASE    Staging to release (eg: '4.0')"
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

LOCK_FILE="/var/lib/oodpkg/release-staging-${RELEASE}.lock"

(
  flock -x -w 30 200
    STAGING_PATH="${BASE_PATH}/staging/${RELEASE}"
    RELEASE_PATH="${BASE_PATH}/${RELEASE}"

    rsync -av --delete "${STAGING_PATH}/" "${RELEASE_PATH}/"
) 200>"${LOCK_FILE}"

RETVAL=$?

exit $RETVAL
