%{!?ncpus: %define ncpus 12}
%global package_name ondemand
%global package_version 1.4.10
%global package_release 1

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
BuildRequires:   rh-ruby24, rh-ruby24-rubygem-rake, rh-ruby24-rubygem-bundler, rh-ruby24-ruby-devel, rh-nodejs6, rh-git29
Requires:        sudo, lsof, sqlite-devel, cronie, wget, curl, make
Requires:        httpd24, httpd24-mod_ssl, httpd24-mod_ldap
Requires:        nginx = 100:1.14.0
Requires:        passenger = 5.3.7
Requires:        rh-ruby24, rh-ruby24-rubygem-rake, rh-ruby24-rubygem-bundler, rh-ruby24-ruby-devel, rh-ruby24-rubygems, rh-ruby24-rubygems-devel
Requires:        rh-nodejs6, rh-git29

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
export SCL_PKGS="rh-ruby24 rh-nodejs6 rh-git29"
export SCL_SOURCE=$(command -v scl_source)
if [ "$SCL_SOURCE" ]; then
  source "$SCL_SOURCE" enable $SCL_PKGS &> /dev/null || :
fi
rake -mj%{ncpus}


%install
export SCL_PKGS="rh-ruby24"
export SCL_SOURCE=$(command -v scl_source)
if [ "$SCL_SOURCE" ]; then
  source "$SCL_SOURCE" enable $SCL_PKGS &> /dev/null || :
fi
rake install PREFIX=%{buildroot}/opt/ood
%__rm %{buildroot}/opt/ood/apps/*/log/production.log
echo "%{package_version}" > %{buildroot}/opt/ood/VERSION
%__mkdir_p %{buildroot}%{_localstatedir}/www/ood/public
%__mkdir_p %{buildroot}%{_localstatedir}/www/ood/discover
%__mkdir_p %{buildroot}%{_localstatedir}/www/ood/register
%__mkdir_p %{buildroot}%{_localstatedir}/www/ood/apps/sys
%__mkdir_p %{buildroot}%{_localstatedir}/www/ood/apps/usr
%__mv %{buildroot}/opt/ood/apps/dashboard %{buildroot}%{_localstatedir}/www/ood/apps/sys/dashboard
%__mv %{buildroot}/opt/ood/apps/shell %{buildroot}%{_localstatedir}/www/ood/apps/sys/shell
%__mv %{buildroot}/opt/ood/apps/files %{buildroot}%{_localstatedir}/www/ood/apps/sys/files
# Work around issues where node modules go from a directory to symlink which breaks RPM updates
if [ -L %{buildroot}%{_localstatedir}/www/ood/apps/sys/files/node_modules/cloudcmd ]; then
    pushd %{buildroot}%{_localstatedir}/www/ood/apps/sys/files/node_modules
    dest=$(readlink %{buildroot}%{_localstatedir}/www/ood/apps/sys/files/node_modules/cloudcmd)
    unlink %{buildroot}%{_localstatedir}/www/ood/apps/sys/files/node_modules/cloudcmd
    cp -pr $dest %{buildroot}%{_localstatedir}/www/ood/apps/sys/files/node_modules/
    popd
fi
%__mv %{buildroot}/opt/ood/apps/file-editor %{buildroot}%{_localstatedir}/www/ood/apps/sys/file-editor
%__mv %{buildroot}/opt/ood/apps/activejobs %{buildroot}%{_localstatedir}/www/ood/apps/sys/activejobs
%__mv %{buildroot}/opt/ood/apps/myjobs %{buildroot}%{_localstatedir}/www/ood/apps/sys/myjobs
%__mv %{buildroot}/opt/ood/apps/bc_desktop %{buildroot}%{_localstatedir}/www/ood/apps/sys/bc_desktop
%__mkdir_p %{buildroot}%{_sharedstatedir}/nginx/config/puns
%__mkdir_p %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys
%__mkdir_p %{buildroot}%{_sharedstatedir}/nginx/config/apps/usr
%__mkdir_p %{buildroot}%{_sharedstatedir}/nginx/config/apps/dev

%__install -D -m 644 build/ood-portal-generator/share/ood_portal_example.yml \
    %{buildroot}%{_sysconfdir}/ood/config/ood_portal.yml
%__mkdir_p %{buildroot}/opt/rh/httpd24/root/etc/httpd/conf.d
touch %{buildroot}/opt/rh/httpd24/root/etc/httpd/conf.d/ood-portal.conf

%__install -D -m 644 build/nginx_stage/share/nginx_stage_example.yml \
    %{buildroot}%{_sysconfdir}/ood/config/nginx_stage.yml
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/dashboard.conf
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/shell.conf
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/files.conf
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/file-editor.conf
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/activejobs.conf
touch %{buildroot}%{_sharedstatedir}/nginx/config/apps/sys/myjobs.conf

%__mkdir_p %{buildroot}%{_sysconfdir}/sudoers.d
%__cat >> %{buildroot}%{_sysconfdir}/sudoers.d/ood << EOF
Defaults:apache !requiretty, !authenticate
apache ALL=(ALL) NOPASSWD: /opt/ood/nginx_stage/sbin/nginx_stage
EOF
%__chmod 440 %{buildroot}%{_sysconfdir}/sudoers.d/ood

%__mkdir_p %{buildroot}%{_sysconfdir}/cron.d
%__cat >> %{buildroot}%{_sysconfdir}/cron.d/ood << EOF
#!/bin/bash
PATH=/sbin:/bin:/usr/sbin:/usr/bin
0 */2 * * * root [ -f /opt/ood/nginx_stage/sbin/update_nginx_stage ] && /opt/ood/nginx_stage/sbin/update_nginx_stage --quiet
EOF

