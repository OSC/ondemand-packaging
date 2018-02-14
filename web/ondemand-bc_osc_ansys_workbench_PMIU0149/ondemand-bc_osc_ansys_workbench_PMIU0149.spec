# Disable debuginfo as it causes issues with bundled gems that build libraries
%global debug_package %{nil}
%global repo_name bc_osc_ansys_workbench
%global app_name bc_osc_ansys_workbench_PMIU0149
%global package_version 0.2.0
%global tag %{package_version}-PMIU0149

Name:     ondemand-%{app_name}
Version:  %{package_version}
Release:  1%{?dist}
Summary:  Batch Connect - OSC ANSYS Workbench

Group:    System Environment/Daemons
License:  MIT
URL:      https://github.com/OSC/%{repo_name}
Source0:  https://github.com/OSC/%{repo_name}/archive/v%{tag}.tar.gz

Requires: ondemand

# Disable automatic dependencies as it causes issues with bundled gems and
# node.js packages used in the apps
AutoReqProv: no

%description
A Batch Connect app designed for OSC OnDemand that launches an ANSYS Workbench 
within an Oakley batch job. It runs in a heavily customized desktop/environment 
so that it works in OSC's supercomputer environment.

%prep
%setup -q -n %{repo_name}-%{tag}


%build


%install
export PASSENGER_APP_ENV=production
export PASSENGER_BASE_URI=/pun/sys/%{app_name}
mkdir -p %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}
if [ -x bin/setup ]; then
    bin/setup
fi
cp -a ./. %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/


%files
%defattr(-,root,root)
%{_localstatedir}/www/ood/apps/sys/%{app_name}
%{_localstatedir}/www/ood/apps/sys/%{app_name}/manifest.yml


%changelog
