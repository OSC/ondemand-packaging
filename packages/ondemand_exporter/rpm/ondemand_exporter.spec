%{!?package_release: %define package_release 1}

%define debug_package %{nil}
%define __strip /bin/true

%define apache_confd /etc/httpd/conf.d

%define go_version 1.23.4
%ifarch x86_64
%define platform amd64
%endif
%ifarch aarch64
%define platform arm64
%endif
%ifarch ppc64le
%define platform ppc64le
%endif

Name:       ondemand_exporter
Version:    %{package_version}
Release:    %{package_release}%{?dist}
Summary:    OnDemand Prometheus Exporter

Group:      System Environment/Daemons
License:    Apache-2.0
URL:        https://github.com/OSC/ondemand_exporter
Source0:    https://github.com/OSC/ondemand_exporter/archive/v%{version}.tar.gz
Source1:    https://dl.google.com/go/go%{go_version}.linux-%{platform}.tar.gz

BuildRequires:  systemd
Requires:       ondemand

%description
OnDemand Prometheus Exporter

%prep
%setup -q -n ondemand_exporter-%{version}
%__tar -C %{_builddir} -xzf %{SOURCE1}

%build
export PATH=$PATH:%{_builddir}/go/bin
%__make build

%install
%__install -p -m 755 -D ondemand_exporter %{buildroot}%{_bindir}/%{name}

%__mkdir_p %{buildroot}%{_unitdir}
%__install files/ondemand_exporter.service %{buildroot}%{_unitdir}/%{name}.service

%__mkdir_p %{buildroot}%{_sysconfdir}/sudoers.d
%__install -m 0440 files/sudo %{buildroot}%{_sysconfdir}/sudoers.d/%{name}

%__mkdir_p %{buildroot}/%{apache_confd}
%__install files/apache.conf %{buildroot}/%{apache_confd}/%{name}.conf

%clean

%pre
getent group %{name} > /dev/null || groupadd -r %{name}
getent passwd %{name} > /dev/null || useradd -r -d /var/lib/%{name} -g %{name} -s /sbin/nologin -c "OnDemand Exporter" %{name}

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%{_bindir}/%{name}
%{_unitdir}/%{name}.service
%config(noreplace,missingok) %{_sysconfdir}/sudoers.d/%{name}
%config(noreplace,missingok) %{apache_confd}/%{name}.conf
