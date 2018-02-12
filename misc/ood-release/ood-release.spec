Name:       ood-release-web
Version:    1.2
Release:    1%{?dist}
Summary:    Open OnDemand web repository files

Group:      Applications/System
License:    Apache 2.0
URL:        https://osc.github.io/ood-documentation/
BuildArch:  noarch
Source0:    ood-web.repo
Source1:    ood-compute.repo

%description
Open OnDemand web repository contains open source and other distributable software for
distributions in RPM format. This package contains the repository configuration
for Yum.

%package -n ood-release-compute
Summary:        Open OnDemand compute repository files
Group:          Applications/System

%description -n ood-release-compute
Open OnDemand compute repository contains open source and other distributable software for
distributions in RPM format. This package contains the repository configuration
for Yum.

%prep
exit 0

%build
exit 0

%install
install -Dpm0644 %{SOURCE0} %{buildroot}%{_sysconfdir}/yum.repos.d/ood-web.repo
install -Dpm0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/yum.repos.d/ood-compute.repo
sed "s/\$DIST/$(echo %{?dist} | cut -d. -f2)/g" -i %{buildroot}%{_sysconfdir}/yum.repos.d/ood-*.repo


%clean
exit 0

%files
%config %{_sysconfdir}/yum.repos.d/ood-web.repo

%files -n ood-release-compute
%config %{_sysconfdir}/yum.repos.d/ood-compute.repo


%changelog

