Name:           nitrokey-app2
Version:        2.4.3
Release:        %autorelease
Summary:        Graphical application to manage Nitrokey 3 devices

License:        Apache-2.0
URL:            https://github.com/nitrokey/nitrokey-app2
Vendor:         Nitrokey

Source0:        %{URL}/archive/refs/tags/v%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  %{py3_dist nitrokey}
BuildRequires:  %{py3_dist usb-monitor}
BuildRequires:  %{py3_dist pyside6}

Requires:       atk
Requires:       binutils
Requires:       cairo-gobject
Requires:       dbus-libs
Requires:       gdk-pixbuf2
Requires:       glibc
Requires:       gtk3
Requires:       libxkbcommon
Requires:       libwayland-client
Requires:       libwayland-cursor
Requires:       libwayland-egl
Requires:       libxkbcommon-x11
Requires:       libX11-xcb
Requires:       pango
Requires:       xcb-util-wm
Requires:       xcb-util-keysyms
Requires:       xcb-util-image
Requires:       xcb-util-cursor
Requires:       xcb-util-renderutil
Requires:       zlib

%description
%{summary}.

%prep
%autosetup -n nitrokey-app2-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files nitrokeyapp
mv %{buildroot}%{_bindir}/nitrokeyapp %{buildroot}%{_bindir}/%{name}
mkdir -p %{buildroot}%{_datadir}/icons/hicolor
cp -r ci-scripts/linux/rpm/icons/hicolor/* %{buildroot}%{_datadir}/icons/hicolor
mkdir -p %{buildroot}%{_datadir}/applications
cp ci-scripts/linux/rpm/nitrokey-app2.desktop %{buildroot}%{_datadir}/applications

%check

%files -f %{pyproject_files}
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_datadir}/icons/hicolor/scalable/apps/%{name}.svg
%{_datadir}/applications/%{name}.desktop

%changelog
* Mon Nov 04 2024 Markus Merklinger <markus@nitrokey.com> - 2.3.2-1
- Changed the build process and dependencies.

* Wed Jan 10 2024 Markus Merklinger <markus@nitrokey.com> - 2.1.5-1
- First release of package
