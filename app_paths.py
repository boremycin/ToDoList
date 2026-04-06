import os
import sys


def get_application_path() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_resource_path(filename: str) -> str:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(get_application_path(), filename)


def get_data_file_path(filename: str = "todo_data.json") -> str:
    return os.path.join(get_application_path(), filename)
