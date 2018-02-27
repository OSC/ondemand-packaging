%global package_name ondemand
%global package_version 1.3.1
%global package_release 2

Name:      %{package_name}
Version:   %{package_version}
Release:   %{package_release}%{?dist}
Summary:   Web server that provides users access to HPC resources

Group:     System Environment/Daemons
License:   MIT
URL:       https://osc.github.io/Open-OnDemand
Source0:   https://github.com/OSC/%{package_name}/archive/v%{package_version}.tar.gz

# Disable debuginfo as it causes issues with bundled gems that build libraries
%global debug_package %{nil}

# Check if system uses systemd by default
%if 0%{?rhel} >= 7 || 0%{?fedora} >= 16
%bcond_without systemd
%else
%bcond_with systemd
%endif

# Disable automatic dependencies as it causes issues with bundled gems and
# node.js packages used in the apps
AutoReqProv:     no

BuildRequires:   sqlite-devel, curl, make
BuildRequires:   rh-ruby22, rh-ruby22-rubygem-rake, rh-ruby22-rubygem-bundler, rh-ruby22-ruby-devel, nodejs010, git19
Requires:        sudo, lsof, sqlite-devel, cronie, wget, curl, make
Requires:        httpd24, httpd24-mod_ssl, httpd24-mod_ldap
Requires:        nginx16, rh-passenger40
Requires:        rh-ruby22, rh-ruby22-rubygem-rake, rh-ruby22-rubygem-bundler, rh-ruby22-ruby-devel, rh-ruby22-rubygems, rh-ruby22-rubygems-devel
Requires:        nodejs010, git19

%if %{with systemd}
BuildRequires: systemd
%{?systemd_requires}
%endif

%description
Open OnDemand is an open source release of OSC's OnDemand platform to provide
HPC access via a web browser, supporting web based file management, shell
access, job submission and interactive work on compute nodes.


%prep
%setup -q -n %{package_name}-%{package_version}


%build
export SCL_PKGS="rh-ruby22 nodejs010 git19"
export SCL_SOURCE=$(command -v scl_source)
if [ "$SCL_SOURCE" ]; then
  source "$SCL_SOURCE" enable $SCL_PKGS &> /dev/null || :
fi
rake


%install
export SCL_PKGS="rh-ruby22"
export SCL_SOURCE=$(command -v scl_source)
if [ "$SCL_SOURCE" ]; then
  source "$SCL_SOURCE" enable $SCL_PKGS &> /dev/null || :
fi
rake install PREFIX=%{buildroot}/opt/ood
mkdir -p %{buildroot}%{_localstatedir}/www/ood/public
mkdir -p %{buildroot}%{_localstatedir}/www/ood/discover
mkdir -p %{buildroot}%{_localstatedir}/www/ood/register
mkdir -p %{buildroot}%{_localstatedir}/www/ood/apps/sys
mkdir -p %{buildroot}%{_localstatedir}/www/ood/apps/usr
mv %{buildroot}/opt/ood/apps/dashboard %{buildroot}%{_localstatedir}/www/ood/apps/sys/dashboard
mv %{buildroot}/opt/ood/apps/shell %{buildroot}%{_localstatedir}/www/ood/apps/sys/shell
mv %{buildroot}/opt/ood/apps/files %{buildroot}%{_localstatedir}/www/ood/apps/sys/files
mv %{buildroot}/opt/ood/apps/file-editor %{buildroot}%{_localstatedir}/www/ood/apps/sys/file-editor
mv %{buildroot}/opt/ood/apps/activejobs %{buildroot}%{_localstatedir}/www/ood/apps/sys/activejobs
mv %{buildroot}/opt/ood/apps/myjobs %{buildroot}%{_localstatedir}/www/ood/apps/sys/myjobs
mv %{buildroot}/opt/ood/apps/bc_desktop %{buildroot}%{_localstatedir}/www/ood/apps/sys/bc_desktop
mkdir -p %{buildroot}%{_sharedstatedir}/nginx/config/puns
mkdir -p %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys
mkdir -p %{buildroot}%{_sharedstatedir}/nginx/config/apps/usr
mkdir -p %{buildroot}%{_sharedstatedir}/nginx/config/apps/dev

