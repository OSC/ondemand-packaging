#!/bin/bash
set -e

function header()
{
	echo
	echo "----- $@ -----"
}

function run()
{
	echo "+ $@"
	"$@"
}

export HOME=/root
export LANG=en_US.UTF-8
export LC_CTYPE=en_US.UTF-8

header "Creating users"
run groupadd ood
run useradd --create-home --gid ood --password 'ood' ood

header "Installing dependencies"
run yum update -y
run yum install -y epel-release centos-release-scl
run yum install -y mock rubygem-rake sudo git git-annex which expect \
    rpm-build rpmdevtools rpm-sign scl-utils-build \
    selinux-policy bsdtar

header "Miscellaneous"
run cp /build/sudoers.conf /etc/sudoers.d/ood
run chmod 440 /etc/sudoers.d/ood

run usermod -a -G mock ood
run sudo -u ood -H rpmdev-setuptree
sudo -u ood -H cat >> /home/ood/.rpmmacros <<EOF
%_signature gpg
%_gpg_path ~/.gnupg
%_gpg /usr/bin/gpg
EOF
rpm --import /build/RPM-GPG-KEY-ondemand

run sudo -u ood -H git config --global user.email "packages@osc.edu"
run sudo -u ood -H git config --global user.name "OnDemand Packaging"

run cp -a /build/epel-7-x86_64.cfg /etc/mock/epel-7-x86_64.cfg
run cp -a /build/epel-8-x86_64.cfg /etc/mock/epel-8-x86_64.cfg
run cp -a /build/ondemand-el7-x86_64.cfg /etc/mock/ondemand-el7-x86_64.cfg
run cp -a /build/ondemand-el8-x86_64.cfg /etc/mock/ondemand-el8-x86_64.cfg

# Hack to work around issue with logs filling up during EL8 builds
# Issue resolved but left just in case
#rm -f /var/log/lastlog
#ln -s /dev/null /var/log/lastlog

source /build/env
run curl -f -o /build/$MOCK_CACHE https://yum.osc.edu/ondemand/build/$MOCK_CACHE || echo "Download failed!"
if [ -f /build/$MOCK_CACHE ]; then
    grep ' / ' /proc/mounts | grep -q overlay
    if [ $? -eq 0 ]; then
        tar=bsdtar
    else
        tar=tar
    fi
    run $tar xf /build/$MOCK_CACHE -C /
fi

header "Cleaning up"
run yum clean all
run rm -rf /build
