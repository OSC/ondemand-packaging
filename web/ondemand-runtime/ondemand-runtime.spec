%global scl ondemand
%global scl_name_base %scl
%global _scl_prefix /opt/ood
%scl_package %scl

%global ruby rh-ruby24
%global nodejs rh-nodejs6
%global git rh-git29
%global apache httpd24

Name:      ondemand-runtime
Version:   1.5
Release:   3%{?dist}
Summary:   Package that handles %{scl} Software Collection.
License:   MIT

BuildRequires:  scl-utils-build
Requires:       scl-utils
Requires:       rh-ruby24-runtime
Requires:       rh-nodejs6-runtime
Requires:       rh-git29-runtime
Requires:       httpd24-runtime

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
Requires: %{ruby}
Requires: %{ruby}-rubygem-rake
Requires: %{ruby}-rubygem-bundler
Requires: %{ruby}-ruby-devel
Requires: %{ruby}-rubygems
Requires: %{ruby}-rubygems-devel

%description -n ondemand-ruby
Meta package for pulling in SCL Ruby %{ruby}

%package -n ondemand-nodejs
Summary: Meta package for pulling in SCL nodejs %{nodejs}
Requires: %{nodejs}

%description -n ondemand-nodejs
Meta package for pulling in SCL nodejs %{nodejs}

%package -n ondemand-git
Summary: Meta package for pulling in SCL git %{git}
Requires: %{git}

%description -n ondemand-git
Meta package for pulling in SCL git %{git}

%package -n ondemand-apache
Summary: Meta package for pulling in SCL apache %{apache}
Requires: %{apache}
Requires: %{apache}-mod_ssl
Requires: %{apache}-mod_ldap

%description -n ondemand-apache
Meta package for pulling in SCL apache %{apache}

%prep
%setup -c -T

%install
%scl_install
mkdir -p %{buildroot}/opt/rh
ln -s ../ood/ondemand %{buildroot}/opt/rh/%{scl}
cat >> %{buildroot}%{_scl_scripts}/enable << EOF
. scl_source enable httpd24 rh-ruby24 rh-nodejs6 rh-git29
export PATH="%{_bindir}:%{_sbindir}\${PATH:+:\${PATH}}"
export LD_LIBRARY_PATH="%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}"
export MANPATH="%{_mandir}:\${MANPATH:-}"
export PKG_CONFIG_PATH="%{_libdir}/pkgconfig\${PKG_CONFIG_PATH:+:\${PKG_CONFIG_PATH}}"
export RUBYLIB="%{_datadir}/ruby/vendor_ruby:%{_libdir}/ruby/vendor_ruby\${RUBYLIB:+:\${RUBYLIB}}"
EOF

cat >> %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel << EOF
%%scl_%{scl_name_base} %{scl}
%%scl_prefix_%{scl_name_base} %{scl_prefix}
%%_scl_prefix_%{scl_name_base} %{_scl_prefix}
EOF

%files -f filelist
%scl_files
/opt/rh/%{scl}

%files -n ondemand-build
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files -n ondemand-scldevel
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%changelog
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

