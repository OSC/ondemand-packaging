#!/bin/bash -x

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
