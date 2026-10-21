# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller onedir build for Subtitler."""
from PyInstaller.utils.hooks import collect_all


def collect_optional(package):
    try:
        return collect_all(package)
    except (ImportError, ModuleNotFoundError):
        return [], [], []


datas = [(".env.example", ".")]
binaries = []
hiddenimports = [
    "openai",
    "deepgram",
    "pysubs2",
    "app.ui",
    "app.pipeline",
]
for package in ("gradio", "gradio_client", "groovy", "safehttpx", "pydub"):
    package_datas, package_binaries, package_hiddenimports = collect_optional(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

analysis = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="Subtitler",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="Subtitler",
)
