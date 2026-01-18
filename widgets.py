"""UI 组件模块 - 封装所有自定义 UI 控件"""
from typing import Optional
from PySide6 import QtCore, QtGui, QtWidgets


class CircleToggle(QtWidgets.QPushButton):
    """圆形切换按钮 - 显示选中/未选中状态"""

    toggled = QtCore.Signal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setFixedSize(20, 20)
        self.setFlat(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.setMouseTracking(True)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """绘制圆形按钮"""
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(2, 2, -2, -2)
        
        if self.isChecked():
            # 选中状态：填充蓝色圆圈 + 白色勾号
            brush = QtGui.QBrush(QtGui.QColor(40, 120, 220))
            p.setBrush(brush)
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.drawEllipse(r)
            
            # 绘制白色勾号
            p.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.white, 1.8, QtCore.Qt.PenStyle.SolidLine, 
                               QtCore.Qt.PenCapStyle.RoundCap, QtCore.Qt.PenJoinStyle.RoundJoin))
            w, h = self.width(), self.height()
            path = QtGui.QPainterPath()
            path.moveTo(w * 0.25, h * 0.5)
            path.lineTo(w * 0.4, h * 0.65)
            path.lineTo(w * 0.75, h * 0.35)
            p.drawPath(path)
        else:
            # 未选中状态：空心圆圈
            pen = QtGui.QPen(QtGui.QColor(120, 120, 120))
            pen.setWidthF(1.5)
            p.setPen(pen)
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            p.drawEllipse(r)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """鼠标释放 - 确保状态正确"""
        if event.button() == QtCore.Qt.LeftButton: # type: ignore
            self.update()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        """鼠标进入 - 视觉反馈"""
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event: QtGui.QKeyEvent) -> None:
        """鼠标离开 - 更新显示"""
        super().leaveEvent(event)
        self.update()


class TaskWidget(QtWidgets.QWidget):
    """单个任务项组件"""
    
    changed = QtCore.Signal()
    removed = QtCore.Signal(object)  # 发出 self 信号以通知父窗口删除该任务

    def __init__(self, text: str, checked: bool = False, parent=None):
        super().__init__(parent)
        self.text = text
        self.checked = checked

        # 创建布局
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(6, 4, 6, 4)
        self.main_layout.setSpacing(10)

        self.toggle = CircleToggle(checked)
        self.toggle.toggled.connect(self.on_toggled)
        self.main_layout.addWidget(self.toggle, alignment=QtCore.Qt.AlignmentFlag.AlignVCenter)

        # 任务文本标签
        self.label = QtWidgets.QLabel(self.text)
        self.label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, 
            QtWidgets.QSizePolicy.Policy.Preferred
        )
        font = self._create_font(12)
        self.label.setFont(font)
        self.update_style()
        self.main_layout.addWidget(self.label)

        # 编辑按钮
        btn_edit = QtWidgets.QPushButton("编辑")
        btn_edit.setFixedWidth(60)
        btn_edit.setFont(font)
        btn_edit.clicked.connect(self.edit)
        self.main_layout.addWidget(btn_edit)

        # 删除按钮
        btn_del = QtWidgets.QPushButton("删除")
        btn_del.setFixedWidth(70)
        btn_del.setFont(font)
        btn_del.clicked.connect(self.delete)
        self.main_layout.addWidget(btn_del)

    @staticmethod
    def _create_font(size: int) -> QtGui.QFont:
        """创建指定大小的字体"""
        font = QtGui.QFont()
        font.setPointSize(size)
        return font

    def update_style(self):
        """更新文本样式（删除线和颜色）"""
        f = self.label.font()
        if self.toggle.isChecked():
            f.setStrikeOut(True)
            self.label.setStyleSheet("color: #888888;")
        else:
            f.setStrikeOut(False)
            self.label.setStyleSheet("color: #111111;")
        self.label.setFont(f)
        self.label.update()

    def on_toggled(self, checked: bool):
        """切换状态时的处理"""
        self.checked = checked
        self.update_style()
        self.changed.emit()
        self.update()

    def edit(self):
        """编辑任务内容"""
        text, ok = QtWidgets.QInputDialog.getText(
            self, "编辑任务", "任务内容:", text=self.label.text()
        )
        if ok:
            self.label.setText(text)
            self.text = text
            self.changed.emit()

    def delete(self):
        """删除任务"""
        self.removed.emit(self)

    def to_dict(self) -> dict:
        """转换为字典格式用于数据保存"""
        return {"text": self.label.text(), "checked": bool(self.checked)}
