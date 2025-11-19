%define scl ondemand
%define pkg_name passenger
%scl_package passenger
%define passenger_version %{package_version}
%define nginx_version 1.26.3
%define release_version %{package_release}
%define ngix_release_version 2

%define runtime_version 4.1.0

%global  nginx_user          %{?scl_prefix}nginx
%global  nginx_group         %{nginx_user}
%global  nginx_home          %{_root_localstatedir}/lib/%{?scl_prefix}nginx
%global  nginx_home_tmp      %{nginx_home}/tmp
%global  nginx_confdir       %{_sysconfdir}/nginx
%global  nginx_datadir       %{_datadir}/nginx
%global  nginx_logdir        %{_root_localstatedir}/log/%{?scl_prefix}nginx
%global  nginx_webroot       %{nginx_datadir}/html

%global bundled_boost_version 1.87.0
%global apache_module_package_name mod_passenger
%global ruby_vendorlibdir %{_datadir}/ruby/vendor_ruby
%global ruby_vendorarchdir %{_libdir}/ruby/vendor_ruby
%global passenger_ruby_libdir %{ruby_vendorlibdir}
%{!?_httpd_mmn: %{expand: %%global _httpd_mmn %%(cat %{_includedir}/httpd/.mmn 2>/dev/null || echo 0-0)}}
%{!?_httpd_moddir: %{expand: %%global _httpd_moddir      %%{_libdir}/httpd/modules}}

%ifarch aarch64
%define mflag "-march=armv8-a"
%else
%define mflag "-m64"
%endif
%ifarch ppc64le
%define mtune "-mcpu=powerpc64le"
%else
%define mtune "-mtune=generic"
%endif

Name:       %{?scl_prefix}passenger
Version:    %{passenger_version}
Release:    %{release_version}.ood%{runtime_version}%{?dist}
Summary:    Phusion Passenger application server
URL:        https://www.phusionpassenger.com
Group:      System Environment/Daemons
License:    Boost and BSD and BSD with advertising and MIT and zlib
Source0:    https://github.com/phusion/passenger/releases/download/release-%{passenger_version}/passenger-%{passenger_version}.tar.gz
Source1:    http://nginx.org/download/nginx-%{nginx_version}.tar.gz

Patch0:     passenger-analytics-collection-static-sleep.patch

%{?scl:Requires:%scl_runtime}
%{?scl:BuildRequires:%scl_runtime}
BuildRequires:  ondemand-scldevel = %{runtime_version}
BuildRequires:  ondemand-build = %{runtime_version}
BuildRequires:  ondemand-ruby = %{runtime_version}
BuildRequires:  ondemand-apache = %{runtime_version}
BuildRequires:  libcurl-devel
BuildRequires:  zlib-devel
BuildRequires:  openssl-devel
BuildRequires:  pcre2-devel
BuildRequires:  patch
Requires: ondemand-runtime = %{runtime_version}
Requires: ondemand-ruby = %{runtime_version}
Requires: procps-ng
Provides: %{name} = %{version}-%{release}
Provides: bundled(boost)  = %{bundled_boost_version}

%description
Phusion Passenger® is a web server and application server, designed to be fast,
robust and lightweight. It takes a lot of complexity out of deploying web apps,
adds powerful enterprise-grade features that are useful in production,
and makes administration much easier and less complex. It supports Ruby,
Python, Node.js and Meteor.

%package devel
Summary: Phusion Passenger development files
Requires: %{name} = %{version}-%{release}
Provides: bundled(boost-devel) = %{bundled_boost_version}
License: Boost and BSD and BSD with advertising and GPL+ and MIT and zlib

%description devel
This package contains development files for Phusion Passenger®. Installing this
package allows it to compile native extensions for non-standard Ruby interpreters,
and allows Passenger Standalone to use a different Nginx core version.

%package doc
Summary: Phusion Passenger documentation
Requires: %{name} = %{version}-%{release}
Provides:  %{?scl_prefix}rubygem-passenger-doc = %{version}-%{release}
BuildArch: noarch
License: CC-BY-SA and MIT and (MIT or GPL+)

%description doc
This package contains documentation files for Phusion Passenger®.

