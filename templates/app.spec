# Disable debuginfo as it causes issues with bundled gems that build libraries
%global debug_package %{nil}
%global repo_name REPO_NAME
%global app_name APP_NAME
%global with_passenger 1

%if 0%{?with_passenger}
%bcond_without passenger
%else
%bcond_with passenger
%endif

Name:     ondemand-%{app_name}
Version:  VERSION
Release:  1%{?dist}
Summary:  SUMMARY

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
DESCRIPTION

%prep
%setup -q -n %{repo_name}-%{version}


%build
scl enable ondemand - << \EOS
%if %{with passenger}
export PASSENGER_APP_ENV=production
export PASSENGER_BASE_URI=/pun/sys/%{app_name}
%endif
bin/setup
EOS


%install
%__rm ./log/production.log
%__mkdir_p %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}
%__cp -a ./. %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/
echo v%{version} > %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/VERSION
%if %{with passenger}
%__mkdir_p %{buildroot}%{_sharedstatedir}/ondemand-nginx/config/apps/sys
touch %{buildroot}%{_sharedstatedir}/ondemand-nginx/config/apps/sys/%{app_name}.conf
%__mkdir_p %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/tmp
touch %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/tmp/restart.txt
%endif


%post
%if %{with passenger}
# This NGINX app config needs to exist before it can be rebuilt
touch %{_sharedstatedir}/ondemand-nginx/config/apps/sys/%{app_name}.conf

if [ $1 -eq 1 ]; then
  # Rebuild NGINX app config and restart PUNs w/ no active connections
  /opt/ood/nginx_stage/sbin/update_nginx_stage &>/dev/null || :
fi
%endif


%postun
if [[ $1 -eq 0 ]]; then
%if %{with passenger}
  # On uninstallation restart PUNs w/ no active connections
  /opt/ood/nginx_stage/sbin/update_nginx_stage &>/dev/null || :
%endif
fi


%posttrans
%if %{with passenger}
# Restart app in case PUN wasn't restarted
touch %{_localstatedir}/www/ood/apps/sys/%{app_name}/tmp/restart.txt
%endif


%files
%defattr(-,root,root)
%{_localstatedir}/www/ood/apps/sys/%{app_name}
%{_localstatedir}/www/ood/apps/sys/%{app_name}/manifest.yml
%if %{with passenger}
%ghost %{_localstatedir}/www/ood/apps/sys/%{app_name}/tmp/restart.txt
%ghost %{_sharedstatedir}/ondemand-nginx/config/apps/sys/%{app_name}.conf
%endif

%changelog
* Sat Feb 02 2019 Trey Dockendorf <tdockendorf@osc.edu> VERSION-1
- new package built with tito

