#!/bin/bash

set -euxo pipefail

pwd=$(pwd)

#export WINEPREFIX=${pwd}/wine_base
#export WINEARCH=win32

. /opt/mkuserwineprefix

PY_WIN_VERSION_SUFFIX=39
PY_VERSION=3.9.11

#PY_BASE_URL=https://www.python.org/ftp/python/${PY_VERSION}/win32
PY_DIR=Python${PY_WIN_VERSION_SUFFIX}
PY_WINE_HOME=c:/${PY_DIR}
PY_HOME=${WINEPREFIX}/drive_c/${PY_DIR}

WINE_BUILD_DIR=${WINEPREFIX}/drive_c/build
CACHE_DIR=${WINE_BUILD_DIR}/cache

NITROKEY_APP2_DIR=${WINE_BUILD_DIR}/nitrokey-app2

NITROKEY_APP2_VERSION=0.0.1


BIN_LIBUSB=${CACHE_DIR}/libusb/libusb.git/libusb/.libs/libusb-1.0.dll
LIBUSB=${WINE_BUILD_DIR}/libusb-1.0.dll

#BIN_PYBOOTLOADER=${CACHE_DIR}/SomberNight/pyinstaller.git/PyInstaller/bootloader/Windows-64bit/run.exe
#PYBOOTLOADER=${WINE_BUILD_DIR}/run.exe


cat ${NITROKEY_APP2_DIR}/wine-build/nitropy.spec.tmpl | \
	sed -e "s/%%PYTHON_VERSION%%/${PY_WIN_VERSION_SUFFIX}/g" | \
	sed -e "s/%%NITROKEY_APP2_VERSION%%/${NITROKEY_APP2_VERSION}/g" > ${NITROKEY_APP2_DIR}/wine-build/nitropy.spec


export WINEPREFIX

function py
{
	#WINEDEBUG=+all wine ${PY_WINE_HOME}/python.exe -O -B "$@"
	wine ${PY_WINE_HOME}/python.exe -O -B "$@"
}


# boot wineprefix
mkdir -p ${CACHE_DIR} ${WINE_BUILD_DIR} ${WINEPREFIX}

#WINEDEBUG=+all wineboot
wineboot

# install usb stuff for win32
py -m pip install pyusb libusb

# ok let's hack the right libusb version into it...
#mkdir libusb-1.0.24
#pushd libusb-1.0.24
#wget https://github.com/libusb/libusb/releases/download/v1.0.24/libusb-1.0.24.7z
#7z x libusb-1.0.24.7z
#cp VS2019/MS32/dll/libusb-1.0.dll ${PY_HOME}/Lib/site-packages/libusb/_platform/_windows/x86/libusb-1.0.dll
#popd

cp -r ${WINE_BUILD_DIR}/PortableGit ${WINEPREFIX}/drive_c/git

# now actually run pynitrokey build(s)
pushd ${WINE_BUILD_DIR}/nitrokey-app2

# upgrade pip to enable 'cryptography' install
py -m pip install -U pip
py -m pip install cryptography

# @fixme: obsolete?!
#cp /build/${LIBUSB} /build/${PY_HOME}/Lib/site-packages/usb/backend/

## install cx-Freeze for the msi build
#py -m pip install cx-Freeze

# install flit as our build system
py -m pip install flit

# install pynitrokey and dependencies
WINEPATH="C:\\git\\bin\\" py -m flit install --deps production

# build msi
#py win_setup.py bdist_msi
cp wine-build/nitropy.spec .

# build single-exe
py -m PyInstaller --noconfirm --clean --name nitrokey-app2-${NITROKEY_APP2_VERSION} --onefile nitropy.spec

#cp dist/pynitrokey-${PYNITROKEY_VERSION}-win32.msi /build/wine_base/drive_c/build
#cp dist/pynitrokey-${PYNITROKEY_VERSION}-win32.msi /build/wine_base/drive_c/build/pynitrokey.msi
#cp dist/nitropy-${PYNITROKEY_VERSION}.exe /build/wine_base/drive_c/build
cp /opt/wineprefix/drive_c/build/nitrokey-app2/dist/nitrokey-app2-*.exe /opt/wineprefix/drive_c/build/

popd
