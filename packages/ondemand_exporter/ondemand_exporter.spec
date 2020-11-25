%define debug_package %{nil}
%define __strip /bin/true

%if 0%{?rhel} >= 8
%define apache_confd /etc/httpd/conf.d
%else
%define apache_confd /opt/rh/httpd24/root/etc/httpd/conf.d
%endif

Name:       ondemand_exporter
Version:    0.8.0
Release:    1%{?dist}
Summary:    OnDemand Prometheus Exporter

Group:      System Environment/Daemons
License:    Apache-2.0
URL:        https://github.com/OSC/ondemand_exporter
Source0:    https://github.com/OSC/ondemand_exporter/releases/download/v%{version}/ondemand_exporter-%{version}.linux-amd64.tar.gz

BuildRequires:  systemd
Requires:       ondemand

%description
OnDemand Prometheus Exporter

%prep
%setup -q -n ondemand_exporter-%{version}.linux-amd64

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
