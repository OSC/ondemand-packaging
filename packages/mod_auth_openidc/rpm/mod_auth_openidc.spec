%{?scl:%scl_package mod_auth_openidc}
%{!?scl:%global pkg_name %{name}}
%{!?package_release: %define package_release 1}

%{!?_httpd_mmn: %{expand: %%global _httpd_mmn %%(cat %{_includedir}/httpd/.mmn || echo 0-0)}}
%{!?_httpd_moddir: %{expand: %%global _httpd_moddir %%{_libdir}/httpd/modules}}
%{!?_httpd_confdir: %{expand: %%global _httpd_confdir %{_sysconfdir}/httpd/conf.d}}

# Optionally build with hiredis if --with hiredis is passed
%{!?_with_hiredis: %{!?_without_hiredis: %global _without_hiredis --without-hiredis}}
# It is an error if both or neither required options exist.
%{?_with_hiredis: %{?_without_hiredis: %{error: both _with_hiredis and _without_hiredis}}}
%{!?_with_hiredis: %{!?_without_hiredis: %{error: neither _with_hiredis nor _without_hiredis}}}

# /etc/httpd/conf.d with httpd < 2.4 and defined as /etc/httpd/conf.modules.d with httpd >= 2.4
%{!?_httpd_modconfdir: %{expand: %%global _httpd_modconfdir %%{_sysconfdir}/httpd/conf.d}}

%global httpd_pkg_cache_dir %{?scl:%{_scl_root}}/var/cache/httpd/mod_auth_openidc

Name:     %{?scl_prefix}mod_auth_openidc
Version:  %{package_version}
Release:  %{package_release}%{?dist}
Summary:  OpenID Connect auth module for Apache HTTP Server

Group:    System Environment/Daemons
License:  ASL 2.0
URL:      https://github.com/OpenIDC/mod_auth_openidc
Source0:  https://github.com/OpenIDC/mod_auth_openidc/releases/download/v%{version}/mod_auth_openidc-%{version}.tar.gz

BuildRequires:	%{?scl_prefix}httpd-devel
BuildRequires:	openssl-devel
BuildRequires:	curl-devel
BuildRequires:	jansson-devel
BuildRequires:  cjose-devel
BuildRequires:	pcre-devel
BuildRequires:	autoconf
BuildRequires:	automake
%{?_with_hiresdis:%{?scl_prefix}BuildRequires: %{?scl_prefix}hiresdis-devel}
Requires:	%{?scl_prefix}httpd-mmn = %{_httpd_mmn}

%description
This module enables an Apache 2.x web server to operate as
an OpenID Connect Relying Party and/or OAuth 2.0 Resource Server.

%prep
%setup -n %{pkg_name}-%{version} -q

%build
%{?scl:%define with_apxs "--with-apxs=%{_scl_root}%{_root_bindir}/apxs"}
autoreconf
%configure \
  %{?_with_hiredis} \
  %{?_without_hiredis} \
  %{?with_apxs}

make %{?_smp_mflags}

%check
make test

%install
mkdir -p $RPM_BUILD_ROOT%{_httpd_moddir}
make install DESTDIR=$RPM_BUILD_ROOT

install -m 755 -d $RPM_BUILD_ROOT%{_httpd_modconfdir}
echo 'LoadModule auth_openidc_module modules/mod_auth_openidc.so' > \
	$RPM_BUILD_ROOT%{_httpd_modconfdir}/10-auth_openidc.conf

install -m 755 -d $RPM_BUILD_ROOT%{_httpd_confdir}
install -m 644 auth_openidc.conf $RPM_BUILD_ROOT%{_httpd_confdir}
# Adjust httpd cache location in install config file
sed -i 's!/var/cache/apache2/!/var/cache/httpd/!' $RPM_BUILD_ROOT%{_httpd_confdir}/auth_openidc.conf
install -m 700 -d $RPM_BUILD_ROOT%{httpd_pkg_cache_dir}
install -m 700 -d $RPM_BUILD_ROOT%{httpd_pkg_cache_dir}/metadata
install -m 700 -d $RPM_BUILD_ROOT%{httpd_pkg_cache_dir}/cache


%files
%license LICENSE.txt
%doc ChangeLog
%doc AUTHORS
%doc README.md
%{_httpd_moddir}/mod_auth_openidc.so
%config(noreplace) %{_httpd_modconfdir}/10-auth_openidc.conf
%config(noreplace) %{_httpd_confdir}/auth_openidc.conf
%dir %attr(0700, apache, apache) %{httpd_pkg_cache_dir}
%dir %attr(0700, apache, apache) %{httpd_pkg_cache_dir}/metadata
%dir %attr(0700, apache, apache) %{httpd_pkg_cache_dir}/cache

%changelog
* Thu Jan 03 2019 Trey Dockendorf <tdockendorf@osc.edu> 2.3.10-1
- Upgrade mod_auth_openidc to 2.3.10 (tdockendorf@osc.edu)

* Thu Oct 12 2017 Trey Dockendorf <tdockendorf@osc.edu> 2.3.2-1
- new package built with tito

* Tue Jul 12 2016 John Dennis <jdennis@redhat.com> - 1.8.10.1-1
- Upgrade to new upstream
  See /usr/share/doc/mod_auth_openidc/ChangeLog for details

* Tue Mar 29 2016 John Dennis <jdennis@redhat.com> - 1.8.8-3
- Add %check to run test

* Wed Mar 23 2016 John Dennis <jdennis@redhat.com> - 1.8.8-2
- Make building with redis support optional (defaults to without)

* Mon Mar 21 2016 John Dennis <jdennis@redhat.com> - 1.8.8-1
- Update to 1.8.8 (#1316528)
- Add missing unpackaged files/directories

  Add to doc: README.md, DISCLAIMER, AUTHORS
  Add to httpd/conf.d: auth_openidc.conf
  Add to /var/cache: /var/cache/httpd/mod_auth_openidc/cache
                     /var/cache/httpd/mod_auth_openidc/metadata

* Sat Nov 07 2015 Jan Pazdziora <jpazdziora@redhat.com> 1.8.6-1
- Initial packaging for Fedora 23.
