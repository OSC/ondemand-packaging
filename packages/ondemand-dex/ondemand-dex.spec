%define go_version 1.13.9

%define debug_package %{nil}
%define __strip /bin/true

%define appname dex
%define confdir %{_sysconfdir}/ood/%{appname}

Name:       ondemand-%{appname}
Version:    2.23.0
Release:    2%{?dist}
Summary:    A federated OpenID Connect provider

Group:      System Environment/Daemons
License:    Apache-2.0
URL:        https://github.com/dexidp/dex
Source0:    https://github.com/dexidp/dex/archive/v%{version}.tar.gz
Source1:    https://dl.google.com/go/go%{go_version}.linux-amd64.tar.gz
Source2:    ondemand-dex-theme

BuildRequires:  ondemand-scldevel
BuildRequires:  systemd
BuildRequires:  git
Requires:       systemd
Requires:       %{?scl_ondemand_prefix_apache}mod_auth_openidc

%description
A federated OpenID Connect provider packaged for Open OnDemand

%prep
%setup -q -n %{appname}-%{version}
%__tar -C %{_buildrootdir} -xzf %{SOURCE1}
export PATH=$PATH:%{_buildrootdir}/go/bin
GOPATH=$(go env GOPATH)
%__mkdir_p $GOPATH/src/github.com/dexidp/dex
%__cp -R ./* $GOPATH/src/github.com/dexidp/dex/

%build
export PATH=$PATH:%{_buildrootdir}/go/bin
GOPATH=$(go env GOPATH)
cd $GOPATH/src/github.com/dexidp/dex/
%__make bin/dex


%install
export PATH=$PATH:%{_buildrootdir}/go/bin
GOPATH=$(go env GOPATH)
cd $GOPATH/src/github.com/dexidp/dex/
%__install -p -m 755 -D bin/dex %{buildroot}%{_exec_prefix}/local/bin/%{name}
%__install -p -m 600 -D examples/config-dev.yaml %{buildroot}%{confdir}/config.yaml
touch %{buildroot}%{confdir}/dex.db
%__mkdir_p %{buildroot}%{_datadir}/%{name}
%__cp -R web %{buildroot}%{_datadir}/%{name}/web
%__cp -R %{SOURCE2} %{buildroot}%{_datadir}/%{name}/web/themes/ondemand
%__mkdir_p %{buildroot}%{_unitdir}
%__cat >> %{buildroot}%{_unitdir}/%{name}.service << EOF
[Unit]
Description=OnDemand Dex - A federated OpenID Connect provider packaged for OnDemand
After=network-online.target multi-user.target
Wants=network-online.target

[Service]
WorkingDirectory=%{_datadir}/%{name}
ExecStart=%{_exec_prefix}/local/bin/%{name} serve %{confdir}/config.yaml
User=%{name}
Group=%{name}

[Install]
WantedBy=multi-user.target
EOF

%clean
%__rm -rf %{_buildrootdir}/go

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
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/*
%{_unitdir}/%{name}.service
