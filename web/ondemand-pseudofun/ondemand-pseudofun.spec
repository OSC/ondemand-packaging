# Disable debuginfo as it causes issues with bundled gems that build libraries
%global debug_package %{nil}
%global repo_name pseudofun
%global app_name pseudofun

# Work around issue with EL6 builds
# https://stackoverflow.com/a/48801417
%if 0%{?rhel} < 7
%define __strip /opt/rh/devtoolset-6/root/usr/bin/strip
%endif

Name:     ondemand-%{app_name}
Version:  0.2.1
Release:  4%{?dist}
Summary:  Pseudogene Functional Network

Group:    System Environment/Daemons
License:  MIT
URL:      https://github.com/OSC/%{repo_name}
Source0:  https://github.com/OSC/%{repo_name}/archive/v%{version}.tar.gz

BuildRequires:  sqlite-devel curl make
BuildRequires:  ondemand-runtime
BuildRequires:  ondemand-ruby
BuildRequires:  ondemand-nodejs
BuildRequires:  ondemand-git
Requires:       ondemand

# Disable automatic dependencies as it causes issues with bundled gems and
# node.js packages used in the apps
AutoReqProv: no

%description
Pseudogene Functional Network is a computational tool for studying potential
functions of pseudogenes in the context of evolution and diseases, developed by
the Zhang Lab of Computational Genomics and Proteomics at OSU BMI.

%prep
%setup -q -n %{repo_name}-%{version}


%build
scl enable ondemand - << \EOS
export PASSENGER_APP_ENV=production
export PASSENGER_BASE_URI=/pun/sys/%{app_name}
bin/setup
EOS


%install
%__rm        ./log/production.log
%__mkdir_p   %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}
%__cp -a ./. %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/
%__mkdir_p   %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/tmp
touch        %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/tmp/restart.txt
echo v%{version} > %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/VERSION

%__mkdir_p   %{buildroot}%{_sharedstatedir}/ondemand-nginx/config/apps/sys
touch        %{buildroot}%{_sharedstatedir}/ondemand-nginx/config/apps/sys/%{app_name}.conf


%post
# Install (not upgrade)
if [ $1 -eq 1 ]; then
  # This NGINX app config needs to exist before it can be rebuilt
  touch %{_sharedstatedir}/ondemand-nginx/config/apps/sys/%{app_name}.conf

  # Rebuild NGINX app config and restart PUNs w/ no active connections
  /opt/ood/nginx_stage/sbin/update_nginx_stage &>/dev/null || :
fi


%postun
# Uninstall (not upgrade)
if [[ $1 -eq 0 ]]; then
  # On uninstallation restart PUNs w/ no active connections
  /opt/ood/nginx_stage/sbin/update_nginx_stage &>/dev/null || :
fi


%posttrans
# Restart app in case PUN wasn't restarted
touch %{_localstatedir}/www/ood/apps/sys/%{app_name}/tmp/restart.txt


%files
%defattr(-,root,root)
%{_localstatedir}/www/ood/apps/sys/%{app_name}
%{_localstatedir}/www/ood/apps/sys/%{app_name}/manifest.yml
%ghost %{_localstatedir}/www/ood/apps/sys/%{app_name}/tmp/restart.txt
%ghost %{_sharedstatedir}/ondemand-nginx/config/apps/sys/%{app_name}.conf

%changelog
* Sun Feb 03 2019 Trey Dockendorf <tdockendorf@osc.edu> 0.2.1-3
- Update passenger apps to use new /var/lib/ondemand-nginx paths and new
  ondemand SCL for ondemand 1.5 (tdockendorf@osc.edu)

* Wed Oct 24 2018 Morgan Rodgers <mrodgers@osc.edu> 0.2.1-2
- Update pseudofun dependencies (mrodgers@osc.edu)

* Wed Jul 18 2018 Trey Dockendorf <tdockendorf@osc.edu> 0.2.0-2
- Remove production.log (tdockendorf@osc.edu)

* Tue May 29 2018 Jeremy Nicklas <jnicklas@osc.edu> 0.2.0-1
- Bump pseudofun to 0.2.0 (jnicklas@osc.edu)

* Thu May 24 2018 Jeremy Nicklas <jnicklas@osc.edu> 0.1.0-1
- new package built with tito

