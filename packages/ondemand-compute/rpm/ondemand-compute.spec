%{!?package_release: %define package_release 1}

Name:       ondemand-compute
Version:    %{package_version}
Release:    %{package_release}%{?dist}
Summary:    Open OnDemand Compute meta package

Group:      Applications/System
License:    Apache 2.0
URL:        https://osc.github.io/ood-documentation/
BuildArch:  noarch

Requires:   turbovnc >= 2.2.5
Requires:   python3-websockify >= 0.10.0
Requires:   /bin/bash
Requires:   /usr/bin/shuf
Requires:   /usr/bin/pgrep
Requires:   /usr/bin/nc

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
* Sun Feb 03 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.5-1
- Bump release to 1.5 (tdockendorf@osc.edu)

* Thu Jan 03 2019 Trey Dockendorf <tdockendorf@osc.edu> 1.4-1
- Bump to 1.4 ./bump-release.py -p 1.3 -n 1.4 (tdockendorf@osc.edu)

* Tue Feb 13 2018 Trey Dockendorf <tdockendorf@osc.edu> 1.3-1
- new package built with tito


