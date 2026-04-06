import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
RELEASE_DIR = ROOT / "release"
APP_NAME = "RecordToday"
PACKAGE_NAME = "RecordToday-windows-portable-fixed"


def verify_build_dependencies() -> None:
    required_modules = ["PySide6", "PyInstaller"]
    missing = []
    for module_name in required_modules:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(module_name)

    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            f"Missing build dependencies: {missing_text}. "
            "Install them into the active Python environment before packaging."
        )


def clean_build_dirs() -> None:
    for path in (DIST_DIR, BUILD_DIR):
        if path.exists():
            shutil.rmtree(path)


def build_executable() -> Path:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "RecordToday.spec",
        "--noconfirm",
        "--clean",
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)
    return DIST_DIR / APP_NAME


def stage_release_files(app_dir: Path) -> Path:
    package_dir = RELEASE_DIR / PACKAGE_NAME
    if package_dir.exists():
        shutil.rmtree(package_dir)
    shutil.copytree(app_dir, package_dir)

    # Keep core Qt and CRT dependencies next to PySide6 DLLs for cleaner resolution on target machines.
    pyside6_dir = package_dir / "_internal" / "PySide6"
    internal_dir = package_dir / "_internal"
    env_root = Path(sys.executable).resolve().parent
    library_bin = env_root / "Library" / "bin"

    runtime_patterns = [
        "api-ms-win-*.dll",
        "concrt140.dll",
        "msvcp140*.dll",
        "python3.dll",
        "python*.dll",
        "ucrtbase.dll",
        "vc*.dll",
        "vcruntime*.dll",
        "zlib.dll",
        "libcrypto-*.dll",
        "libssl-*.dll",
        "libbz2.dll",
        "liblzma.dll",
        "bzip2.dll",
        "expat.dll",
        "libexpat.dll",
        "sqlite3.dll",
        "ffi*.dll",
    ]

    def copy_matching_dlls(source_dir: Path) -> None:
        if not source_dir.exists():
            return

        for pattern in runtime_patterns:
            for source in source_dir.glob(pattern):
                if not source.is_file():
                    continue

                for target_dir in (internal_dir, pyside6_dir):
                    destination = target_dir / source.name
                    if not destination.exists():
                        shutil.copy2(source, destination)

    copy_matching_dlls(env_root)
    copy_matching_dlls(library_bin)

    # Remove incompatible ICU DLLs if PyInstaller collected them from unrelated locations.
    for target_dir in (internal_dir, pyside6_dir):
        for dll_name in ("icudt73.dll", "icuuc.dll", "icuin.dll"):
            dll_path = target_dir / dll_name
            if dll_path.exists():
                dll_path.unlink()

    shutil.copy2(ROOT / "README.md", package_dir / "README.md")
    shutil.copy2(ROOT / "LICENSE", package_dir / "LICENSE")

    zip_base = RELEASE_DIR / PACKAGE_NAME
    return Path(shutil.make_archive(str(zip_base), "zip", package_dir.parent, package_dir.name))


def main() -> None:
    verify_build_dependencies()
    clean_build_dirs()
    app_dir = build_executable()
    zip_path = stage_release_files(app_dir)
    print(f"Built application directory: {app_dir}")
    print(f"Created portable zip: {zip_path}")


if __name__ == "__main__":
    main()
