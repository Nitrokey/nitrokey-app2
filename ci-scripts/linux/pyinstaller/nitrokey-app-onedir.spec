# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata

datas = [
    ('../../../venv/lib/python3.9/site-packages/fido2/public_suffix_list.dat', 'fido2'),
    ('../../../venv/lib/python3.9/site-packages/pynitrokey/VERSION', 'pynitrokey'),
    ('../../../nitrokeyapp/ui', 'nitrokeyapp/ui'),
    ('../../../nitrokeyapp/VERSION', 'nitrokeyapp'),
    ('../../../LICENSE', '.')
]
datas += copy_metadata('ecdsa')
datas += copy_metadata('fido2')
datas += copy_metadata('nitrokeyapp')
datas += copy_metadata('pynitrokey')
datas += copy_metadata('pyusb')
datas += copy_metadata('spsdk')


block_cipher = None


a = Analysis(
    ['../../../nitrokeyapp/__main__.py'],
    pathex=[],
    binaries=[
        ('../../../venv/lib/python3.9/site-packages/libusbsio/bin/linux_x86_64/libusbsio.so', 'libusbsio')
    ],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='nitrokey-app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='nitrokey-app',
)
