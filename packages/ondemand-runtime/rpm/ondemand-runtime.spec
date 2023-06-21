%global scl ondemand
%global scl_name_base %scl
%global _scl_prefix /opt/ood
%scl_package %scl
%{!?package_release: %define package_release 1}

%if 0%{?rhel} >= 8
%global ruby ruby
%global nodejs nodejs
%global apache httpd
%endif
%if 0%{?rhel} == 7
%global ruby rh-ruby30
%global nodejs rh-nodejs14
%global apache httpd24
%endif
%if 0%{?amzn} == 2023
%global ruby ruby3.2
%global nodejs nodejs
%global apache httpd
%endif
%global ruby_version 3.0
%global ondemand_gem_home %{_datadir}/gems/%{ruby_version}
%global ondemand_apps_gem_home %{ondemand_gem_home}/apps
%global ondemand_core_gem_home %{ondemand_gem_home}/ondemand

# Attempts to speed up builds on non x86_64
%global debug_package %{nil}
%global __os_install_post %{nil}

Name:      ondemand-runtime
Version:   %{package_version}
Release:   %{package_release}%{?dist}
Summary:   Package that handles %{scl} Software Collection.
License:   MIT

BuildRequires:  scl-utils-build
Requires:       scl-utils
%if 0%{?rhel} == 7
Requires:       %{ruby}-runtime
Requires:       %{nodejs}-runtime
Requires:       %{apache}-runtime
%endif
Obsoletes: ondemand-python

%description
Package shipping essential scripts to work with %{scl} Software Collection.

%package -n ondemand-build
Summary: Package shipping basic build configuration
Requires: scl-utils-build
Requires: curl
Requires: make
Requires: zlib-devel
Requires: libxslt-devel

%description -n ondemand-build
Package shipping essential configuration macros to build %{scl} Software Collection.

%package -n ondemand-scldevel
Summary: Package shipping development files for %{scl}

%description -n ondemand-scldevel
Package shipping development files, especially useful for development of
packages depending on %{scl} Software Collection.

%package -n ondemand-ruby
Summary: Meta package for pulling in SCL Ruby %{ruby}
%if 0%{?rhel} >= 8
Requires: %{ruby} >= 3.1, %{ruby} < 3.2
Requires: rubygem-rake
Requires: rubygem-bundler >= 2.1
Requires: ruby-devel
Requires: rubygems
Requires: rubygems-devel
# In some cases this RPM doesn't get pulled in
Requires: rubygem-bigdecimal
Requires: sqlite-devel
%endif
%if 0%{?rhel} == 7
Requires: %{ruby}
Requires: %{ruby}-rubygem-rake
Requires: %{ruby}-rubygem-bundler >= 2.1
Requires: %{ruby}-ruby-devel
Requires: %{ruby}-rubygems
Requires: %{ruby}-rubygems-devel
Requires: ondemand-sqlite-devel
%endif
%if 0%{?amzn} == 2023
Requires: %{ruby}
Requires: %{ruby}-rubygem-rake
Requires: %{ruby}-rubygem-bundler >= 2.1
Requires: %{ruby}-devel
Requires: %{ruby}-rubygems
Requires: rubygems-devel
# In some cases this RPM doesn't get pulled in
Requires: %{ruby}-rubygem-bigdecimal
Requires: sqlite-devel
%endif
Obsoletes: ondemand-rubygem-bundler

%description -n ondemand-ruby
Meta package for pulling in SCL Ruby %{ruby}

%package -n ondemand-nodejs
Summary: Meta package for pulling in SCL nodejs %{nodejs}
%if 0%{?rhel} == 9
Requires: %{nodejs} >= 1:18.0, %{nodejs} < 1:19.0
Requires: npm
%endif
%if 0%{?rhel} == 8
Requires: %{nodejs} >= 1:18.0, %{nodejs} < 1:19.0
Requires: npm
%endif
%if 0%{?rhel} == 7
Requires: %{nodejs}
Requires: %{nodejs}-npm
%endif
%if 0%{?amzn} == 2023
Requires: %{nodejs} >= 1:18.0, %{nodejs} < 1:19.0
Requires: npm
%endif

%description -n ondemand-nodejs
Meta package for pulling in SCL nodejs %{nodejs}

%package -n ondemand-apache
Summary: Meta package for pulling in SCL apache %{apache}
%if 0%{?rhel} >= 8
Requires: %{apache} >= 2.4, %{apache} < 2.5
Requires: httpd-devel
Requires: mod_ssl
Requires: mod_ldap
%endif
%if 0%{?rhel} == 7
Requires: %{apache}
Requires: %{apache}-httpd-devel
Requires: %{apache}-mod_ssl
Requires: %{apache}-mod_ldap
%endif
%if 0%{?amzn} == 2023
Requires: %{apache} >= 2.4, %{apache} < 2.5
Requires: httpd-devel
Requires: mod_ssl
Requires: mod_ldap
%endif