install -D -m 644 build/ood-portal-generator/share/ood_portal_example.yml \
    %{buildroot}%{_sysconfdir}/ood/config/ood_portal.yml
mkdir -p %{buildroot}/opt/rh/httpd24/root/etc/httpd/conf.d
%{buildroot}/opt/ood/ood-portal-generator/bin/generate \
    -c %{buildroot}%{_sysconfdir}/ood/config/ood_portal.yml \
    -o %{buildroot}/opt/rh/httpd24/root/etc/httpd/conf.d/ood-portal.conf

install -D -m 644 build/nginx_stage/share/nginx_stage_example.yml \
    %{buildroot}%{_sysconfdir}/ood/config/nginx_stage.yml
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/dashboard.conf
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/shell.conf
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/files.conf
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/file-editor.conf
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/activejobs.conf
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/myjobs.conf
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/bc_desktop.conf
(
export NGINX_STAGE_CONFIG_FILE=$(mktemp)
cat > $NGINX_STAGE_CONFIG_FILE << EOF
app_config_path:
  sys: '%{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/%%{name}.conf'
EOF
%{buildroot}/opt/ood/nginx_stage/sbin/nginx_stage \
    app_reset --sub-uri=/pun
rm -f $NGINX_STAGE_CONFIG_FILE
)

mkdir -p %{buildroot}%{_sysconfdir}/sudoers.d
cat >> %{buildroot}%{_sysconfdir}/sudoers.d/ood << EOF
Defaults:apache !requiretty, !authenticate
apache ALL=(ALL) NOPASSWD: /opt/ood/nginx_stage/sbin/nginx_stage
EOF
chmod 600 %{buildroot}%{_sysconfdir}/sudoers.d/ood

mkdir -p %{buildroot}%{_sysconfdir}/cron.d
cat >> %{buildroot}%{_sysconfdir}/cron.d/ood << EOF
#!/bin/bash
PATH=/sbin:/bin:/usr/sbin:/usr/bin
0 */2 * * * root [ -f /opt/ood/nginx_stage/sbin/update_nginx_stage ] && /opt/ood/nginx_stage/sbin/update_nginx_stage --quiet
EOF

%if %{with systemd}
mkdir -p %{buildroot}%{_sysconfdir}/systemd/system/httpd24-httpd.service.d
cat >> %{buildroot}%{_sysconfdir}/systemd/system/httpd24-httpd.service.d/ood.conf << EOF
[Service]
KillSignal=SIGTERM
KillMode=process
PrivateTmp=false
EOF
%endif


%post
sed -i 's/^HTTPD24_HTTPD_SCLS_ENABLED=.*/HTTPD24_HTTPD_SCLS_ENABLED="httpd24 rh-ruby22"/' \
    /opt/rh/httpd24/service-environment
/opt/ood/nginx_stage/sbin/update_nginx_stage &>/dev/null || :
touch %{_localstatedir}/www/ood/apps/sys/dashboard/tmp/restart.txt
touch %{_localstatedir}/www/ood/apps/sys/shell/tmp/restart.txt
touch %{_localstatedir}/www/ood/apps/sys/files/tmp/restart.txt
touch %{_localstatedir}/www/ood/apps/sys/file-editor/tmp/restart.txt
touch %{_localstatedir}/www/ood/apps/sys/activejobs/tmp/restart.txt
touch %{_localstatedir}/www/ood/apps/sys/myjobs/tmp/restart.txt


%preun
if [ "$1" -eq 0 ]; then
sed -i 's/^HTTPD24_HTTPD_SCLS_ENABLED=.*/HTTPD24_HTTPD_SCLS_ENABLED="httpd24"/' \
    /opt/rh/httpd24/service-environment
