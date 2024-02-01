%define unmangled_name proton-vpn-killswitch
%define version 0.3.0
%define release 1

Prefix: %{_prefix}

Name: python3-%{unmangled_name}
Version: %{version}
Release: %{release}%{?dist}
Summary: %{unmangled_name} library

Group: ProtonVPN
License: GPLv3
Vendor: Proton Technologies AG <opensource@proton.me>
URL: https://github.com/ProtonVPN/%{unmangled_name}
Source0: %{unmangled_name}-%{version}.tar.gz
BuildArch: noarch
BuildRoot: %{_tmppath}/%{unmangled_name}-%{version}-%{release}-buildroot

BuildRequires: python3-proton-core
BuildRequires: python3-setuptools
Requires: python3-proton-core

Conflicts: python3-proton-vpn-connection < 0.12.0
Conflicts: python3-proton-vpn-killswitch-network-manager < 0.3.0
Conflicts: python3-proton-vpn-api-core < 0.19.0

%{?python_disable_dependency_generator}

%description
Package %{unmangled_name} library.


%prep
%setup -n %{unmangled_name}-%{version} -n %{unmangled_name}-%{version}

%build
python3 setup.py build

%install
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES


%files -f INSTALLED_FILES
%{python3_sitelib}/proton/
%{python3_sitelib}/proton_vpn_killswitch-%{version}*.egg-info/
%defattr(-,root,root)

%changelog
* Thu Feb 01 2024 Josep Llaneras <josep.llaneras@proton.ch> 0.3.0
- Make kill switch interface async

* Mon Sep 04 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.2.0
- Add kill switch states

* Tue Apr 04 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.1.1
- Update interface

* Thu Mar 23 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.1.0
- Refactor class

* Wed Jun 1 2022 Proton Technologies AG <opensource@proton.me> 0.0.1
- First RPM release
