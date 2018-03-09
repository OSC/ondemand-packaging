# Disable debuginfo as it causes issues with bundled gems that build libraries
%global debug_package %{nil}
%global repo_name bc_osc_abaqus
%global app_name bc_osc_abaqus

Name:     ondemand-%{app_name}
Version:  0.3.0
Release:  1%{?dist}
Summary:  Batch Connect - OSC Abaqus/CAE

Group:    System Environment/Daemons
License:  MIT
URL:      https://github.com/OSC/%{repo_name}
Source0:  https://github.com/OSC/%{repo_name}/archive/v%{version}.tar.gz

Requires: ondemand

# Disable automatic dependencies as it causes issues with bundled gems and
# node.js packages used in the apps
AutoReqProv: no

%description
A Batch Connect app designed for OSC OnDemand that launches Abaqus within an Owens batch job.

%prep
%setup -q -n %{repo_name}-%{version}


%build


%install
%__mkdir_p %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}
%__cp -a ./. %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/


%files
%defattr(-,root,root)
%{_localstatedir}/www/ood/apps/sys/%{app_name}
%{_localstatedir}/www/ood/apps/sys/%{app_name}/manifest.yml


%changelog
* Tue Feb 13 2018 Trey Dockendorf <tdockendorf@osc.edu> 0.2.0-1
- new package built with tito

