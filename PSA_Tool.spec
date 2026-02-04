# -*- mode: python ; coding: utf-8 -*-
import glob

a = Analysis(
    ['PSA_Tool.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('animations\\logo_load_animation.json', 'animations'),
        ('animations\\images\\img_0.png', 'animations\\images'),
    ] + [
        (src, 'animations\\Frames\\LoadLogoAnimimation')
        for src in glob.glob('animations\\Frames\\LoadLogoAnimimation\\*.png')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='PSA_Tool',
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
)
