%define go_version 1.13.9

%define debug_package %{nil}
%define __strip /bin/true

%define appname dex
%define confdir %{_sysconfdir}/ood/%{appname}

Name:       ondemand-%{appname}
Version:    2.23.0
Release:    1%{?dist}
Summary:    A federated OpenID Connect provider

Group:      System Environment/Daemons
License:    Apache-2.0
URL:        https://github.com/dexidp/dex
Source0:    https://github.com/dexidp/dex/archive/v%{version}.tar.gz
Source1:    https://dl.google.com/go/go%{go_version}.linux-amd64.tar.gz

BuildRequires:  ondemand-scldevel
BuildRequires:  systemd
BuildRequires:  git
Requires:       systemd
Requires:       %{?scl_ondemand_prefix_apache}mod_auth_openidc

%description
A federated OpenID Connect provider packaged for Open OnDemand

%prep
%setup -q -n %{appname}-%{version}
%__mkdir ./go
%__tar -C ./go -xzf %{SOURCE1}

%build
export PATH=$PATH:./go/go/bin
%__make


%install
%__install -p -m 755 -D bin/dex %{buildroot}%{_exec_prefix}/local/bin/%{name}
%__install -p -m 600 -D examples/config-dev.yaml %{buildroot}%{confdir}/config.yaml
touch %{buildroot}%{confdir}/dex.db
%__mkdir_p %{buildroot}%{_unitdir}
%__cat >> %{buildroot}%{_unitdir}/%{name}.service << EOF
[Unit]
Description=OnDemand Dex - A federated OpenID Connect provider packaged for OnDemand
After=network-online.target multi-user.target
Wants=network-online.target

[Service]
ExecStart=%{_exec_prefix}/local/bin/%{name} serve %{confdir}/config.yaml
User=%{name}
Group=%{name}

[Install]
WantedBy=multi-user.target
EOF

%pre
getent group %{name} > /dev/null || groupadd -r %{name}
getent passwd %{name} > /dev/null || useradd -r -d /var/lib/%{name} -g %{name} -s /sbin/nologin -c "OnDemand Dex" %{name}

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%{_exec_prefix}/local/bin/%{name}
%dir %attr(0700,%{name},%{name}) %{confdir}
%config(noreplace,missingok) %attr(0600,%{name},%{name}) %{confdir}/config.yaml
%ghost %{confdir}/dex.db
%{_unitdir}/%{name}.service
