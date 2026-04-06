import os

from PySide6 import QtGui

from app_paths import get_resource_path


def create_notebook_icon():
    icon_path = get_resource_path("icon.png")
    if os.path.exists(icon_path):
        return QtGui.QIcon(icon_path)

    pixmap = QtGui.QPixmap(64, 64)
    pixmap.fill(QtGui.QColor(255, 255, 255))

    painter = QtGui.QPainter(pixmap)
    painter.setBrush(QtGui.QColor(40, 120, 220))
    painter.setPen(QtGui.QColor(30, 100, 200))
    painter.drawRect(5, 5, 54, 54)

    painter.setBrush(QtGui.QColor(255, 255, 255))
    painter.drawRect(10, 10, 44, 44)

    for i in range(5):
        y = 15 + i * 7
        painter.setPen(QtGui.QColor(0, 0, 0))
        painter.drawLine(15, y, 45, y)

    painter.end()
    return QtGui.QIcon(pixmap)


def create_font(size: int, bold: bool = False):
    font = QtGui.QFont("Microsoft YaHei UI")
    if not font.exactMatch():
        font = QtGui.QFont("Microsoft YaHei")
    if not font.exactMatch():
        font = QtGui.QFont("Segoe UI")
    font.setPointSize(size)
    font.setBold(bold)
    return font
