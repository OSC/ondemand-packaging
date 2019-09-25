Name:       ondemand-release-web-latest
Version:    1
Release:    4
Summary:    Open OnDemand web repository files

Group:      Applications/System
License:    Apache 2.0
URL:        https://osc.github.io/ood-documentation/
BuildArch:  noarch
Source0:    ondemand-web.repo
Source1:    ondemand-compute.repo
Source2:    RPM-GPG-KEY-ondemand
Source3:    ondemand-centos-scl.repo
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
install -Dpm0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand
install -Dpm0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand-compute
mkdir -p %{buildroot}%{_docdir}/%{name}
install -Dpm0644 %{SOURCE3} %{buildroot}%{_docdir}/%{name}/ondemand-centos-scl.repo

%clean
exit 0

%post
if [ -f /etc/os-release ]; then
    source /etc/os-release
    if [ "$ID" = "centos" -a "$VERSION_ID" = "7" ]; then
        ln -snf %{_docdir}/%{name}/ondemand-centos-scl.repo %{_sysconfdir}/yum.repos.d/ondemand-centos-scl.repo
    fi
fi

%files
%config %{_sysconfdir}/yum.repos.d/ondemand-web.repo
%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand
%config %{_docdir}/%{name}/ondemand-centos-scl.repo
%ghost %{_sysconfdir}/yum.repos.d/ondemand-centos-scl.repo

%files -n ondemand-release-compute-latest
%config %{_sysconfdir}/yum.repos.d/ondemand-compute.repo
%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand-compute


%changelog
* Tue Nov 20 2018 Trey Dockendorf <tdockendorf@osc.edu> 1-2
- Rework latest RPM (tdockendorf@osc.edu)

* Wed Feb 28 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3-1
- new package built with tito


