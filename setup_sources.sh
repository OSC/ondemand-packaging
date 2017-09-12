#!/bin/bash -x

dir='*'
[ -n "$1" ] && dir=$1

for subdir in dependencies; do
  for spec in $subdir/$dir/*.spec; do
    d=$(dirname $spec)
    for source in $(spectool --list-files $spec | awk '{print $2}'); do
      sourcebase=$(basename "$source")
      [ -h $d/$sourcebase ] || continue
      git annex whereis "$d/$sourcebase" 2>/dev/null | grep -q " web:" && continue
      git annex addurl --file "$d/$sourcebase" "$source"
    done
  done
done

