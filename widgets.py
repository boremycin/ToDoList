"""UI 组件模块 - 封装所有自定义 UI 控件"""
from typing import Optional
from PySide6 import QtCore, QtGui, QtWidgets
import time

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
        """鼠标释放 - 切换状态"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton: # type: ignore
            # 切换按钮状态并发射信号
            self.toggle()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        """鼠标进入 - 视觉反馈"""
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event: QtCore.QEvent) -> None:
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
        self.is_running = False  # 是否正在计时
        self.start_time = None  # 计时开始时间
        self.elapsed_time = 0  # 已消耗时间（秒）
        self.total_elapsed = 0  # 总共消耗时间（秒）

        # RGB动画计时器
        self.rgb_animation_timer = None
        self.hue_value = 0  # HSV色彩值，范围0-359
        
        # 防抖定时器 - 防止快速重复点击
        self.click_debounce_timer = None
        self.click_debounce_active = False

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

        # 计时标签
        self.timer_label = QtWidgets.QLabel("")
        self.timer_label.setFont(font)
        self.timer_label.setStyleSheet("color: #888888;")
        self.timer_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(self.timer_label)

        # 创建一个按钮容器，整合编辑和删除按钮
        button_container = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(2)  # 进一步减少按钮间距
        
        # 使用稍小的字体用于按钮
        button_font = QtGui.QFont()
        button_font.setPointSize(10)
        
        # 编辑按钮
        btn_edit = QtWidgets.QPushButton("编辑")
        btn_edit.setFixedWidth(46)
        btn_edit.setFont(button_font)
        btn_edit.clicked.connect(self.edit)
        button_layout.addWidget(btn_edit)

        # 删除按钮
        btn_del = QtWidgets.QPushButton("删除")
        btn_del.setFixedWidth(46)
        btn_del.setFont(button_font)
        btn_del.clicked.connect(self.delete)
        button_layout.addWidget(btn_del)
        
        # 防止按钮区域被压缩
        self.main_layout.addWidget(button_container, alignment=QtCore.Qt.AlignmentFlag.AlignVCenter)

        # 安装事件过滤器来处理标签点击事件
        self.label.installEventFilter(self)
        self.main_layout.itemAt(1).widget().setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))

    def eventFilter(self, obj, event):
        """事件过滤器 - 处理标签点击事件"""
        if obj is self.label and event.type() == QtCore.QEvent.Type.MouseButtonPress:
            mouse_event = event
            if mouse_event.button() == QtCore.Qt.MouseButton.LeftButton:
                # 防抖处理：如果在防抖时间内，忽略点击
                if self.click_debounce_active:
                    return True
                
                # 激活防抖，防止快速重复点击
                self.click_debounce_active = True
                self.click_debounce_timer = QtCore.QTimer(self)
                self.click_debounce_timer.setSingleShot(True)
                self.click_debounce_timer.timeout.connect(self._reset_debounce)
                self.click_debounce_timer.start(200)  # 200ms 内忽略重复点击
                
                # 发送changed信号给主窗口处理，由主窗口统一管理全局计时状态
                # 这样可以确保只有一个任务计时，且点击一次即可启动/停止
                self.changed.emit()
                        
                return True  # 标记事件已处理，防止进一步传播
                
        # 处理鼠标进入/离开事件以提供视觉反馈
        elif obj is self.label:
            if event.type() == QtCore.QEvent.Type.Enter:
                self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
                return True
            elif event.type() == QtCore.QEvent.Type.Leave:
                self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
                return True
                
        # 其他事件继续正常处理
        return super().eventFilter(obj, event)
    
    def _reset_debounce(self):
        """重置防抖标志"""
        self.click_debounce_active = False
        
    def start_timer(self):
        """开始计时 - 由主窗口控制"""
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time()
            self.update_style()
            # 启动RGB动画
            self._start_rgb_animation()
            # 立即刷新显示
            self.repaint()

    def stop_timer(self):
        """停止计时 - 由主窗口控制"""
        if self.is_running:
            self.is_running = False
            # 计算最终耗时
            if self.start_time:
                self.total_elapsed += time.time() - self.start_time
                self.start_time = None
            self.update_style()
            
            # 停止RGB动画
            self._stop_rgb_animation()
            
            # 立即更新计时显示
            self.update_timer_display()
            
            # 发送changed信号以确保数据保存
            self.changed.emit()
    
    def update_timer_display(self):
        """更新计时显示 - 由主窗口的全局计时器调用"""
        if self.is_running and self.start_time is not None:
            current_elapsed = self.total_elapsed + (time.time() - self.start_time)
            self.timer_label.setText(self.format_time(current_elapsed))
        else:
            self.timer_label.setText(self.format_time(self.total_elapsed))
        # 立即更新UI显示 - 使用repaint强制立即刷新，而不是update队列
        self.timer_label.repaint()
        self.main_layout.update()  # 同时更新主布局确保布局正确

    def _start_rgb_animation(self):
        """启动RGB动画效果"""
        if self.rgb_animation_timer is None:
            self.rgb_animation_timer = QtCore.QTimer(self)  # 设置 parent，确保线程安全
            self.rgb_animation_timer.timeout.connect(self._animate_rgb)
            self.rgb_animation_timer.start(50)  # 每50ms更新一次颜色

    def _stop_rgb_animation(self):
        """停止RGB动画效果"""
        if self.rgb_animation_timer is not None:
            self.rgb_animation_timer.stop()
            try:
                self.rgb_animation_timer.timeout.disconnect()
            except TypeError:
                # 如果信号没有连接，会抛出TypeError
                pass
            self.rgb_animation_timer = None

    def _animate_rgb(self):
        """RGB动画更新"""
        # 循环更新HSV值中的H（色相），产生彩虹效果
        self.hue_value = (self.hue_value + 2) % 360
        color = QtGui.QColor.fromHsv(self.hue_value, 255, 255)
        self.setStyleSheet(f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 50); border-radius: 5px;")

    def format_time(self, seconds):
        """格式化时间显示"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

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
            # 停止RGB动画，恢复正常样式
            if self.rgb_animation_timer:
                self._stop_rgb_animation()
            self.setStyleSheet("")
        elif self.is_running:
            # 正在运行时的特殊样式 - 由RGB动画处理
            self.label.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        else:
            f.setStrikeOut(False)
            self.label.setStyleSheet("color: #111111;")
            # 停止RGB动画，恢复正常样式
            if self.rgb_animation_timer:
                self._stop_rgb_animation()
            self.setStyleSheet("")
        self.label.setFont(f)
        self.label.repaint()  # 使用repaint强制立即刷新
        self.repaint()  # 也刷新整个组件

    def on_toggled(self, checked: bool):
        """切换状态时的处理"""
        self.checked = checked
        # 如果任务完成，停止计时
        if checked and self.is_running:
            self.stop_timer()
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
        # 删除前停止计时
        if self.is_running:
            self.stop_timer()
        self.cleanup()
        self.removed.emit(self)

    def cleanup(self):
        """清理所有定时器和资源 - 在删除前必须调用"""
        # 停止RGB动画定时器
        if self.rgb_animation_timer is not None:
            self.rgb_animation_timer.stop()
            try:
                self.rgb_animation_timer.timeout.disconnect()
            except TypeError:
                pass
            self.rgb_animation_timer = None
        
        # 停止防抖定时器
        if self.click_debounce_timer is not None:
            self.click_debounce_timer.stop()
            self.click_debounce_timer = None

    def to_dict(self) -> dict:
        """转换为字典格式用于数据保存"""
        # 如果任务正在运行，需要计算当前总时间，但不能改变运行状态
        current_total = self.total_elapsed
        if self.is_running and self.start_time is not None:
            # 临时计算总时间，但不改变实际状态
            current_total += time.time() - self.start_time
        
        return {
            "text": self.label.text(), 
            "checked": bool(self.checked),
            "total_elapsed": current_total
        }

    def load_from_dict(self, data: dict):
        """从字典加载数据"""
        self.total_elapsed = data.get("total_elapsed", 0)
        # 修复：调用正确的update_timer_display方法
        self.update_timer_display()