%package -n %{?scl_prefix}nginx
Summary: A high performance web server and reverse proxy server
URL:        http://nginx.org/
Version: %{nginx_version}
Release: %{ngix_release_version}.p%{passenger_version}.ood%{runtime_version}%{?dist}
Obsoletes: %{?scl_prefix}nginx-filesystem
BuildRequires: libxslt-devel
BuildRequires: gd-devel
BuildRequires: libev-devel >= 4.0.0
Requires: gd
Requires: openssl
Requires: pcre2

%description -n %{?scl_prefix}nginx
Nginx is a web server and a reverse proxy server for HTTP, SMTP, POP3 and
IMAP protocols, with a strong focus on high concurrency, performance and low
memory usage. Includes Phusion Passenger support.

%prep
%setup -q -n %{pkg_name}-%{passenger_version}
%setup -q -T -D -a 1 -n %{pkg_name}-%{passenger_version}

# Apply patches
%patch -P0 -p1 -F1

%build
scl enable ondemand - << \EOF
set -x
set -e

export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# nginx
# TODO %optflags on EL8 caused some very odd problems so only pull in what's absolutely necessary
%if 0%{?rhel} >= 8
export EXTRA_CFLAGS="${CFLAGS} %{mflag} %{mtune} -fPIC"
export EXTRA_CXXFLAGS="${CXXFLAGS} %{mflag} %{mtune} -fPIC"
%else
export EXTRA_CFLAGS="${CFLAGS:-%optflags} -Wno-deprecated"
export EXTRA_CXXFLAGS="${CXXFLAGS:-%optflags} -Wno-deprecated"
# Remove default optimization flags and use Phusion Passenger's recommended optimization flags.
export EXTRA_CFLAGS=`echo "$EXTRA_CFLAGS" | sed 's|-O2||g'`
export EXTRA_CXXFLAGS=`echo "$EXTRA_CXXFLAGS" | sed 's|-O2||g'`
%endif
export OPTIMIZE=yes
export CACHING=false

rake nginx

unset EXTRA_CFLAGS
unset EXTRA_CXXFLAGS
unset OPTIMIZE
unset CACHING

export DESTDIR=%{buildroot}
pushd nginx-%{nginx_version}
./configure \
    --prefix=%{nginx_datadir} \
    --sbin-path=%{_sbindir}/nginx \
    --conf-path=%{nginx_confdir}/nginx.conf \
    --error-log-path=%{nginx_logdir}/error.log \
    --http-log-path=%{nginx_logdir}/access.log \
    --http-client-body-temp-path=%{nginx_home_tmp}/client_body \
    --http-proxy-temp-path=%{nginx_home_tmp}/proxy \
    --http-fastcgi-temp-path=%{nginx_home_tmp}/fastcgi \
    --http-uwsgi-temp-path=%{nginx_home_tmp}/uwsgi \
    --http-scgi-temp-path=%{nginx_home_tmp}/scgi \
%if 0%{?rhel} >= 7 || 0%{?fedora} >= 16
    --pid-path=/run/%{?scl_prefix}nginx.pid \
    --lock-path=/run/lock/subsys/%{?scl_prefix}nginx \
%else
    --pid-path=%{_root_localstatedir}/run/%{?scl_prefix}nginx.pid \
    --lock-path=%{_root_localstatedir}/lock/subsys/%{?scl_prefix}nginx \
%endif
    --user=%{nginx_user} \
    --group=%{nginx_group} \
    --with-file-aio \
    --with-http_ssl_module \
    --with-http_v2_module \
    --with-http_realip_module \
    --with-http_addition_module \
    --with-http_xslt_module \
    --with-http_image_filter_module \
    --with-http_sub_module \
    --with-http_dav_module \
    --with-http_flv_module \
    --with-http_mp4_module \
    --with-http_gunzip_module \
    --with-http_gzip_static_module \
    --with-http_random_index_module \
    --with-http_secure_link_module \
    --with-http_degradation_module \
    --with-http_stub_status_module \
    --with-mail \
    --with-mail_ssl_module \
    --with-pcre \
    --with-pcre-jit \
    --add-module=../src/nginx_module \
    --with-debug \
    --with-cc-opt="%{optflags} $(pcre2-config --cflags)" \
    --with-ld-opt="$RPM_LD_FLAGS -Wl,-E" # so the perl module finds its symbols

