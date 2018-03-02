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

BuildRequires:  sqlite-devel, curl, make
BuildRequires:  rh-ruby22, rh-ruby22-rubygem-rake, rh-ruby22-rubygem-bundler, rh-ruby22-ruby-devel, nodejs010, git19
Requires:       ondemand

# Disable automatic dependencies as it causes issues with bundled gems and
# node.js packages used in the apps
AutoReqProv: no

%description
DESCRIPTION

%prep
%setup -q -n %{repo_name}-%{version}


%build


%install
export PASSENGER_APP_ENV=production
export PASSENGER_BASE_URI=/pun/sys/%{app_name}
mkdir -p %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}
if [ -x bin/setup ]; then
    bin/setup
fi
cp -a ./. %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/
%if %{with passenger}
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/%{app_name}.conf
%endif

%posttrans
%if %{with passenger}
# Generate NGINX app config during installation/upgrade
/opt/ood/nginx_stage/sbin/update_nginx_stage &>/dev/null || :

# Do not forget to restart app if it is a Passenger app
touch %{_localstatedir}/www/ood/apps/sys/%{app_name}/tmp/restart.txt
%endif

%postun
if [[ $1 -eq 0 ]]; then
%if %{with passenger}
  # Clean up NGINX app config after uninstallation
  /opt/ood/nginx_stage/sbin/update_nginx_stage &>/dev/null || :
%endif
fi

%files
%defattr(-,root,root)
%{_localstatedir}/www/ood/apps/sys/%{app_name}
%{_localstatedir}/www/ood/apps/sys/%{app_name}/manifest.yml
%if %{with passenger}
%ghost %{_sharedstatedir}/nginx/config/apps/sys/%{app_name}.conf
%endif

%changelog
