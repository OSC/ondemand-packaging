# Disable debuginfo as it causes issues with bundled gems that build libraries
%global debug_package %{nil}
%global repo_name ood_auth_registration
%global app_name register

Name:     ondemand-%{app_name}
Version:  0.4.0
Release:  1%{?dist}
Summary:  OSC OnDemand Open ID Connect CI Logon Registration page

Group:    System Environment/Daemons
License:  MIT
URL:      https://github.com/OSC/%{repo_name}
Source0:  https://github.com/OSC/%{repo_name}/archive/v%{version}.tar.gz

Requires: ondemand
Requires: rh-php56-php-ldap

# Disable automatic dependencies as it causes issues with bundled gems and
# node.js packages used in the apps
AutoReqProv: no

%description
OSC OnDemand Open ID Connect CI Logon Registration page

%prep
%setup -q -n %{repo_name}-%{version}


%build


%install
mkdir -p %{buildroot}%{_localstatedir}/www/ood/%{app_name}
cp -R ./* %{buildroot}%{_localstatedir}/www/ood/%{app_name}


%files
%defattr(-,root,root)
%{_localstatedir}/www/ood/%{app_name}


%changelog
* Thu Oct 25 2018 Morgan Rodgers <mrodgers@osc.edu> 0.3.0-1
- Bump ondemand-register version (mrodgers@osc.edu)

* Tue Feb 13 2018 Trey Dockendorf <tdockendorf@osc.edu> 0.2.0-1
- new package built with tito

