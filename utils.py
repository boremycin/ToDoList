"""图标和 UI 工具模块"""
from PySide6 import QtGui, QtWidgets
import os


def create_notebook_icon():
    """创建笔记本图标"""
    # 尝试从资源文件创建图标，如果不存在则使用内建图标
    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    if os.path.exists(icon_path):
        return QtGui.QIcon(icon_path)
    else:
        # 创建一个简单的内建图标
        pixmap = QtGui.QPixmap(64, 64)
        pixmap.fill(QtGui.QColor(255, 255, 255))
        
        painter = QtGui.QPainter(pixmap)
        painter.setBrush(QtGui.QColor(40, 120, 220))
        painter.setPen(QtGui.QColor(30, 100, 200))
        painter.drawRect(5, 5, 54, 54)
        
        painter.setBrush(QtGui.QColor(255, 255, 255))
        painter.drawRect(10, 10, 44, 44)
        
        # Draw lines to represent notebook pages
        for i in range(5):
            y = 15 + i * 7
            painter.setPen(QtGui.QColor(0, 0, 0))
            painter.drawLine(15, y, 45, y)
        
        painter.end()
        
        return QtGui.QIcon(pixmap)


def create_font(size: int, bold: bool = False):
    """创建字体"""
    font = QtGui.QFont()
    font.setPointSize(size)
    font.setBold(bold)
    return font