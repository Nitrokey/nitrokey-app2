Name:           nitrokey-app2
Version:        2.3.1
Release:        1%{?dist}
Summary:        Graphical application to manage Nitrokey 3 devices

License:		Apache-2.0
URL:			https://github.com/nitrokey/%{name}
Vendor:			Nitrokey

Source0:		%{URL}/archive/refs/tags/v%{version}.tar.gz

BuildRequires: atk
BuildRequires: binutils
BuildRequires: cairo-gobject
BuildRequires: dbus-libs
BuildRequires: gdk-pixbuf2
BuildRequires: gtk3
BuildRequires: libxkbcommon
BuildRequires: libwayland-client
BuildRequires: libwayland-cursor
BuildRequires: libwayland-egl
BuildRequires: libxkbcommon-x11
BuildRequires: libX11-xcb
BuildRequires: make
BuildRequires: pango
BuildRequires: poetry
BuildRequires: python3.9
BuildRequires: python3-devel
BuildRequires: which
BuildRequires: xcb-util-wm
BuildRequires: xcb-util-keysyms
BuildRequires: xcb-util-image
BuildRequires: xcb-util-cursor
BuildRequires: xcb-util-renderutil

Requires: glibc
Requires: zlib

%global debug_package %{nil}

%description
%{summary}.

%prep
%autosetup -v

%build
poetry env use python3.9
poetry install
make build-pyinstaller-onedir

%install
%define _build_id_links none
mkdir -p %{buildroot}%{_libdir}/%{name}
cp -r dist/nitrokey-app/* %{buildroot}%{_libdir}/%{name}
mkdir -p %{buildroot}%{_bindir}
ln -s %{_libdir}/%{name}/nitrokey-app %{buildroot}%{_bindir}/%{name}
mkdir -p %{buildroot}%{_datadir}/icons/hicolor
cp -r ci-scripts/linux/rpm/icons/hicolor/* %{buildroot}%{_datadir}/icons/hicolor
mkdir -p %{buildroot}%{_datadir}/applications
cp ci-scripts/linux/rpm/nitrokey-app2.desktop %{buildroot}%{_datadir}/applications

%files
%{_bindir}/%{name}
%{_libdir}/%{name}
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_datadir}/icons/hicolor/scalable/apps/%{name}.svg
%{_datadir}/applications/%{name}.desktop

%changelog
* Wed Jan 10 2024 Markus Merklinger <markus@nitrokey.com> - 2.1.5-1
- First release of package
