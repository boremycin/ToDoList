"""系统托盘管理模块"""
from PySide6 import QtWidgets, QtCore

from utils import create_notebook_icon
from time_rings import FloatingTimeRings


class SystemTray:
    """处理系统托盘功能"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.tray_icon = QtWidgets.QSystemTrayIcon(main_window)
        self.floating_rings = None  # 悬浮时间圆环组件
        self._setup_tray()

    def _setup_tray(self):
        """设置托盘图标和菜单"""
        self.tray_icon.setIcon(create_notebook_icon())
        self.tray_icon.setToolTip("ToDo 任务清单")
        
        # 创建托盘菜单
        tray_menu = QtWidgets.QMenu()
        
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self._show_window)
        
        # toggle_floating_action = tray_menu.addAction("切换悬浮圆环")
        # toggle_floating_action.triggered.connect(self._toggle_floating_rings)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("退出程序")
        quit_action.triggered.connect(self._quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # 双击托盘图标切换显示/隐藏
        self.tray_icon.activated.connect(self._on_tray_activated)

    def _show_window(self):
        """显示主窗口"""
        # 如果有悬浮圆环，先隐藏它
        if self.floating_rings and self.floating_rings.isVisible():
            self.floating_rings.hide()
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def _toggle_floating_rings(self):
        """切换悬浮时间圆环的显示/隐藏"""
        if not self.floating_rings:
            # 创建悬浮圆环
            self.floating_rings = FloatingTimeRings()
            self.floating_rings.show()
        else:
            if self.floating_rings.isVisible():
                self.floating_rings.hide()
            else:
                self.floating_rings.show()
                # 确保不遮挡其他窗口
                self.floating_rings.raise_()

    def _hide_window(self):
        """隐藏主窗口到托盘，并显示悬浮圆环"""
        self.main_window.hide()
        # # 自动显示悬浮圆环
        # if not self.floating_rings:
        #     self.floating_rings = FloatingTimeRings()
        # if not self.floating_rings.isVisible():
        #     self.floating_rings.show()

    def _on_tray_activated(self, reason):
        """托盘图标被激活"""
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.main_window.isVisible():
                self._hide_window()
            else:
                self._show_window()

    def _quit_app(self):
        """退出应用"""
        if self.floating_rings and self.floating_rings.isVisible():
            self.floating_rings.close()
        self.main_window.quit_application()

    def show_message(self, title: str, message: str, duration: int = 2000):
        """显示托盘通知"""
        self.tray_icon.showMessage(
            title, message, QtWidgets.QSystemTrayIcon.MessageIcon.Information, duration
        )