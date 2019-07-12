# Disable debuginfo as it causes issues with bundled gems that build libraries
%global debug_package %{nil}
%global repo_name bc_osc_jupyter_pitzer
%global app_name bc_osc_jupyter_pitzer

Name:     ondemand-%{app_name}
Version:  0.11.1
Release:  2%{?dist}
Summary:  Batch Connect - OSC Jupyter Notebook (Pitzer)

Group:    System Environment/Daemons
License:  MIT
URL:      https://github.com/OSC/%{repo_name}
Source0:  https://github.com/OSC/%{repo_name}/archive/v%{version}.tar.gz

Requires: ondemand

# Disable automatic dependencies as it causes issues with bundled gems and
# node.js packages used in the apps
AutoReqProv: no

%description
An interactive app designed for OSC OnDemand that launches a Jupyter Notebook server within an Pitzer batch job.


%prep
%setup -q -n %{repo_name}-%{version}


%build


%install
%__mkdir_p %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}
%__cp -a ./. %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/
echo v%{version} > %{buildroot}%{_localstatedir}/www/ood/apps/sys/%{app_name}/VERSION


%files
%defattr(-,root,root)
%{_localstatedir}/www/ood/apps/sys/%{app_name}
%{_localstatedir}/www/ood/apps/sys/%{app_name}/manifest.yml


%changelog
* Tue Nov 06 2018 Morgan Rodgers <mrodgers@osc.edu> 0.10.0-1
- Addition of Jupyter for Pitzer
* Thu Sep 20 2018 Morgan Rodgers <mrodgers@osc.edu> 0.9.0-1
- Update Jupyter to v0.9.0 (mrodgers@osc.edu)

* Fri Aug 24 2018 Morgan Rodgers <mrodgers@osc.edu> 0.8.0-1
- Add IJulia kernel for Julia 0.6.4 (mrodgers@osc.edu)

* Tue Aug 14 2018 Morgan Rodgers <mrodgers@osc.edu> 0.7.0-1
- Added support for Julia 1.0 kernel (mrodgers@osc.edu)

* Fri Apr 27 2018 Jeremy Nicklas <jnicklas@osc.edu> 0.6.2-1
- Bump bc_osc_jupyter to 0.6.2 (jnicklas@osc.edu)

* Thu Apr 26 2018 Jeremy Nicklas <jnicklas@osc.edu> 0.6.1-1
- Bump bc_osc_jupyter to 0.6.1 (jnicklas@osc.edu)

* Tue Apr 17 2018 Jeremy Nicklas <jnicklas@osc.edu> 0.6.0-1
- Bump bc_osc_jupyter to 0.6.0 (jnicklas@osc.edu)

* Wed Mar 28 2018 Jeremy Nicklas <jnicklas@osc.edu> 0.5.0-1
- Bump bc_osc_jupyter to 0.5.0 (jnicklas@osc.edu)

* Tue Mar 06 2018 Jeremy Nicklas <jnicklas@osc.edu> 0.4.1-1
- Bump bc_osc_jupyter to 0.4.1 (jnicklas@osc.edu)

* Tue Mar 06 2018 Jeremy Nicklas <jnicklas@osc.edu>
- Bump bc_osc_jupyter to 0.4.1 (jnicklas@osc.edu)

* Tue Feb 13 2018 Trey Dockendorf <tdockendorf@osc.edu> 0.3.0-1
- new package built with tito

