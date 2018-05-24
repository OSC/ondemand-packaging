# Disable debuginfo as it causes issues with bundled gems that build libraries
%global debug_package %{nil}
%global repo_name pseudofun
%global app_name pseudofun

Name:     ondemand-%{app_name}
Version:  0.1.0
Release:  1%{?dist}
Summary:  Pseudogene Functional Network

Group:    System Environment/Daemons
License:  MIT
URL:      https://github.com/OSC/%{repo_name}
Source0:  https://github.com/OSC/%{repo_name}/archive/v%{version}.tar.gz

BuildRequires:  sqlite-devel curl make
BuildRequires:  rh-ruby22 rh-ruby22-rubygem-rake rh-ruby22-rubygem-bundler rh-ruby22-ruby-devel nodejs010 git19
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
source scl_source enable rh-ruby22 nodejs010 git19 &> /dev/null || :

export PASSENGER_APP_ENV=production
export PASSENGER_BASE_URI=/pun/sys/%{app_name}
bin/setup


%install
%__mkdir_p   %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}
%__cp -a ./. %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/
%__mkdir_p   %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/tmp
touch        %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/tmp/restart.txt

%__mkdir_p   %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys
touch        %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/%{app_name}.conf


%post
# Install (not upgrade)
if [ $1 -eq 1 ]; then
  # This NGINX app config needs to exist before it can be rebuilt
  touch %{_sharedstatedir}/nginx/config/apps/sys/%{app_name}.conf

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
%ghost %{_sharedstatedir}/nginx/config/apps/sys/%{app_name}.conf

%changelog
