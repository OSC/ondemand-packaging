%{!?package_release: %define package_release 1}

Name:       ondemand-release-web-latest
Version:    %{package_version}
Release:    %{package_release}%{?dist}
Summary:    Open OnDemand web repository files

Group:      Applications/System
License:    Apache 2.0
URL:        https://osc.github.io/ood-documentation/
BuildArch:  noarch
Source0:    ondemand-web.repo
Source1:    ondemand-compute.repo
Source2:    RPM-GPG-KEY-ondemand
Source3:    RPM-GPG-KEY-ondemand-SHA512
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
mkdir -p %{buildroot}%{_sysconfdir}/yum.repos.d
DIST=$(echo "%{dist}" | sed -r 's|\.(.+)|\1|g')
sed -e "s|@DIST@|$DIST|g" %{SOURCE0} > %{buildroot}%{_sysconfdir}/yum.repos.d/ondemand-web.repo
sed -e "s|@DIST@|$DIST|g" %{SOURCE1} > %{buildroot}%{_sysconfdir}/yum.repos.d/ondemand-compute.repo
mkdir -p %{buildroot}%{_datadir}/%{name}
install -Dpm0644 %{SOURCE2} %{buildroot}%{_datadir}/%{name}/RPM-GPG-KEY-ondemand
install -Dpm0644 %{SOURCE2} %{buildroot}%{_datadir}/ondemand-release-compute/RPM-GPG-KEY-ondemand-compute
install -Dpm0644 %{SOURCE3} %{buildroot}%{_datadir}/%{name}/RPM-GPG-KEY-ondemand-SHA512
install -Dpm0644 %{SOURCE3} %{buildroot}%{_datadir}/ondemand-release-compute/RPM-GPG-KEY-ondemand-compute-SHA512
mkdir -p %{buildroot}%{_docdir}/%{name}

%clean
exit 0

%post
source /etc/os-release
if [[ "$VERSION_ID" =~ ^8 ]] ; then
  install -m 0644 %{_datadir}/%{name}/RPM-GPG-KEY-ondemand %{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand
else
  install -m 0644 %{_datadir}/%{name}/RPM-GPG-KEY-ondemand-SHA512 %{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand
fi

%post -n ondemand-release-compute-latest
source /etc/os-release
if [[ "$VERSION_ID" =~ ^8 ]] ; then
  install -m 0644 %{_datadir}/ondemand-release-compute/RPM-GPG-KEY-ondemand-compute %{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand-compute
else
  install -m 0644 %{_datadir}/ondemand-release-compute/RPM-GPG-KEY-ondemand-compute-SHA512 %{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand-compute
fi

%files
%config %{_sysconfdir}/yum.repos.d/ondemand-web.repo
%{_datadir}/%{name}/*
%ghost %{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand

%files -n ondemand-release-compute-latest
%config %{_sysconfdir}/yum.repos.d/ondemand-compute.repo
%{_datadir}/ondemand-release-compute/*
%ghost %{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ondemand-compute


%changelog
* Tue Nov 20 2018 Trey Dockendorf <tdockendorf@osc.edu> 1-2
- Rework latest RPM (tdockendorf@osc.edu)

* Wed Feb 28 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3-1
- new package built with tito


