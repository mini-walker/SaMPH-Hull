# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('src/SaMPH_Images', 'SaMPH/SaMPH_Images')]
datas += collect_data_files('matplotlib')
datas += collect_data_files('latex2mathml')
datas += collect_data_files('reportlab')


a = Analysis(
    ['src\\Main.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=['matplotlib', 'matplotlib.pyplot', 'matplotlib.backends.backend_agg', 'latex2mathml', 'latex2mathml.converter', 'scipy.special.cython_special'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'IPython', 'pandas', 'setuptools'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SaMPH-Hull',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['src\\SaMPH_Images\\planing-hull-app-logo.ico'],
)
