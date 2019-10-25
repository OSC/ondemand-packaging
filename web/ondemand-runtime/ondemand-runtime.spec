%global scl ondemand
%global scl_name_base %scl
%global _scl_prefix /opt/ood
%scl_package %scl

%if 0%{?rhel} >= 8
%global ruby ruby
%global python python2
%global nodejs nodejs
%global apache httpd
%else
%global ruby rh-ruby25
%global python python
%global nodejs rh-nodejs10
%global apache httpd24
%endif
%global ruby_version 2.5

Name:      ondemand-runtime
Version:   1.7
Release:   3%{?dist}
Summary:   Package that handles %{scl} Software Collection.
License:   MIT

BuildRequires:  scl-utils-build
Requires:       scl-utils
%if 0%{?rhel} <= 7
Requires:       %{ruby}-runtime
Requires:       %{nodejs}-runtime
Requires:       %{apache}-runtime
%endif

%description
Package shipping essential scripts to work with %{scl} Software Collection.

%package -n ondemand-build
Summary: Package shipping basic build configuration
Requires: scl-utils-build

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
Requires: %{ruby} >= 2.5, %{ruby} < 2.6
Requires: rubygem-rake
Requires: rubygem-bundler
Requires: ruby-devel
Requires: rubygems
Requires: rubygems-devel
%else
Requires: %{ruby}
Requires: %{ruby}-rubygem-rake
Requires: %{ruby}-rubygem-bundler
Requires: %{ruby}-ruby-devel
Requires: %{ruby}-rubygems
Requires: %{ruby}-rubygems-devel
%endif

%description -n ondemand-ruby
Meta package for pulling in SCL Ruby %{ruby}

%package -n ondemand-python
Summary: Meta package for pulling in Python needed by OnDemand
Requires: %{python}

%description -n ondemand-python
Meta package for pulling in Python needed by OnDemand

%package -n ondemand-nodejs
Summary: Meta package for pulling in SCL nodejs %{nodejs}
%if 0%{?rhel} >= 8
Requires: %{nodejs}
Requires: npm
%else
Requires: %{nodejs}
Requires: %{nodejs}-npm
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
%else
Requires: %{apache}
Requires: %{apache}-httpd-devel
Requires: %{apache}-mod_ssl
Requires: %{apache}-mod_ldap
%endif

%description -n ondemand-apache
Meta package for pulling in SCL apache %{apache}

%prep
%setup -c -T

%install
%scl_install
mkdir -p %{buildroot}/opt/rh
ln -s ../ood/ondemand %{buildroot}/opt/rh/%{scl}
cat >> %{buildroot}%{_scl_scripts}/enable << EOF
%if 0%{?rhel} <= 7
. scl_source enable %{apache} %{ruby} %{nodejs}
%endif
export PYTHON=%{python}
export PATH="%{_bindir}:%{_sbindir}\${PATH:+:\${PATH}}"
export LD_LIBRARY_PATH="%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}"
export MANPATH="%{_mandir}:\${MANPATH:-}"
export PKG_CONFIG_PATH="%{_libdir}/pkgconfig\${PKG_CONFIG_PATH:+:\${PKG_CONFIG_PATH}}"
export RUBYLIB="%{_datadir}/ruby/vendor_ruby:%{_libdir}/ruby/vendor_ruby\${RUBYLIB:+:\${RUBYLIB}}"
export GEM_HOME="%{_datadir}/gems/%{ruby_version}"
export GEM_PATH="\${GEM_HOME}:\${GEM_PATH}"
EOF

cat >> %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel << EOF
%%scl_%{scl_name_base} %{scl}
%%scl_prefix_%{scl_name_base} %{scl_prefix}
%%_scl_prefix_%{scl_name_base} %{_scl_prefix}
%if 0%{?rhel} <= 7
%%scl_%{scl_name_base}_ruby %{ruby}
%%scl_%{scl_name_base}_prefix_ruby %{ruby}-
%%scl_%{scl_name_base}_nodejs %{nodejs}
%%scl_%{scl_name_base}_prefix_nodejs %{nodejs}-
%%scl_%{scl_name_base}_apache %{apache}
%%scl_%{scl_name_base}_prefix_apache %{apache}-
%endif
%%scl_%{scl_name_base}_gem_home %{_datadir}/gems/%{ruby_version}
EOF

%files -f filelist
%scl_files
/opt/rh/%{scl}

%files -n ondemand-build
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files -n ondemand-scldevel
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%files -n ondemand-ruby

%files -n ondemand-python

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

