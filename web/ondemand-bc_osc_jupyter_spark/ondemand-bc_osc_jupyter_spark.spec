# Disable debuginfo as it causes issues with bundled gems that build libraries
%global debug_package %{nil}
%global repo_name bc_osc_jupyter_spark
%global app_name bc_osc_jupyter_spark

Name:     ondemand-%{app_name}
Version:  0.2.1
Release:  1%{?dist}
Summary:  Batch Connect - OSC Jupyter Notebook Server + Spark

Group:    System Environment/Daemons
License:  MIT
URL:      https://github.com/OSC/%{repo_name}
Source0:  https://github.com/OSC/%{repo_name}/archive/v%{version}.tar.gz

Requires: ondemand

# Disable automatic dependencies as it causes issues with bundled gems and
# node.js packages used in the apps
AutoReqProv: no

%description
An interactive app designed for OSC OnDemand that launches a Jupyter Notebook server and an Apache Spark cluster within an Owens batch job.


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
* Mon Apr 23 2018 Jeremy Nicklas <jnicklas@osc.edu> 0.2.1-1
- Bump bc_osc_jupyter_spark to 0.2.1 (jnicklas@osc.edu)

* Wed Mar 28 2018 Jeremy Nicklas <jnicklas@osc.edu> 0.2.0-1
- Bump bc_osc_jupyter_spark to 0.2.0 (jnicklas@osc.edu)

* Tue Mar 06 2018 Jeremy Nicklas <jnicklas@osc.edu> 0.1.0-1
- Bump bc_osc_jupyter_spark to 0.1.0 (jnicklas@osc.edu)

* Tue Feb 13 2018 Trey Dockendorf <tdockendorf@osc.edu> 0.0.3-1
- new package built with tito

