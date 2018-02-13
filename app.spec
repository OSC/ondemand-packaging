# Disable debuginfo as it causes issues with bundled gems that build libraries
%global debug_package %{nil}
%global repo_name REPO_NAME
%global app_name APP_NAME

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
[ -x bin/setup ] && bin/setup


%files
%defattr(-,root,root)
%{_localstatedir}/www/ood/apps/sys/%{app_name}


%changelog
