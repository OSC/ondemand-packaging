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
run yum install -y rubygem-rake sudo git git-annex which expect \
    rpm-build rpmdevtools mock rpm-sign scl-utils-build

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

run cp /build/epel-6-x86_64.cfg /etc/mock/epel-6-x86_64.cfg
run cp /build/epel-7-x86_64.cfg /etc/mock/epel-7-x86_64.cfg

run sudo -u ood -H git config --global user.email "packages@osc.edu"
run sudo -u ood -H git config --global user.name "OnDemand Packaging"

header "Cleaning up"
run yum clean all
run rm -rf /build
