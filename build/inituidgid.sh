#!/bin/bash
# Changes the 'app' user's UID and GID to the values specified
# in $OOD_UID and $OOD_GID.
set -e
set -o pipefail

chown -R "$OOD_UID:$OOD_GID" /home/ood
groupmod -o -g "$OOD_GID" ood
usermod -o -u "$OOD_UID" -g "$OOD_GID" ood 2>/dev/null 1>/dev/null

# There's something strange with either Docker or the kernel, so that
# the 'app' user cannot access its home directory even after a proper
# chown/chmod. We work around it like this.
mv /home/ood /home/ood2
cp -dpR /home/ood2 /home/ood
rm -rf /home/ood2

if [[ $# -gt 0 ]]; then
	exec "$@"
fi
