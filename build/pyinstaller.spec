# -*- mode: python ; coding: utf-8 -*-
import argparse
import shutil

# Argument
parser = argparse.ArgumentParser(description="Pass arguments to PyInstaller")
parser.add_argument(
    "--version",
    type=str,
    help="Version used on output folder",
)
parser.add_argument("--dev", action="store_true", help="Only build executable with conslo enabled")
args = parser.parse_args()
isdevelopment = bool(args.dev)
version: str = args.version if not isdevelopment else args.version + "-dev"

# Variables
name = "KeyTik"
output_dir = f"{name} {version}"

a = Analysis(
    [f"..\\{name.lower()}\\main.py"],
    pathex=[],
    binaries=[],
    datas=[
        (f"..\\{name.lower()}\\_internal\\Data", "Data"),
        (
            "..\\.venv\\Lib\\site-packages\\pyqcodeeditor\\resources",
            "pyqcodeeditor\\resources",
        ),
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
    [],
    exclude_binaries=True,
    name=name if not isdevelopment else f"{name} Console",
    debug=isdevelopment,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=isdevelopment,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[f"..\\{name.lower()}\\_internal\\Data\\icon.ico"],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=output_dir,
)

shutil.copy2("LICENSE", f"build/dist/{output_dir}")
