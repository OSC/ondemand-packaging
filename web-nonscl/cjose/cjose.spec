Name:		cjose
Version:	0.5.1
Release:	1%{?dist}
Summary:	JOSE implementation for C

Group:		Networking/Daemons/HTTP
License:	Apache License Version 2.0
URL:		https://github.com/cisco/cjose
Source0:	https://github.com/cisco/cjose/archive/%{version}.tar.gz

BuildRequires:  check-devel
BuildRequires:	jansson-devel >= 2.9
BuildRequires:  openssl-devel
Requires:	    jansson >= 2.9
Requires:       openssl

%description
JOSE implementation for C

%package devel
Summary:  Development libraries for cjose
Group:		Networking/Daemons/HTTP
Requires: %{name} = %{version}-%{release}

%description devel
Development libraries for cjose

%prep
%setup -q


%build
%configure --disable-static
make %{?_smp_mflags}

%check
make test

%install
make install DESTDIR=${RPM_BUILD_ROOT}
rm -f ${RPM_BUILD_ROOT}%{_libdir}/lib%{name}.la


%files
%doc
%{_libdir}/lib%{name}.so*

%files devel
%{_includedir}/%{name}
%{_libdir}/pkgconfig/%{name}.pc


%changelog
* Wed Oct 11 2017 Trey Dockendorf <tdockendorf@osc.edu> 0.5.1-1
- new package built with tito

* Fri Jan 27 2017 Trey Dockendorf <tdockendorf@osc.edu> - 0.4.1-1
- Initial build of cjose-0.4.1
