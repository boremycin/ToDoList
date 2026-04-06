import os
import sys
import ctypes


def _show_bootstrap_error(message: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(None, message, "RecordToday Startup Error", 0x10)
    except Exception:
        pass


def _write_bootstrap_log(lines: list[str]) -> str | None:
    try:
        base_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(base_dir, "startup_diagnostics.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return log_path
    except Exception:
        return None


def _bootstrap_dll_search_path() -> None:
    if not getattr(sys, "frozen", False):
        return

    base_dir = os.path.dirname(sys.executable)
    internal_dir = os.path.join(base_dir, "_internal")
    candidate_dirs = [
        internal_dir,
        os.path.join(internal_dir, "PySide6"),
        os.path.join(internal_dir, "shiboken6"),
    ]

    for path in candidate_dirs:
        if not os.path.isdir(path):
            continue
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(path)

    current_path = os.environ.get("PATH", "")
    prepend = [path for path in candidate_dirs if os.path.isdir(path)]
    if prepend:
        os.environ["PATH"] = os.pathsep.join(prepend + ([current_path] if current_path else []))


def _preflight_qt_runtime() -> None:
    if not getattr(sys, "frozen", False):
        return

    base_dir = os.path.dirname(sys.executable)
    internal_dir = os.path.join(base_dir, "_internal")
    pyside6_dir = os.path.join(internal_dir, "PySide6")
    shiboken6_dir = os.path.join(internal_dir, "shiboken6")

    diagnostics = [
        f"Executable: {sys.executable}",
        f"Base dir: {base_dir}",
        f"Internal dir exists: {os.path.isdir(internal_dir)}",
        f"PySide6 dir exists: {os.path.isdir(pyside6_dir)}",
        f"shiboken6 dir exists: {os.path.isdir(shiboken6_dir)}",
        "",
        "DLL preload results:",
    ]

    preload_targets = [
        os.path.join(internal_dir, "python311.dll"),
        os.path.join(internal_dir, "vcruntime140.dll"),
        os.path.join(internal_dir, "vcruntime140_1.dll"),
        os.path.join(internal_dir, "vcruntime140_threads.dll"),
        os.path.join(internal_dir, "msvcp140.dll"),
        os.path.join(internal_dir, "msvcp140_1.dll"),
        os.path.join(internal_dir, "msvcp140_2.dll"),
        os.path.join(internal_dir, "msvcp140_atomic_wait.dll"),
        os.path.join(internal_dir, "ucrtbase.dll"),
        os.path.join(pyside6_dir, "shiboken6.abi3.dll"),
        os.path.join(shiboken6_dir, "shiboken6.abi3.dll"),
        os.path.join(pyside6_dir, "Qt6Core.dll"),
        os.path.join(pyside6_dir, "Qt6Gui.dll"),
        os.path.join(pyside6_dir, "Qt6Widgets.dll"),
        os.path.join(pyside6_dir, "opengl32sw.dll"),
    ]

    for target in preload_targets:
        if not os.path.exists(target):
            diagnostics.append(f"MISSING: {target}")
            continue
        try:
            ctypes.WinDLL(target)
            diagnostics.append(f"OK: {target}")
        except OSError as exc:
            diagnostics.append(f"FAIL: {target} -> {exc}")
            log_path = _write_bootstrap_log(diagnostics)
            message = "A required runtime DLL failed to load before Qt startup."
            if log_path:
                message += f"\n\nDiagnostic log:\n{log_path}"
            _show_bootstrap_error(message)
            raise


_bootstrap_dll_search_path()
_preflight_qt_runtime()

from PySide6 import QtWidgets

from app_paths import get_data_file_path
from main_window import MainWindow

DATA_FILE = get_data_file_path()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    win = MainWindow(DATA_FILE)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
