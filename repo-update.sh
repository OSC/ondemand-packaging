#!/bin/bash

GPGPASS="/systems/osc_certs/gpg/ondemand/.gpgpass"
BASE_PATH="/var/www/repos/public/ondemand"
# Only EL7 uses different
GPG_KEY="FD775498"
REPO=""
TYPE="web"
DIST=""
ARCH="x86_64"

function usage()
{
  echo "Usage repo-update.sh -r REPO -t [WEB|COMPUTE] -d DIST -a [ARCH]"

  echo "Required options:"
  echo "  -r REPO       Repo to update (eg: 'latest', '2.1', 'build/2.1')"
  echo "  -d DIST       Distribution to update (eg: 'el7', 'el8', 'focal')"
  echo
  echo "Optional options:"
  echo "  -g GPGPASS    The path to GPG password file (default ${GPGPASS})"
  echo "  -t TYPE       Type of repo to update, either web or compute (default: ${TYPE})"
  echo "  -a ARCH       Arch to update (default: ${ARCH})"
}

while getopts "r:t:d:a:g:" opt; do
  case "${opt}" in
    r)
      REPO="${OPTARG}"
      ;;
    t)
      TYPE="${OPTARG}"
      ;;
    d)
      DIST="${OPTARG}"
      ;;
    a)
      ARCH="${OPTARG}"
      ;;
    g)
      GPGPASS="${OPTARG}"
      ;;
    *)
      usage
      exit
      ;;
  esac
done
shift $((OPTIND-1))

do_hash() {
  HASH_NAME=$1
  HASH_CMD=$2
  echo "${HASH_NAME}:"
  for f in $(find -type f); do
    f=$(echo $f | cut -c3-) # remove ./ prefix
    if [[ "$(basename $f)" != "Packages"* ]]; then
      continue
    fi
    echo " $(${HASH_CMD} ${f}  | cut -d" " -f1) $(wc -c $f)"
  done
}

if [[ "${USER}" != "oodpkg" ]]; then
  echo "Must run as oodpkg user"
  exit 1
fi

EL=true
if [[ "${DIST}" != "el"* ]]; then
  EL=false
fi

if [[ "${DIST}" == "el7" ]];
  GPG_KEY="92D31755"
fi

if [[ "x${REPO_PATH}" = "x" ]]; then
  LOCK_NAME="$(echo '${REPO}-${TYPE}-${DIST}-${ARCH}' | md5sum | cut -d' ' -f1)"
else
  LOCK_NAME="$(echo '${REPO_PATH}' | md5sum | cut -d' ' -f1)"
fi
LOCK_FILE="/var/lib/oodpkg/repo-update-${LOCK_NAME}.lock"

(
  flock -x -w 30 200
  if $EL; then
    REPO_PATH="${BASE_PATH}/${REPO}/${TYPE}/${DIST}/${ARCH}"
    SRPM_PATH="${BASE_PATH}/${REPO}/${TYPE}/${DIST}/SRPMS"
    echo "level=\"info\" msg=\"Update repo\" repo=\"${REPO_PATH}\""
    cd ${REPO_PATH}
    createrepo_c --update .
    echo "level=\"info\" msg=\"GPG sign repo\" repo=\"${REPO_PATH}\""
    gpg --default-key ${GPG_KEY} --detach-sign --passphrase-file ${GPGPASS} --batch --yes --no-tty --armor repodata/repomd.xml
    echo "level=\"info\" msg=\"Update repo\" repo=\"${SRPM_PATH}\""
    cd ${SRPM_PATH}
    createrepo_c --update .
    echo "level=\"info\" msg=\"GPG sign repo\" repo=\"${SRPM_PATH}\""
    gpg --default-key ${GPG_KEY} --detach-sign --passphrase-file ${GPGPASS} --batch --yes --no-tty --armor repodata/repomd.xml
  else
    case "${DIST}" in
    ubuntu-22.04|jammy)
      DIST="jammy"
      ;;
    ubuntu-20.04|focal)
      DIST="focal"
      ;;
    *)
      echo "Unrecognized DIST"
      exit 1
      ;;
    esac
    case "${ARCH}" in
    x86_64)
      ARCH="amd64"
      ;;
    *)
      echo "Unrecognized ARCH"
      exit 1
      ;;
    esac
    REPO_PATH="${BASE_PATH}/${REPO}/${TYPE}/apt"
    DIST_PATH="${REPO_PATH}/dists/${DIST}"
    echo "level=\"info\" msg=\"Scan packages repo\" repo=\"${REPO_PATH}\""
    pushd ${REPO_PATH}
    dpkg-scanpackages --multiversion --arch ${ARCH} pool/${DIST} > dists/${DIST}/main/binary-${ARCH}/Packages
    cat dists/${DIST}/main/binary-${ARCH}/Packages | gzip -9 > dists/${DIST}/main/binary-${ARCH}/Packages.gz
    echo "level=\"info\" msg=\"Update Release\" repo=\"${DIST_PATH}\""
    pushd ${DIST_PATH}
    cat > Release <<EOF
Origin: OnDemand Repository
Label: OnDemand
Suite: stable
Codename: ${DIST}
Version: ${REPO}
Architectures: ${ARCH}
Components: main
Description: OnDemand repository
Date: $(date -Ru)
$(do_hash "MD5Sum" "md5sum")
$(do_hash "SHA1" "sha1sum")
$(do_hash "SHA256" "sha256sum")
EOF
    echo "level=\"info\" msg=\"GPG sign Release\" repo=\"${DIST_PATH}\""
    cat Release | gpg --detach-sign --passphrase-file ${GPGPASS} --batch --yes --no-tty --digest-algo SHA256 --cert-digest-algo SHA256 --armor > Release.gpg
    cat Release | gpg --detach-sign --passphrase-file ${GPGPASS} --batch --yes --no-tty --armor --digest-algo SHA256 --cert-digest-algo SHA256 --clearsign > InRelease
  fi
) 200>${LOCK_FILE}

RETVAL=$?

exit $RETVAL
