import os
import sys


def _add_directory(path: str) -> None:
    if not os.path.isdir(path):
        return

    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(path)

    current_path = os.environ.get("PATH", "")
    if path not in current_path.split(os.pathsep):
        os.environ["PATH"] = path + os.pathsep + current_path if current_path else path


if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    base_dir = sys._MEIPASS
    _add_directory(base_dir)
    _add_directory(os.path.join(base_dir, "PySide6"))
    _add_directory(os.path.join(base_dir, "shiboken6"))