%description -n ondemand-apache
Meta package for pulling in SCL apache %{apache}

%prep
%setup -c -T

%install
%scl_install
# Hacks to reduce number of objects in RPM which
# should speed up non x86_64 builds running on x86_64 hardware
rm -f $RPM_BUILD_DIR/%{buildsubdir}/filelist
rm -f $RPM_BUILD_DIR/%{buildsubdir}/filesystem
rm -rf %{buildroot}%{_datadir}/man/man*/*
rm -rf %{buildroot}%{_datadir}/locale/*
# End hacks
# The %undefine macros in Amazon Linux throw errors
%if 0%{?amzn} == 2023
cat > %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-config << EOF
%%scl %scl
EOF
%endif
mkdir -p %{buildroot}/opt/rh
ln -s ../ood/ondemand %{buildroot}/opt/rh/%{scl}
mkdir -p %{buildroot}%{ondemand_apps_gem_home}
mkdir -p %{buildroot}%{ondemand_core_gem_home}
cat >> %{buildroot}%{_scl_scripts}/enable << EOF
%if 0%{?rhel} == 7
. scl_source enable %{apache} %{ruby} %{nodejs}
%endif
export PATH="%{_bindir}:%{_sbindir}\${PATH:+:\${PATH}}"
export LD_LIBRARY_PATH="%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}"
export MANPATH="%{_mandir}:\${MANPATH:-}"
export PKG_CONFIG_PATH="%{_libdir}/pkgconfig\${PKG_CONFIG_PATH:+:\${PKG_CONFIG_PATH}}"
export RUBYLIB="%{_datadir}/ruby/vendor_ruby:%{_libdir}/ruby/vendor_ruby\${RUBYLIB:+:\${RUBYLIB}}"
export GEM_HOME="%{ondemand_gem_home}"
shopt -s nullglob
for dir in %{ondemand_apps_gem_home}/* ; do
    export GEM_PATH="\${dir}:\${GEM_PATH}"
done
for dir in %{ondemand_core_gem_home}/* ; do
    export GEM_PATH="\${dir}:\${GEM_PATH}"
done
shopt -u nullglob
export GEM_PATH="\${GEM_HOME}:\${GEM_PATH}"
EOF

cat >> %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel << EOF
%%scl_%{scl_name_base} %{scl}
%%scl_prefix_%{scl_name_base} %{scl_prefix}
%%_scl_prefix_%{scl_name_base} %{_scl_prefix}
%if 0%{?rhel} == 7
%%scl_%{scl_name_base}_ruby %{ruby}
%%scl_%{scl_name_base}_prefix_ruby %{ruby}-
%%scl_%{scl_name_base}_nodejs %{nodejs}
%%scl_%{scl_name_base}_prefix_nodejs %{nodejs}-
%%scl_%{scl_name_base}_apache %{apache}
%%scl_%{scl_name_base}_prefix_apache %{apache}-
%endif
%%scl_%{scl_name_base}_gem_home %{ondemand_gem_home}
%%scl_%{scl_name_base}_core_gem_home %{ondemand_core_gem_home}
%%scl_%{scl_name_base}_apps_gem_home %{ondemand_apps_gem_home}
EOF

%files
%scl_files
/opt/rh/%{scl}

%files -n ondemand-build
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files -n ondemand-scldevel
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%files -n ondemand-ruby
%{ondemand_gem_home}
%{ondemand_apps_gem_home}
%{ondemand_core_gem_home}

%files -n ondemand-nodejs

%files -n ondemand-apache

%changelog
* Tue Jan 29 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.5-5
- Depend on apache devel and add some more marcos to aid in package development
  using ondemand (tdockendorf@osc.edu)

* Tue Jan 29 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.5-4
- Fix meta packages to actually get created Ensure SCL variables are used
  everywhere so only one place to update dependencies (tdockendorf@osc.edu)

* Tue Jan 29 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.5-3
- Add meta packages to define SCL dependencies (tdockendorf@osc.edu)

* Wed Jan 16 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.5-2
- Add symlink /opt/rh/ondemand so that httpd24 assumption of loading SCL from
  /opt/rh will work (tdockendorf@osc.edu)

* Wed Jan 16 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.5-1
- Bump ondemand-runtime to 1.5 and add RUBYLIB (tdockendorf@osc.edu)

* Wed Jan 16 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.4-4
- Disable nfsmountable for ondemand-runtime to hopefully avoid files ending up
  in /etc (tdockendorf@osc.edu)

* Tue Jan 15 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.4-3
- Add _scl_prefix_ondemand macro (tdockendorf@osc.edu)

* Tue Jan 15 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.4-2
- Add ondemand-scldevel subpackage to ondemand-runtime (tdockendorf@osc.edu)

* Tue Jan 15 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.4-1
- new package built with tito