%if %{with systemd}
%__mkdir_p %{buildroot}%{_sysconfdir}/systemd/system/httpd24-httpd.service.d
%__cat >> %{buildroot}%{_sysconfdir}/systemd/system/httpd24-httpd.service.d/ood.conf << EOF
[Service]
KillSignal=SIGTERM
KillMode=process
PrivateTmp=false
EOF
%__chmod 444 %{buildroot}%{_sysconfdir}/systemd/system/httpd24-httpd.service.d/ood.conf
%endif


%post
%__sed -i 's/^HTTPD24_HTTPD_SCLS_ENABLED=.*/HTTPD24_HTTPD_SCLS_ENABLED="httpd24 rh-ruby24"/' \
    /opt/rh/httpd24/service-environment

%if %{with systemd}
/bin/systemctl daemon-reload &>/dev/null || :
%endif

# These NGINX app configs need to exist before rebuilding them
touch %{_sharedstatedir}/nginx/config/apps/sys/dashboard.conf
touch %{_sharedstatedir}/nginx/config/apps/sys/shell.conf
touch %{_sharedstatedir}/nginx/config/apps/sys/files.conf
touch %{_sharedstatedir}/nginx/config/apps/sys/file-editor.conf
touch %{_sharedstatedir}/nginx/config/apps/sys/activejobs.conf
touch %{_sharedstatedir}/nginx/config/apps/sys/myjobs.conf


%preun
if [ "$1" -eq 0 ]; then
%__sed -i 's/^HTTPD24_HTTPD_SCLS_ENABLED=.*/HTTPD24_HTTPD_SCLS_ENABLED="httpd24"/' \
    /opt/rh/httpd24/service-environment
/opt/ood/nginx_stage/sbin/nginx_stage nginx_clean --force &>/dev/null || :
fi


%postun
if [ "$1" -eq 0 ]; then
%if %{with systemd}
/bin/systemctl daemon-reload &>/dev/null || :
/bin/systemctl try-restart httpd24-httpd.service httpd24-htcacheclean.service &>/dev/null || :
%else
/sbin/service httpd24-httpd condrestart &>/dev/null
/sbin/service httpd24-htcacheclean condrestart &>/dev/null
exit 0
%endif
fi


%posttrans
# Rebuild NGINX app configs and restart PUNs w/ no active connections
/opt/ood/nginx_stage/sbin/update_nginx_stage &>/dev/null || :

# Restart apps in case PUN wasn't restarted
touch %{_localstatedir}/www/ood/apps/sys/dashboard/tmp/restart.txt
touch %{_localstatedir}/www/ood/apps/sys/shell/tmp/restart.txt
touch %{_localstatedir}/www/ood/apps/sys/files/tmp/restart.txt
touch %{_localstatedir}/www/ood/apps/sys/file-editor/tmp/restart.txt
touch %{_localstatedir}/www/ood/apps/sys/activejobs/tmp/restart.txt
touch %{_localstatedir}/www/ood/apps/sys/myjobs/tmp/restart.txt

