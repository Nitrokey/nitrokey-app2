# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata
import os
import sys

venv_path = os.popen('poetry env info --path').read().rstrip()
python_version = str(sys.version_info[0]) + '.' + str(sys.version_info[1])

datas = [
    (venv_path + '/lib/python' + python_version + '/site-packages/fido2/public_suffix_list.dat', 'fido2'),
    ('../../../nitrokeyapp/ui', 'nitrokeyapp/ui'),
    ('../../../LICENSE', '.')
]
datas += copy_metadata('ecdsa')
datas += copy_metadata('fido2')
datas += copy_metadata('nitrokeyapp')
datas += copy_metadata('nitrokey')

a = Analysis(
    ['../../../nitrokeyapp/__main__.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

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
    target_arch='x86_64',
    codesign_identity=None,
    entitlements_file=None,
    contents_directory='.',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='nitrokey-app2',
)
app = BUNDLE(
    coll,
    name='nitrokey-app2.app',
    icon='nitrokey-app.icns',
    bundle_identifier=None,
)
