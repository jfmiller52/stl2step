# -*- mode: python ; coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 stl2step contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""PyInstaller one-file spec for the stl2step GUI."""

import sys
from pathlib import Path

from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_all

block_cipher = None
ROOT = Path(SPECPATH).resolve()

datas = []
binaries = []
hiddenimports = [
    "stl2step",
    "stl2step.convert",
    "stl2step.gui",
    "stl2step.gui.main_window",
    "stl2step.gui.viewer",
    "stl2step.gui.worker",
    "OCP",
    "cadquery",
    "cadquery.occ_impl",
    "cadquery.occ_impl.exporters",
    "cadquery.occ_impl.importers",
    "vtkmodules",
    "vtkmodules.all",
    "vtkmodules.util",
    "vtkmodules.util.numpy_support",
    "pyvista",
    "pyvistaqt",
    "stl",
    "numpy",
]

# CadQuery / VTK / viewer natives. Do not collect_all('PyQt6') — hooks pull
# what we import, and full Qt Quick/QML trees break macOS one-file extraction.
for package in ("casadi", "OCP", "cadquery", "vtkmodules", "pyvista", "pyvistaqt"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

_SKIP_FRAGMENTS = (
    "QtQuick",
    "QtQml",
    "Qt3D",
    "QtWebEngine",
    "QtWebView",
    "QtMultimedia",
    "QtBluetooth",
    "QtNfc",
    "QtSensors",
    "QtLocation",
    "QtPositioning",
    "QtPdf",
    "QtVirtualKeyboard",
)


def _keep(entry_name: str) -> bool:
    return not any(frag in entry_name for frag in _SKIP_FRAGMENTS)


a = Analysis(
    [str(ROOT / "pyinstaller_entry" / "run_gui.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "_tkinter",
        "matplotlib.tests",
        "pytest",
        "PyQt6.QtQuick",
        "PyQt6.QtQml",
        "PyQt6.Qt3DCore",
        "PyQt6.QtWebEngineCore",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.binaries = [b for b in a.binaries if _keep(b[0])]
a.datas = [d for d in a.datas if _keep(d[0])]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="stl2step-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=sys.platform == "darwin",
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
