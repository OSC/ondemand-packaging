Name:       ondemand-compute
Version:    1.5
Release:    1%{?dist}
Summary:    Open OnDemand Compute meta package

Group:      Applications/System
License:    Apache 2.0
URL:        https://osc.github.io/ood-documentation/
BuildArch:  noarch

Requires:   turbovnc >= 2.1.1
Requires:   python-websockify >= 0.8.0

%description
Open OnDemand Compute meta package

%prep
exit 0

%build
exit 0

%install
exit 0

%clean
exit 0

%files

%changelog
* Thu Jan 03 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.4-1
- Bump to 1.4 ./bump-release.py -p 1.3 -n 1.4 (tdockendorf@osc.edu)

* Tue Feb 13 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3-1
- new package built with tito


