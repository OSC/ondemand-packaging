#!/bin/bash
# Changes the 'app' user's UID and GID to the values specified
# in $OOD_UID and $OOD_GID.
set -e
set -o pipefail

if awk -F: '{ print $3 }' < /etc/passwd | grep -q "^${OOD_UID}$"; then
	echo "ERROR: you can only run this script with a user whose UID does not already exist in the Docker container. Current UID: $OOD_UID"
	exit 1
fi
if awk -F: '{ print $3 }' < /etc/group | grep -q "^${OOD_GID}$"; then
	echo "ERROR: you can only run this script with a user whose GID does not already exist in the Docker container. Current GID: $OOD_GID"
	exit 1
fi

chown -R "$OOD_UID:$OOD_GID" /home/ood
groupmod -g "$OOD_GID" ood
usermod -u "$OOD_UID" -g "$OOD_GID" ood 2>/dev/null 1>/dev/null

# There's something strange with either Docker or the kernel, so that
# the 'app' user cannot access its home directory even after a proper
# chown/chmod. We work around it like this.
mv /home/ood /home/ood2
cp -dpR /home/ood2 /home/ood
rm -rf /home/ood2

if [[ $# -gt 0 ]]; then
	exec "$@"
fi
