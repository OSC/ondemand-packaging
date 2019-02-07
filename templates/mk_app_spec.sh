#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ $# -ne 3 ]; then
    echo "Must provide repo_name, app_name and version"
    exit 1
fi

REPO_NAME="$1"
APP_NAME="$2"
VERSION="$3"
APP_SPEC_SOURCE="${DIR}/app.spec"
PACKAGE_DIR="${DIR}/../web/ondemand-${APP_NAME}"
APP_SPEC_DEST="${PACKAGE_DIR}/ondemand-${APP_NAME}.spec"

if [ ! -d $PACKAGE_DIR ]; then
    mkdir $PACKAGE_DIR
fi

sed -r \
    -e "s/REPO_NAME/${REPO_NAME}/g" \
    -e "s/APP_NAME/${APP_NAME}/g" \
    -e "s/VERSION/${VERSION}/g"\
    $APP_SPEC_SOURCE > $APP_SPEC_DEST

cd $PACKAGE_DIR
spectool -g -S $(basename $APP_SPEC_DEST)
git annex add v${VERSION}.tar.gz
