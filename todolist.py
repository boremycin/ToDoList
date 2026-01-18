"""
ToDo 任务清单应用 - 主入口
"""
import os
import sys

from PySide6 import QtWidgets

from main_window import MainWindow

DATA_FILE = os.path.join(os.path.dirname(__file__), "todo_data.json")


def main():
    """应用主函数"""
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    win = MainWindow(DATA_FILE)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()