#!/bin/bash

set -euxo pipefail

pushd wine-build

if [[ -e "./out" ]]; then
	echo "the temporary output dir: 'wine-build/out' exists, please delete!"
	exit 1
fi
docker build -t nk/wine-build .

mkdir -p out 
git clone .. out/nitrokey-app2

pushd out
mkdir -p PortableGit
pushd PortableGit
wget https://github.com/git-for-windows/git/releases/download/v2.38.1.windows.1/PortableGit-2.38.1-64-bit.7z.exe
7z x PortableGit-2.38.1-64-bit.7z.exe
popd
popd

docker run "$@" --mount type=bind,source="$(pwd)"/out,target=/opt/wineprefix/drive_c/build nk/wine-build

popd


echo "######################"
echo "to debug (enter the docker after building) just pass '-it' to this script!"
echo "additionally inside do: $ export WINEPREFIX=/build/wine_base "
echo "... this will allow direct usage of 'wine' with the correct wine-base-dir"
echo "######################"
