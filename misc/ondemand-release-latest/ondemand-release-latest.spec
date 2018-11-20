Name:       ondemand-release-web-latest
Version:    1
Release:    2%{?dist}
Summary:    Open OnDemand web repository files

Group:      Applications/System
License:    Apache 2.0
URL:        https://osc.github.io/ood-documentation/
BuildArch:  noarch
Source0:    ondemand-web.repo
Source1:    ondemand-compute.repo
Source2:    RPM-GPG-KEY-ondemand
Obsoletes:  ondemand-release-web

%description
Open OnDemand web repository contains open source and other distributable software for
distributions in RPM format. This package contains the repository configuration
for Yum.

%package -n ondemand-release-compute-latest
Summary:        Open OnDemand compute repository files
Group:          Applications/System
Obsoletes:      ondemand-release-compute

%description -n ondemand-release-compute-latest
Open OnDemand compute repository contains open source and other distributable software for
distributions in RPM format. This package contains the repository configuration
for Yum.

%prep
exit 0

%build
exit 0

%install
install -Dpm0644 %{SOURCE0} %{buildroot}%{_sysconfdir}/yum.repos.d/ondemand-web.repo
install -Dpm0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/yum.repos.d/ondemand-compute.repo
sed "s/\$DIST/$(echo %{?dist} | cut -d. -f2)/g" -i %{buildroot}%{_sysconfdir}/yum.repos.d/ondemand-*.repo
install -Dpm0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand
install -Dpm0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand-compute


%clean
exit 0

%files
%config %{_sysconfdir}/yum.repos.d/ondemand-web.repo
%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand

%files -n ondemand-release-compute-latest
%config %{_sysconfdir}/yum.repos.d/ondemand-compute.repo
%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand-compute


%changelog
* Tue Nov 20 2018 Trey Dockendorf <tdockendorf@osc.edu> 1-2
- Rework latest RPM (tdockendorf@osc.edu)

* Wed Feb 28 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3-1
- new package built with tito