# Rebuild Apache config and restart Apache httpd if config changed
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
%exclude %{_localstatedir}/www/ood/apps/sys/*/tmp/*

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
%ghost %{_sharedstatedir}/nginx/config/apps/sys/dashboard.conf
%ghost %{_sharedstatedir}/nginx/config/apps/sys/shell.conf
%ghost %{_sharedstatedir}/nginx/config/apps/sys/files.conf
%ghost %{_sharedstatedir}/nginx/config/apps/sys/file-editor.conf
%ghost %{_sharedstatedir}/nginx/config/apps/sys/activejobs.conf
%ghost %{_sharedstatedir}/nginx/config/apps/sys/myjobs.conf

%config(noreplace) %{_sysconfdir}/sudoers.d/ood
%config(noreplace) %{_sysconfdir}/cron.d/ood
%ghost /opt/rh/httpd24/root/etc/httpd/conf.d/ood-portal.conf
%if %{with systemd}
%config(noreplace) %{_sysconfdir}/systemd/system/httpd24-httpd.service.d/ood.conf
%endif


%changelog
* Wed Jan 02 2019 Morgan Rodgers <mrodgers@osc.edu> 1.4.9-1
- Update OnDemand to v 1.4.9 (mrodgers@osc.edu)

* Mon Dec 31 2018 Morgan Rodgers <mrodgers@osc.edu> 1.4.8-1
- Update OnDemand to 1.4.8 (mrodgers@osc.edu)

* Thu Dec 27 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.4.7-1
- Update OnDemand to 1.4.7 (tdockendorf@osc.edu)

* Fri Dec 21 2018 Morgan Rodgers <mrodgers@osc.edu> 1.4.6-3
- Revert ood_portal_generator version string (mrodgers@osc.edu)

* Thu Dec 20 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.4.5-3
- Change cloudcmd symlink to directory during RPM build to avoid warnings
  during yum update (tdockendorf@osc.edu)

* Thu Dec 20 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.4.5-2
- Fix so that cloudcmd node module directory is able to be replaced with a
  symlink (tdockendorf@osc.edu)
- Actually use package_version for version (tdockendorf@osc.edu)

* Wed Dec 19 2018 Morgan Rodgers <mrodgers@osc.edu> 1.4.5-1
- OnDemand 1.4.5 release (mrodgers@osc.edu)

* Tue Dec 04 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.4.4-4
- Fix release (tdockendorf@osc.edu)

* Tue Dec 04 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.4.4-3
- Fix dependency on nginx to use correct epoch number

* Tue Dec 04 2018 Morgan Rodgers <mrodgers@osc.edu> 1.4.4-2
- Ondemand 1.4.4 (mrodgers@osc.edu)

* Fri Oct 19 2018 Morgan Rodgers <mrodgers@osc.edu> 1.4.3-2
- Ondemand dependency update and switch to monorepo (mrodgers@osc.edu)

* Fri Sep 14 2018 Morgan Rodgers <mrodgers@osc.edu> 1.4.2-2
- Bump OOD version to v1.4.2 (mrodgers@osc.edu)

* Thu Sep 13 2018 Morgan Rodgers <mrodgers@osc.edu> 1.4.1-2
- Bump OOD version to 1.4.1 (mrodgers@osc.edu)
- Bump ondemand version to v1.4.0 (mrodgers@osc.edu)

* Wed Jul 18 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3.7-2
- Remove production.log (tdockendorf@osc.edu)

* Tue May 15 2018 Jeremy Nicklas <jnicklas@osc.edu> 1.3.7-1
- Bump ondemand to 1.3.7 (jnicklas@osc.edu)

* Mon Apr 30 2018 Jeremy Nicklas <jnicklas@osc.edu> 1.3.6-1
- Bump ondemand to 1.3.6 (jnicklas@osc.edu)

* Fri Apr 20 2018 Jeremy Nicklas <jnicklas@osc.edu> 1.3.5-2
- add version file for ondemand (jnicklas@osc.edu)

* Mon Apr 09 2018 Jeremy Nicklas <jnicklas@osc.edu> 1.3.5-1
- Bump ondemand to 1.3.5 (jnicklas@osc.edu)

* Fri Apr 06 2018 Jeremy Nicklas <jnicklas@osc.edu> 1.3.4-1
- Bump ondemand to 1.3.4 (jnicklas@osc.edu)

* Tue Mar 27 2018 Jeremy Nicklas <jnicklas@osc.edu> 1.3.3-1
- Bump ondemand to 1.3.3 (jnicklas@osc.edu)

* Mon Mar 26 2018 Jeremy Nicklas <jnicklas@osc.edu> 1.3.2-1
- Bump ondemand to 1.3.2 (jnicklas@osc.edu)
- set web server configs as ghost (jnicklas@osc.edu)
- Use macros where possible (tdockendorf@osc.edu)

* Wed Feb 28 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3.1-5
- Set modes to be more restrictive. Matches OSC puppet environment but still
  functions the same (tdockendorf@osc.edu)

* Wed Feb 28 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3.1-4
- Try to speed up builds by doing rake in parallel (tdockendorf@osc.edu)
- Set sudo config to noreplace (tdockendorf@osc.edu)

* Wed Feb 28 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3.1-3
- Move %%posttrans into %%post (#23) Run daemon-reload for systemd in %%post
  and %%postun (#22) Make systemd unit file override %%config(noreplace)
  (tdockendorf@osc.edu)

* Tue Feb 27 2018 Jeremy Nicklas <jnicklas@osc.edu> 1.3.1-2
- set apache config as ghost (jnicklas@osc.edu)

* Tue Feb 27 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3.1-1
- Bump ondemand to 1.3.1 (jnicklas@osc.edu)

* Wed Feb 14 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3.0-1
- update ondemand to v1.3.0 (jeremywnicklas@gmail.com)


