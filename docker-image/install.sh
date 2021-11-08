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

source /etc/os-release

header "Installing dependencies"
if [[ "$ID_LIKE" == *debian* ]]; then
	run apt-get update -y
	run apt install -y init debhelper devscripts dh-make build-essential lintian equivs \
			sudo python rake wget curl ruby
	run ln -snf /bin/bundle2.7 /bin/bundle
else
	run dnf update -y
	run dnf install -y dnf-utils langpacks-en glibc-all-langpacks
	run dnf config-manager --set-enabled powertools
	run dnf install -y epel-release
	run dnf install -y python36 mock rubygem-rake sudo git which expect \
	    rpm-build rpmdevtools rpm-sign scl-utils-build \
	    selinux-policy bsdtar
	run alternatives --set python /usr/bin/python3
fi

header "Creating users"
run groupadd ood
run useradd --create-home --gid ood --password 'ood' ood
run sudo -u ood -H git config --global user.email "packages@osc.edu"
run sudo -u ood -H git config --global user.name "OnDemand Packaging"

header "Miscellaneous"
run cp /build/sudoers.conf /etc/sudoers.d/ood
run chmod 440 /etc/sudoers.d/ood

if [[ "$ID_LIKE" == *rhel* ]]; then
	header "Setup mock and RPM env"
	run usermod -a -G mock ood
	run sudo -u ood -H rpmdev-setuptree
	sudo -u ood -H cat >> /home/ood/.rpmmacros <<EOF
%_signature gpg
%_gpg_path ~/.gnupg
%_gpg /usr/bin/gpg
#%_gpg_sign_cmd_extra_args --pinentry-mode loopback
EOF
	# Modified macro from /usr/lib/rpm/macros to add pinentry-mode and passphrase-file
	# pinentry-mode only needed on EL8
	echo "%__gpg_sign_cmd %{__gpg} \\" >> /home/ood/.rpmmacros
	echo "        gpg --no-verbose --no-armor --batch --pinentry-mode loopback \\" >> /home/ood/.rpmmacros
	echo "        --passphrase-file /ondemand-packaging/.gpgpass \\" >> /home/ood/.rpmmacros
	echo "        %{?_gpg_sign_cmd_extra_args:%{_gpg_sign_cmd_extra_args}} \\" >> /home/ood/.rpmmacros
	echo "        %{?_gpg_digest_algo:--digest-algo %{_gpg_digest_algo}} \\" >> /home/ood/.rpmmacros
	echo "	      --no-secmem-warning \\" >> /home/ood/.rpmmacros
	echo "        -u \"%{_gpg_name}\" -sbo %{__signature_filename} %{__plaintext_filename}" >> /home/ood/.rpmmacros

	run install -d -m 0700 -o ood -g ood /home/ood/.gnupg
	run echo "allow-loopback-pinentry" >> /home/ood/.gnupg/gpg-agent.conf
	run rpm --import /build/RPM-GPG-KEY-ondemand

	run cp -a /build/epel-7-x86_64.cfg /etc/mock/epel-7-x86_64.cfg
	run cp -a /build/epel-8-x86_64.cfg /etc/mock/epel-8-x86_64.cfg
	run cp -a /build/ondemand-el7-x86_64.cfg /etc/mock/ondemand-el7-x86_64.cfg
	run cp -a /build/ondemand-el8-x86_64.cfg /etc/mock/ondemand-el8-x86_64.cfg
	run sed -i.bak '/yum_install_command/d' /etc/mock/templates/centos-7.tpl
	run sed -i.bak '/includepkgs=devtoolset/d' /etc/mock/templates/centos-7.tpl

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
	    run rm -rf /var/lib/mock/*
	    run $tar xf /build/$MOCK_CACHE -C /
	fi
fi

header "Cleaning up"
if [[ "$ID_LIKE" == *debian* ]]; then
	run apt-get clean all -y
else
	run dnf clean all
fi
run rm -rf /build
