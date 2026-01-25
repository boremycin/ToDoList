"""
ToDo 任务清单应用 - 主入口
"""
import os
import sys

from PySide6 import QtWidgets

from main_window import MainWindow

def get_application_path():
    """获取应用程序的实际路径，用于处理PyInstaller打包后的资源定位"""
    if getattr(sys, 'frozen', False):  # 判断是否为打包后的可执行文件
        return os.path.dirname(sys.executable)
    else:  # 开发环境
        return os.path.dirname(__file__)

DATA_FILE = os.path.join(get_application_path(), "todo_data.json")


def main():
    """应用主函数"""
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    win = MainWindow(DATA_FILE)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()