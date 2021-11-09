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

DIST="$1"

header "Creating users"
run groupadd ood
run useradd --create-home --gid ood --password 'ood' ood

header "Miscellaneous"
cat > /etc/sudoers.d/ood <<EOF
Defaults:ood !requiretty, !authenticate
%ood ALL=NOPASSWD:ALL
EOF
run chmod 440 /etc/sudoers.d/ood

if [[ "$DIST" == el* ]]; then
	header "Setup RPM env"
	sudo -u ood -H cat >> /home/ood/.rpmmacros <<EOF
%_topdir /work/$DIST
%_signature gpg
%_gpg_path ~/.gnupg
%_gpg /usr/bin/gpg
EOF
	# Modified macro from /usr/lib/rpm/macros to add pinentry-mode and passphrase-file
	# pinentry-mode only needed on EL8
	echo "%__gpg_sign_cmd %{__gpg} \\" >> /home/ood/.rpmmacros
	echo "        gpg --no-verbose --no-armor --batch \\" >> /home/ood/.rpmmacros
  if [[ "$DIST" != "el7" ]]; then
  	echo "        --pinentry-mode loopback \\" >> /home/ood/.rpmmacros
  fi
	echo "        --passphrase-file /ondemand-packaging/.gpgpass \\" >> /home/ood/.rpmmacros
	echo "        %{?_gpg_sign_cmd_extra_args:%{_gpg_sign_cmd_extra_args}} \\" >> /home/ood/.rpmmacros
	echo "        %{?_gpg_digest_algo:--digest-algo %{_gpg_digest_algo}} \\" >> /home/ood/.rpmmacros
	echo "	      --no-secmem-warning \\" >> /home/ood/.rpmmacros
	echo "        -u \"%{_gpg_name}\" -sbo %{__signature_filename} %{__plaintext_filename}" >> /home/ood/.rpmmacros

  if [[ "$DIST" != "el7" ]]; then
  	run install -d -m 0700 -o ood -g ood /home/ood/.gnupg
	  run echo "allow-loopback-pinentry" >> /home/ood/.gnupg/gpg-agent.conf
  fi  
fi

header "Install ood_packaging gem"
if [[ "$DIST" == "el7" ]]; then
  run scl enable rh-ruby27 -- gem install --no-doc /build/*.gem
else
  run gem install --no-doc /build/*.gem
fi

header "Copy in launch scripts"
run mkdir -p /ondemand-packaging
run install -m 0755 /build/inituidgid.sh /ondemand-packaging/
run install -m 0755 /build/setuser.rb /ondemand-packaging/
run install -m 0644 /build/Rakefile /ondemand-packaging/

header "Cleaning up"
run rm -rf /build