make %{?_smp_mflags}
popd
# end nginx

export EXTRA_CFLAGS="${CFLAGS:-%optflags} -Wno-deprecated"
export EXTRA_CXXFLAGS="${CXXFLAGS:-%optflags} -Wno-deprecated"
# Remove default optimization flags and use Phusion Passenger's recommended optimization flags.
export EXTRA_CFLAGS=`echo "$EXTRA_CFLAGS" | sed 's|-O2||g'`
export EXTRA_CXXFLAGS=`echo "$EXTRA_CXXFLAGS" | sed 's|-O2||g'`
export OPTIMIZE=yes
export CACHING=false

rake fakeroot \
    NATIVE_PACKAGING_METHOD=rpm \
    FS_PREFIX=%{_prefix} \
    FS_BINDIR=%{_bindir} \
    FS_SBINDIR=%{_sbindir} \
    FS_DATADIR=%{_datadir} \
    FS_LIBDIR=%{_libdir} \
    FS_DOCDIR=%{_docdir} \
    RUBY=$(which ruby) \
    RUBYLIBDIR=%{ruby_vendorlibdir} \
    RUBYARCHDIR=%{ruby_vendorarchdir} \
    APACHE2_MODULE_PATH=%{_httpd_moddir}/mod_passenger.so

EOF

%install
scl enable ondemand - << \EOF
set -x
set -e

export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8

%{__rm} -rf %{buildroot}
%{__mkdir} %{buildroot}

# nginx
pushd nginx-%{nginx_version}
make install DESTDIR=%{buildroot} INSTALLDIRS=vendor

find %{buildroot} -type f -name .packlist -exec rm -f '{}' \;
find %{buildroot} -type f -name perllocal.pod -exec rm -f '{}' \;
find %{buildroot} -type f -empty -exec rm -f '{}' \;
find %{buildroot} -type f -iname '*.so' -exec chmod 0755 '{}' \;

