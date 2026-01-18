"""系统托盘管理模块"""
from PySide6 import QtWidgets, QtCore

from utils import create_notebook_icon


class SystemTray:
    """处理系统托盘功能"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.tray_icon = QtWidgets.QSystemTrayIcon(main_window)
        self._setup_tray()

    def _setup_tray(self):
        """设置托盘图标和菜单"""
        self.tray_icon.setIcon(create_notebook_icon())
        self.tray_icon.setToolTip("ToDo 任务清单")
        
        # 创建托盘菜单
        tray_menu = QtWidgets.QMenu()
        
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self._show_window)
        
        hide_action = tray_menu.addAction("隐藏到托盘")
        hide_action.triggered.connect(self._hide_window)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("退出程序")
        quit_action.triggered.connect(self._quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # 双击托盘图标切换显示/隐藏
        self.tray_icon.activated.connect(self._on_tray_activated)

    def _show_window(self):
        """显示主窗口"""
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def _hide_window(self):
        """隐藏主窗口到托盘"""
        self.main_window.hide()

    def _on_tray_activated(self, reason):
        """托盘图标被激活"""
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.main_window.isVisible():
                self._hide_window()
            else:
                self._show_window()

    def _quit_app(self):
        """退出应用"""
        self.main_window.quit_application()

    def show_message(self, title: str, message: str, duration: int = 2000):
        """显示托盘通知"""
        self.tray_icon.showMessage(
            title, message, QtWidgets.QSystemTrayIcon.MessageIcon.Information, duration
        )