# Disable debuginfo as it causes issues with bundled gems that build libraries
%global debug_package %{nil}
%global repo_name bc_osc_ansys_workbench
%global app_name bc_osc_ansys_workbench

Name:     ondemand-%{app_name}
Version:  0.7.1
Release:  1%{?dist}
Summary:  Batch Connect - OSC ANSYS Workbench

Group:    System Environment/Daemons
License:  MIT
URL:      https://github.com/OSC/%{repo_name}
Source0:  https://github.com/OSC/%{repo_name}/archive/v%{version}.tar.gz

Requires: ondemand

# Disable automatic dependencies as it causes issues with bundled gems and
# node.js packages used in the apps
AutoReqProv: no

%description
A Batch Connect app designed for OSC OnDemand that launches an ANSYS Workbench 
within an Oakley batch job. It runs in a heavily customized desktop/environment 
so that it works in OSC's supercomputer environment.

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


%files
%defattr(-,root,root)
%{_localstatedir}/www/ood/apps/sys/%{app_name}
%{_localstatedir}/www/ood/apps/sys/%{app_name}/manifest.yml


%changelog
* Tue Jan 08 2019 Morgan Rodgers <mrodgers@osc.edu> 0.7.0-1
- Update Ansys to v0.7.0 (mrodgers@osc.edu)

* Fri Jul 27 2018 Morgan Rodgers <mrodgers@osc.edu> 0.6.0-1
- Fix license reservation bug (mrodgers@osc.edu)

* Tue Mar 27 2018 Jeremy Nicklas <jnicklas@osc.edu> 0.5.0-1
- Bump bc_osc_ansys_workbench to 0.5.0 (jnicklas@osc.edu)

* Mon Feb 26 2018 Trey Dockendorf <tdockendorf@osc.edu> 0.3.0-1
- Bump ondemand-bc_osc_ansys_workbench to 0.3.0 (tdockendorf@osc.edu)

* Tue Feb 13 2018 Trey Dockendorf <tdockendorf@osc.edu> 0.2.0-1
- new package built with tito

