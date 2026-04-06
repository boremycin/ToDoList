from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs


pyside6_datas = collect_data_files(
    "PySide6",
    includes=[
        "plugins/*/*",
        "translations/*",
    ],
)

pyside6_binaries = collect_dynamic_libs("PySide6") + collect_dynamic_libs("shiboken6")


a = Analysis(
    ["todolist.py"],
    pathex=[],
    binaries=pyside6_binaries,
    datas=[
        ("icon.png", "."),
        ("todo_data.json", "."),
    ] + pyside6_datas,
    hiddenimports=[
        "PySide6",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtNetwork",
        "shiboken6",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["runtime_hook_dll_path.py"],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RecordToday",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="icon.png",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="RecordToday",
)
