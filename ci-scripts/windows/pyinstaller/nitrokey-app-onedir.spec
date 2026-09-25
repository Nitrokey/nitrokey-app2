# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.utils.win32.versioninfo import VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct, VarFileInfo, VarStruct
from importlib.metadata import version
from packaging.version import parse
import importlib.metadata
import os

venv_path = os.popen('poetry env info --path').read().rstrip()

datas = [
    (venv_path + '\\Lib\\site-packages\\fido2\\public_suffix_list.dat', 'fido2'),
    ('..\\..\\..\\nitrokeyapp\\ui', 'nitrokeyapp\\ui'),
    ('..\\..\\..\\LICENSE', '.')
]
datas += copy_metadata('fido2')
datas += copy_metadata('nitrokeyapp')
datas += copy_metadata('nitrokey')


block_cipher = None


try:
    version = parse(version('nitrokeyapp'))
except importlib.metadata.PackageNotFoundError:
    raise Exception("Nitrokeyapp was not found. Make sure it is installed.")
except packaging.version.InvalidVersion:
    raise Exception("Could not parse version from nitrokeyapp installation.")

major = version.major
minor = version.minor
patch = version.micro
build = version.pre[1] if version.pre is not None and isinstance(version.pre[1], int) else 0
flags = 0x2 if version.pre is not None else 0x0

versioninfo = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers = (major, minor, patch, build),
        prodvers = (major, minor, patch, build),
        mask = 0x3f,
        flags = flags,
        OS = 0x40004,
        fileType = 0x1,
        subtype = 0x0,
        date = (0,0)
    ),
    kids=[
        StringFileInfo([
            StringTable(
                u'040904B0',
                [
                    StringStruct('CompanyName', 'Nitrokey GmbH'),
                    StringStruct('FileDescription', 'Graphical application to manage Nitrokey devices'),
                    StringStruct('FileVersion', f"{str(version)}"),
                    StringStruct('InternalName', 'Nitrokey App 2'),
                    StringStruct('LegalCopyright', 'Nitrokey GmbH and contributors'),
                    StringStruct('OriginalFilename', 'nitrokey-app2.exe'),
                    StringStruct('ProductName', 'Nitrokey App 2'),
                    StringStruct('ProductVersion', f"{str(version)}")
                ]
            )
        ]),
        VarFileInfo([VarStruct(u'Translation', [1033, 4608])])
    ]
)


a = Analysis(
    ['..\\..\\..\\nitrokeyapp\\__main__.py'],
    pathex=[],
    binaries=[],
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
    name='nitrokey-app2',
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
    icon=['nitrokey-app.ico'],
    version=versioninfo,
    uac_admin=False,
    contents_directory='.',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='nitrokey-app2',
)
