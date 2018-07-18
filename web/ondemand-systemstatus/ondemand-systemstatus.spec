# Disable debuginfo as it causes issues with bundled gems that build libraries
%global debug_package %{nil}
%global repo_name osc-systemstatus
%global app_name systemstatus
%global with_passenger 1

%if 0%{?with_passenger}
%bcond_without passenger
%else
%bcond_with passenger
%endif

Name:     ondemand-%{app_name}
Version:  1.4.0
Release:  2%{?dist}
Summary:  System Status for OSC Clusters

Group:    System Environment/Daemons
License:  MIT
URL:      https://github.com/AweSim-OSC/%{repo_name}
Source0:  https://github.com/AweSim-OSC/%{repo_name}/archive/v%{version}.tar.gz

BuildRequires:  sqlite-devel curl make
BuildRequires:  rh-ruby22 rh-ruby22-rubygem-rake rh-ruby22-rubygem-bundler rh-ruby22-ruby-devel nodejs010 git19
Requires:       ondemand

# Disable automatic dependencies as it causes issues with bundled gems and
# node.js packages used in the apps
AutoReqProv: no

%description
This app displays the current system status of available system clusters.


%prep
%setup -q -n %{repo_name}-%{version}


%build
%if %{with passenger}
export PASSENGER_APP_ENV=production
export PASSENGER_BASE_URI=/pun/sys/%{app_name}
%endif
export SCL_PKGS="rh-ruby22 nodejs010 git19"
export SCL_SOURCE=$(command -v scl_source)
if [ -x bin/setup ]; then
  if [ "$SCL_SOURCE" ]; then
    source "$SCL_SOURCE" enable $SCL_PKGS &> /dev/null || :
  fi
  bin/setup
fi


%install
%__rm ./log/production.log
%__mkdir_p %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}
%__cp -a ./. %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/
%if %{with passenger}
%__mkdir_p %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/%{app_name}.conf
%__mkdir_p %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/tmp
touch %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/tmp/restart.txt
%endif


%post
%if %{with passenger}
# This NGINX app config needs to exist before it can be rebuilt
touch %{_sharedstatedir}/nginx/config/apps/sys/%{app_name}.conf

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
%ghost %{_sharedstatedir}/nginx/config/apps/sys/%{app_name}.conf
%endif

%changelog
* Wed Mar 07 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.4.0-1
- new package built with tito

