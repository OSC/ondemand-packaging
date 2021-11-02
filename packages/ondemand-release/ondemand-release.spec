Name:       ondemand-release-web
Version:    2.1
Release:    1
Summary:    Open OnDemand web repository files

Group:      Applications/System
License:    Apache 2.0
URL:        https://osc.github.io/ood-documentation/
BuildArch:  noarch
Source0:    ondemand-web.repo
Source1:    ondemand-compute.repo
Source2:    RPM-GPG-KEY-ondemand

%description
Open OnDemand web repository contains open source and other distributable software for
distributions in RPM format. This package contains the repository configuration
for Yum.

%package -n ondemand-release-compute
Summary:        Open OnDemand compute repository files
Group:          Applications/System

%description -n ondemand-release-compute
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
install -Dpm0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand
install -Dpm0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand-compute
mkdir -p %{buildroot}%{_docdir}/%{name}

%clean
exit 0

%post
if [ -L %{_sysconfdir}/yum.repos.d/ondemand-centos-scl.repo ]; then
    unlink %{_sysconfdir}/yum.repos.d/ondemand-centos-scl.repo
fi

%files
%config %{_sysconfdir}/yum.repos.d/ondemand-web.repo
%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand

%files -n ondemand-release-compute
%config %{_sysconfdir}/yum.repos.d/ondemand-compute.repo
%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand-compute


%changelog
* Sun Feb 03 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.5-1
- Bump release to 1.5 (tdockendorf@osc.edu)

* Thu Jan 03 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.4-1
- Bump to 1.4 ./bump-release.py -p 1.3 -n 1.4 (tdockendorf@osc.edu)

* Wed Feb 28 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3-1
- new package built with tito


