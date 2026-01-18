"""图标和 UI 工具模块"""
from PySide6 import QtCore, QtGui


def create_notebook_icon() -> QtGui.QIcon:
    """创建笔记本样式的应用图标"""
    icon = QtGui.QIcon()
    pixmap = QtGui.QPixmap(32, 32)
    pixmap.fill(QtGui.QColor(0, 0, 0, 0))
    
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    
    # 绘制笔记本背景
    painter.setPen(QtGui.QPen(QtGui.QColor(50, 50, 50), 1))
    painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 255, 240)))
    painter.drawRoundedRect(2, 2, 28, 28, 3, 3)
    
    # 绘制左侧装订线
    painter.setPen(QtGui.QPen(QtGui.QColor(200, 200, 200), 2))
    painter.drawLine(8, 4, 8, 28)
    
    # 绘制横线
    painter.setPen(QtGui.QPen(QtGui.QColor(180, 180, 180), 1))
    for i in range(3):
        y = 8 + i * 6
        painter.drawLine(10, y, 26, y)
    
    # 绘制文字点
    painter.setPen(QtGui.QPen(QtGui.QColor(100, 100, 100), 1))
    painter.drawEllipse(12, 10, 2, 2)
    painter.drawEllipse(12, 16, 2, 2)
    painter.drawEllipse(12, 22, 2, 2)
    
    painter.end()
    icon.addPixmap(pixmap)
    return icon


def create_font(size: int, bold: bool = False) -> QtGui.QFont:
    """创建指定大小的字体"""
    font = QtGui.QFont()
    font.setPointSize(size)
    font.setBold(bold)
    return font