%{__mkdir_p} %{buildroot}%{_root_sysconfdir}/logrotate.d
cat > %{buildroot}%{_root_sysconfdir}/logrotate.d/%{?scl_prefix}nginx <<'EOS'
%{nginx_logdir}/*log {
    create 0644 %{nginx_user} %{nginx_group}
    daily
    rotate 10
    missingok
    notifempty
    compress
    sharedscripts
    postrotate
        /bin/kill -USR1 `cat %{_root_localstatedir}/run/%{?scl_prefix}nginx.pid 2>/dev/null` 2>/dev/null || true
    endscript
}
EOS


install -p -d -m 0755 %{buildroot}%{nginx_confdir}/conf.d
install -p -d -m 0755 %{buildroot}%{nginx_confdir}/default.d
install -p -d -m 0700 %{buildroot}%{nginx_home}
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}
install -p -d -m 0700 %{buildroot}%{nginx_logdir}
install -p -d -m 0755 %{buildroot}%{nginx_webroot}
popd
# end nginx

%{__cp} -a pkg/fakeroot/* %{buildroot}/

# Install bootstrapping code into the executables and the Nginx config script.
./dev/install_scripts_bootstrap_code.rb --ruby %{passenger_ruby_libdir} \
    %{buildroot}%{_bindir}/passenger* \
    %{buildroot}%{_sbindir}/passenger* \
    `find %{buildroot} -name rack_handler.rb`
./dev/install_scripts_bootstrap_code.rb --nginx-module-config %{_bindir} %{buildroot}%{_datadir}/passenger/ngx_http_passenger_module/config

# Fix Python scripts with shebang which are not executable
%{__chmod} +x %{buildroot}%{_datadir}/passenger/helper-scripts/wsgi-loader.py

# Don't need Apache module
%{__rm} -f %{buildroot}%{_httpd_moddir}/mod_passenger.so

# Add passenger-status wrapper
%{__mkdir_p} %{buildroot}%{_root_sbindir}
%{__cat} > %{buildroot}%{_root_sbindir}/ondemand-passenger-status <<'EOS'
#!/bin/bash

. scl_source enable ondemand

%{_sbindir}/passenger-status "$@"
EOS
EOF
%{__chmod} 0755 %{buildroot}%{_root_sbindir}/ondemand-passenger-status

%pre -n %{?scl_prefix}nginx

getent group %{nginx_group} > /dev/null || groupadd -r %{nginx_group}
getent passwd %{nginx_user} > /dev/null || \
    useradd -r -d %{nginx_home} -g %{nginx_group} \
    -s /sbin/nologin -c "Nginx web server" %{nginx_user}
exit 0

%post -n %{?scl_prefix}nginx
if [ $1 -eq 2 ]; then
    # Make sure these directories are not world readable.
    chmod o-rwx %{nginx_home}
    chmod o-rwx %{nginx_home_tmp}
    chmod o-rwx %{nginx_logdir}
fi

%files
%{_bindir}/passenger*
%{_sbindir}/passenger*
%{_libdir}/passenger/support-binaries
%{_datadir}/passenger/helper-scripts
%{_datadir}/passenger/templates
%{_datadir}/passenger/standalone_default_root
%{_datadir}/passenger/node
%{_datadir}/passenger/*.types
%{_datadir}/passenger/*.crt
%{_datadir}/passenger/*.txt
%{_datadir}/passenger/*.pem
%{_datadir}/passenger/*.p12
%{passenger_ruby_libdir}/*
%{ruby_vendorarchdir}/passenger_native_support.so
%{_root_sbindir}/ondemand-passenger-status

%files doc
%{_docdir}/passenger/*

%files devel
%{_datadir}/passenger/ngx_http_passenger_module
%{_datadir}/passenger/ruby_extension_source
%{_datadir}/passenger/include
%{_libdir}/passenger/common
%{_libdir}/passenger/nginx_dynamic

%files -n %{?scl_prefix}nginx
%{nginx_datadir}
%dir %{nginx_confdir}
%dir %{nginx_confdir}/conf.d
%dir %{nginx_confdir}/default.d
%{_sbindir}/nginx
%config(noreplace) %{_root_sysconfdir}/logrotate.d/%{?scl_prefix}nginx
%attr(700,%{nginx_user},%{nginx_group}) %dir %{nginx_home}
%attr(700,%{nginx_user},%{nginx_group}) %dir %{nginx_home_tmp}
%attr(700,%{nginx_user},%{nginx_group}) %dir %{nginx_logdir}
%config(noreplace) %{nginx_confdir}/fastcgi.conf
%config(noreplace) %{nginx_confdir}/fastcgi.conf.default
%config(noreplace) %{nginx_confdir}/fastcgi_params
%config(noreplace) %{nginx_confdir}/fastcgi_params.default
%config(noreplace) %{nginx_confdir}/koi-utf
%config(noreplace) %{nginx_confdir}/koi-win
%config(noreplace) %{nginx_confdir}/mime.types
%config(noreplace) %{nginx_confdir}/mime.types.default
%config(noreplace) %{nginx_confdir}/nginx.conf
%config(noreplace) %{nginx_confdir}/nginx.conf.default
%config(noreplace) %{nginx_confdir}/scgi_params
%config(noreplace) %{nginx_confdir}/scgi_params.default
%config(noreplace) %{nginx_confdir}/uwsgi_params
%config(noreplace) %{nginx_confdir}/uwsgi_params.default
%config(noreplace) %{nginx_confdir}/win-utf

%changelog

* Tue Apr 29 2025 Simon Westersund <swesters@csc.fi> [6.0.23-3]
- Patch Passenger analytics collection to sleep for 30 seconds by default,
  to avoid simultaneous wake-ups by all agents. This behavior can be
  restored to upstream defaults by defining the
  OOD_OVERRIDE_PASSENGER_ANALYTICS_COLLECTION_RESTORE_UPSTREAM_BEHAVIOR
  environment variable (any value works).
- Allow overriding the 30 second sleep time with
  OOD_OVERRIDE_PASSENGER_ANALYTICS_COLLECTION_SLEEP_TIME_SECONDS. This
  must be a value that fits into a positive signed int. Fractional
  seconds are not supported.