/opt/ood/nginx_stage/sbin/nginx_stage nginx_clean --force &>/dev/null || :
fi


%postun
if [ "$1" -eq 0 ]; then
%if %{with systemd}
/bin/systemctl try-restart httpd24-httpd.service httpd24-htcacheclean.service &>/dev/null || :
%else
/sbin/service httpd24-httpd condrestart &>/dev/null
/sbin/service httpd24-htcacheclean condrestart &>/dev/null
exit 0
%endif
fi


%posttrans
if /opt/ood/ood-portal-generator/sbin/update_ood_portal &>/dev/null; then
%if %{with systemd}
/bin/systemctl try-restart httpd24-httpd.service httpd24-htcacheclean.service &>/dev/null || :
%else
/sbin/service httpd24-httpd condrestart &>/dev/null
/sbin/service httpd24-htcacheclean condrestart &>/dev/null
exit 0
%endif
fi


%files
%defattr(-,root,root)

/opt/ood
%{_localstatedir}/www/ood/apps/sys/dashboard
%{_localstatedir}/www/ood/apps/sys/shell
%{_localstatedir}/www/ood/apps/sys/files
%{_localstatedir}/www/ood/apps/sys/file-editor
%{_localstatedir}/www/ood/apps/sys/activejobs
%{_localstatedir}/www/ood/apps/sys/myjobs
%{_localstatedir}/www/ood/apps/sys/bc_desktop

%dir %{_localstatedir}/www/ood
%dir %{_localstatedir}/www/ood/public
%dir %{_localstatedir}/www/ood/register
%dir %{_localstatedir}/www/ood/discover
%dir %{_localstatedir}/www/ood/apps
%dir %{_localstatedir}/www/ood/apps/sys
%dir %{_localstatedir}/www/ood/apps/usr

%dir %{_sysconfdir}/ood
%dir %{_sysconfdir}/ood/config
%config(noreplace,missingok) %{_sysconfdir}/ood/config/nginx_stage.yml
%config(noreplace,missingok) %{_sysconfdir}/ood/config/ood_portal.yml

%dir %{_sharedstatedir}/nginx/config
%dir %{_sharedstatedir}/nginx/config/puns
%dir %{_sharedstatedir}/nginx/config/apps
%dir %{_sharedstatedir}/nginx/config/apps/sys
%dir %{_sharedstatedir}/nginx/config/apps/usr
%dir %{_sharedstatedir}/nginx/config/apps/dev
%config(noreplace,missingok) %{_sharedstatedir}/nginx/config/apps/sys/dashboard.conf
%config(noreplace,missingok) %{_sharedstatedir}/nginx/config/apps/sys/shell.conf
%config(noreplace,missingok) %{_sharedstatedir}/nginx/config/apps/sys/files.conf
%config(noreplace,missingok) %{_sharedstatedir}/nginx/config/apps/sys/file-editor.conf
%config(noreplace,missingok) %{_sharedstatedir}/nginx/config/apps/sys/activejobs.conf
%config(noreplace,missingok) %{_sharedstatedir}/nginx/config/apps/sys/myjobs.conf
%config(noreplace,missingok) %{_sharedstatedir}/nginx/config/apps/sys/bc_desktop.conf

%config %{_sysconfdir}/sudoers.d/ood
%config(noreplace) %{_sysconfdir}/cron.d/ood
%ghost %config(noreplace) /opt/rh/httpd24/root/etc/httpd/conf.d/ood-portal.conf
%if %{with systemd}
%config %{_sysconfdir}/systemd/system/httpd24-httpd.service.d/ood.conf
%endif


%changelog
* Tue Feb 27 2018 Jeremy Nicklas <jnicklas@osc.edu> 1.3.1-2
- set apache config as ghost (jnicklas@osc.edu)

* Tue Feb 27 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3.1-1
- Bump ondemand to 1.3.1 (jnicklas@osc.edu)

* Wed Feb 14 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3.0-1
- update ondemand to v1.3.0 (jeremywnicklas@gmail.com)


