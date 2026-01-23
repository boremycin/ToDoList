from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import QTimer, QRectF, Qt, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QMouseEvent
import datetime
import calendar

class TimeRingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(350, 350) 
        self.working_mode = True  # 默认为工作模式

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50) 

    def set_working_mode(self, is_working):
        """设置工作模式状态"""
        self.working_mode = is_working
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        now = datetime.datetime.now()
        
        # --- 进度计算 (保持平滑旋转) ---
        days_in_mo = calendar.monthrange(now.year, now.month)[1]
        days_in_yr = 366 if calendar.isleap(now.year) else 365
        
        sec_ratio = (now.second + now.microsecond / 1_000_000) / 60
        min_ratio = (now.minute + sec_ratio) / 60
        hour_ratio = (now.hour + min_ratio) / 24
        day_ratio = (now.day - 1 + hour_ratio) / days_in_mo
        year_ratio = (now.timetuple().tm_yday - 1 + hour_ratio) / days_in_yr

        # 定义四个环的信息：(标签, 进度, 颜色, 中心显示的准确信息)
        rings = [
            ("YEAR", year_ratio, QColor(255, 85, 85), now.strftime("%Y")),
            ("MONTH", day_ratio, QColor(85, 170, 255), now.strftime("%b %d")),
            ("DAY", hour_ratio, QColor(85, 255, 150), now.strftime("%A")),
            ("HOUR", min_ratio, QColor(255, 200, 85), now.strftime("%H:%M:%S")),
        ]

        # --- 2x2 矩阵动态布局 ---
        w = self.width() / 2
        h = self.height() / 2
        
        # 放大圆环：利用象限最小边的 95%
        cell_size = min(w, h)
        radius = (cell_size * 0.95) / 2 
        thickness = radius * 0.15  # 调整线条粗细比例
        
        # 减小圆环绘制区域，防止贴边过紧
        draw_radius = radius - (thickness / 2) - 5

        for i, (label, ratio, color, info_text) in enumerate(rings):
            col = i % 2
            row = i // 2
            cx = col * w + w / 2
            cy = row * h + h / 2
            
            rect = QRectF(cx - draw_radius, cy - draw_radius, draw_radius * 2, draw_radius * 2)

            # 根据工作模式决定颜色
            if not self.working_mode:
                # 非工作模式：转换为灰度
                gray_value = int(0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue())
                color = QColor(gray_value, gray_value, gray_value)
            
            # 1. 绘制底色轨道
            bg_color = QColor(color)
            if not self.working_mode:
                bg_color.setAlpha(15)  # 非工作模式更淡
            else:
                bg_color.setAlpha(30)
            pen = QPen(bg_color, thickness)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawEllipse(rect)

            # 2. 绘制进度圆环
            pen = QPen(color, thickness)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            span_angle = -int(ratio * 360 * 16)
            painter.drawArc(rect, 90 * 16, span_angle)

            # 3. 绘制中心准确信息 (替换了百分比)
            self.draw_center_info(painter, cx, cy, draw_radius, label, info_text)

    def draw_center_info(self, painter, cx, cy, radius, label, info_text):
        # 缩小字体设定
        # info_size 对应中间的准确日期/时间
        # label_size 对应下方的分类标签
        info_size = int(radius * 0.22) 
        label_size = int(radius * 0.14)
        
        # 绘制主信息 (如 "Oct 26" 或 "14:30")
        font = QFont("Segoe UI", info_size, QFont.Weight.DemiBold)
        painter.setFont(font)
        
        # 根据工作模式决定文本颜色
        if self.working_mode:
            painter.setPen(QColor(40, 40, 40))
        else:
            painter.setPen(QColor(120, 120, 120))  # 非工作模式更灰暗
        
        # 稍微上移一点点，为下方的标签留出空间
        painter.drawText(QRectF(cx - radius, cy - radius * 0.3, radius * 2, radius * 0.4), 
                         Qt.AlignmentFlag.AlignCenter, info_text)
        
        # 绘制分类标签 (如 "MONTH")
        font.setPointSize(label_size)
        font.setBold(False)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2) # 增加字母间距提升质感
        painter.setFont(font)
        
        # 分类标签也根据工作模式变化
        if self.working_mode:
            painter.setPen(QColor(150, 150, 150))
        else:
            painter.setPen(QColor(180, 180, 180))  # 非工作模式稍微亮一些，便于阅读
            
        painter.drawText(QRectF(cx - radius, cy + radius * 0.1, radius * 2, radius * 0.3), 
                         Qt.AlignmentFlag.AlignCenter, label)


class FloatingTimeRings(QWidget):
    """悬浮时间圆环组件，显示在桌面顶层但不遮挡其他应用"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.BypassWindowManagerHint |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setFixedSize(600, 600)

        # 创建时间圆环组件
        self.ring_widget = TimeRingWidget(self)
        self.ring_widget.setGeometry(0, 0, 450, 450)

        # 添加透明拖拽区域（顶部一小条区域用于拖动窗口）
        self.drag_bar = QLabel(self)
        self.drag_bar.setGeometry(0, 0, 450, 200)  # 顶部30px区域用于拖动
        self.drag_bar.setStyleSheet("background-color: rgba(0, 0, 0, 0.01); border-radius: 15px;")
        self.drag_bar.setVisible(True)

        # 拖拽相关变量
        self.old_pos = None

        # 设置初始位置到屏幕右上角
        self.move_to_corner()

    def move_to_corner(self):
        """移动到屏幕右上角"""
        screen_geo = self.screen().availableGeometry()
        self.move(screen_geo.right() - self.width() - 20, screen_geo.top() + 20)

    def mousePressEvent(self, event: QMouseEvent):
        """记录拖动开始位置"""
        if event.button() == Qt.MouseButton.LeftButton and self.drag_bar.geometry().contains(event.pos()):
            self.old_pos = event.globalPosition().toPoint()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        """处理窗口拖动"""
        if self.old_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint()
            delta = new_pos - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = new_pos
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """结束拖动"""
        self.old_pos = None
        event.accept()

    def enterEvent(self, event):
        """鼠标进入时稍微降低透明度使窗口更明显"""
        self.setWindowOpacity(0.75)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时恢复较低透明度"""
        self.setWindowOpacity(0.5)
        super().leaveEvent(event)

    def showEvent(self, event):
        """显示时设置透明度"""
        self.setWindowOpacity(0.5)
        super().showEvent(event)