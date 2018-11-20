#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
declare -A release_map=(
    ["compute"]="compute"
    ["web-nonscl"]="web-nonscl"
    ["web"]="web-scl"
    ["misc/ondemand-release"]="release"
    ["misc/ondemand-release-latest"]="release"
    ["web/mod_auth_openidc"]="web-httpd24"
)

if [ $# -gt 0 ]; then
    packages=($@)
else
    read -p "Are you use you want to release ALL packages? (y/n): "
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        exit 0
    fi
    packages=()
    for c in compute web-nonscl web; do
        for p in ${DIR}/${c}/*; do
            packages+=("$p")
        done
    done
fi

for p in "${packages[@]}"; do
    package=$(basename $p)
    c=$(basename $(dirname $p))
    package_key=$(echo $package | sed "s/-/_/")
    cp="${c}/${package}"
    if [ -n "${release_map[$cp]}" ]; then
        release="${release_map[$cp]}"
    else
        release="${release_map[$c]}"
    fi
    echo "RELEASE: $package"
    cd $p
    RSYNC_USERNAME=oodpkg tito release --all-starting-with=$release --output "$(mktemp -d)"
    cd $DIR
done

exit 0
