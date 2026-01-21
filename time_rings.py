from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, QRectF, Qt
from PySide6.QtGui import QPainter, QPen, QColor, QFont
import datetime
import calendar

class TimeRingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(350, 350) 

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50) 

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

            # 1. 绘制底色轨道
            bg_color = QColor(color)
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
        painter.setPen(QColor(40, 40, 40))
        # 稍微上移一点点，为下方的标签留出空间
        painter.drawText(QRectF(cx - radius, cy - radius * 0.3, radius * 2, radius * 0.4), 
                         Qt.AlignmentFlag.AlignCenter, info_text)
        
        # 绘制分类标签 (如 "MONTH")
        font.setPointSize(label_size)
        font.setBold(False)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2) # 增加字母间距提升质感
        painter.setFont(font)
        painter.setPen(QColor(150, 150, 150))
        painter.drawText(QRectF(cx - radius, cy + radius * 0.1, radius * 2, radius * 0.3), 
                         Qt.AlignmentFlag.AlignCenter, label)