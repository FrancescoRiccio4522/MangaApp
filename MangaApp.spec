# -*- mode: python ; coding: utf-8 -*-
# Build:  pyinstaller --noconfirm MangaApp.spec
#   Windows / Linux -> un unico eseguibile in dist/
#   macOS           -> dist/MangaApp.app
import sys

from PyInstaller.utils.hooks import collect_data_files

MAC = sys.platform == "darwin"
WINDOWS = sys.platform == "win32"
VERSIONE = "2.0.0"

a = Analysis(
    ["MangaApp.py"],
    pathex=[],
    binaries=[],
    datas=[("icon.png", "."), ("icon.ico", ".")] + collect_data_files("customtkinter"),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

if MAC:
    # Su macOS serve un vero bundle .app (onefile + finestra è deprecato da PyInstaller)
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="MangaApp",
        console=False,
        argv_emulation=False,
        upx=False,
        icon="icon.icns",
    )
    coll = COLLECT(exe, a.binaries, a.datas, name="MangaApp", upx=False)
    app = BUNDLE(
        coll,
        name="MangaApp.app",
        icon="icon.icns",
        bundle_identifier="io.github.francescoriccio4522.mangaapp",
        version=VERSIONE,
        info_plist={
            "CFBundleName": "MangaApp",
            "CFBundleDisplayName": "MangaApp",
            "CFBundleShortVersionString": VERSIONE,
            "NSHighResolutionCapable": True,
            # Barra del titolo scura quando il Mac è in modalità scura
            "NSRequiresAquaSystemAppearance": False,
            "LSApplicationCategoryType": "public.app-category.utilities",
            "NSDownloadsFolderUsageDescription": "MangaApp salva i PDF dei capitoli nella cartella Download.",
            "NSDocumentsFolderUsageDescription": "MangaApp salva i PDF dei capitoli nella cartella scelta.",
            "NSDesktopFolderUsageDescription": "MangaApp salva i PDF dei capitoli nella cartella scelta.",
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="MangaApp",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        icon="icon.ico" if WINDOWS else None,
    )
