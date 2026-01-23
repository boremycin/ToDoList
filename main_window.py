import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from PySide6 import QtCore, QtGui, QtWidgets

from data_manager import DataManager
from system_tray import SystemTray
from utils import create_notebook_icon, create_font
from widgets import TaskWidget
from time_rings import TimeRingWidget


class MainWindow(QtWidgets.QMainWindow):
    """应用主窗口"""

    def __init__(self, data_file: str):
        super().__init__()
        self.setWindowTitle("ToDo — 任务清单 (Windows)")
        self.resize(900, 600)
        self.setWindowIcon(create_notebook_icon())

        # 数据管理
        self.data_manager = DataManager(data_file)
        self.data_manager.load()
        if not self.data_manager.data:
            self.data_manager.data = {"我的任务": []}

        # 当前正在计时的任务
        self.active_task_widget = None

        # 延迟保存定时器
        self.save_timer = QtCore.QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._save_data_immediate)
        self.pending_save = False

        # 系统托盘
        self.system_tray = SystemTray(self)

        # 报告窗口
        self.report_window = None

        # 构建 UI
        self._setup_ui()
        self._populate_lists()

    def _create_right_panel_no_header(self) -> QtWidgets.QWidget:
        """创建右侧面板（任务管理）- 不含顶部标题栏"""
        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        # 任务输入框
        add_layout = QtWidgets.QHBoxLayout()
        self.input_task = QtWidgets.QLineEdit()
        self.input_task.setPlaceholderText("添加新任务，按回车确认")
        self.input_task.setFont(create_font(12))
        self.input_task.returnPressed.connect(self.add_task_from_input)
        add_layout.addWidget(self.input_task)

        btn_add_task = QtWidgets.QPushButton("添加")
        btn_add_task.setFont(create_font(12))
        btn_add_task.clicked.connect(self.add_task_from_input)
        add_layout.addWidget(btn_add_task)
        right_layout.addLayout(add_layout)

        # 任务滚动区域
        self.scroll: QtWidgets.QScrollArea = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.tasks_container: QtWidgets.QWidget = QtWidgets.QWidget()
        self.tasks_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(6, 6, 6, 6)
        self.tasks_layout.setSpacing(6)
        self.tasks_layout.addStretch()
        
        # 设置滚动区域的组件
        self.scroll.setWidget(self.tasks_container)
        right_layout.addWidget(self.scroll)

        # 添加当前列表标签，放置在输入框上方
        self.current_list_label = QtWidgets.QLabel("")
        self.current_list_label.setFont(create_font(18, bold=True))
        self.current_list_label.setStyleSheet("color: #333333;")
        right_layout.insertWidget(0, self.current_list_label)
        return right

    def _setup_ui(self):
        """构建用户界面"""
        # 创建主布局容器
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 添加时间圆环组件 - 放在最顶部
        self.time_ring_widget = TimeRingWidget()
        # 添加点击事件以切换工作/休息状态
        self.time_ring_widget.mousePressEvent = self._toggle_working_mode
        self.time_ring_widget.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        main_layout.addWidget(self.time_ring_widget)

        # 创建分割器用于左右面板
        splitter = QtWidgets.QSplitter()
        splitter.setHandleWidth(2)

        # 左侧：列表管理
        left = self._create_left_panel()
        splitter.addWidget(left)
        left.setMaximumWidth(280)

        # 右侧：任务管理（移除原有的标题栏，因为现在有时间圆环了）
        right = self._create_right_panel_no_header()
        splitter.addWidget(right)

        main_layout.addWidget(splitter)

        self.setCentralWidget(main_widget)

        # 状态栏
        self.status: QtWidgets.QStatusBar = self.statusBar()
        self.status.setFont(create_font(10))
        
        # 初始化工作状态
        self.working_mode = True
        self._update_working_visuals()

    def _toggle_working_mode(self, event):
        """切换工作/休息模式"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.working_mode = not self.working_mode
            self.time_ring_widget.set_working_mode(self.working_mode)
            self._update_working_visuals()
            if self.working_mode:
                self.status.showMessage("进入工作模式", 2000)
            else:
                self.status.showMessage("退出工作模式", 2000)

    def _update_working_visuals(self):
        """更新工作模式下的视觉效果"""
        if self.working_mode:
            # 工作模式：圆环更鲜艳，背景稍暗
            self.time_ring_widget.setStyleSheet("")
        else:
            # 休息模式：圆环变灰
            self.time_ring_widget.setStyleSheet("")

    def _create_left_panel(self) -> QtWidgets.QWidget:
        """创建左侧面板（列表管理）"""
        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        # 标题
        lbl_lists = QtWidgets.QLabel("任务列表")
        lbl_lists.setFont(create_font(16, bold=True))
        lbl_lists.setStyleSheet("color: #333333;")
        left_layout.addWidget(lbl_lists)

        # 操作按钮布局 - 在标题下方
        button_layout = QtWidgets.QHBoxLayout()
        btn_add_list = QtWidgets.QPushButton("+")
        btn_add_list.setFixedWidth(30)
        btn_add_list.setFont(create_font(10))
        btn_add_list.clicked.connect(self.add_list)
        button_layout.addWidget(btn_add_list)

        btn_rename_list = QtWidgets.QPushButton("R")
        btn_rename_list.setFixedWidth(30)
        btn_rename_list.setFont(create_font(10))
        btn_rename_list.clicked.connect(self.rename_list)
        button_layout.addWidget(btn_rename_list)

        btn_delete_list = QtWidgets.QPushButton("×")
        btn_delete_list.setFixedWidth(30)
        btn_delete_list.setFont(create_font(10))
        btn_delete_list.clicked.connect(self.delete_list)
        button_layout.addWidget(btn_delete_list)

        # 将按钮布局添加到标题下方
        left_layout.addLayout(button_layout)

        # 列表组件
        self.list_widget: QtWidgets.QListWidget = QtWidgets.QListWidget()
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection) # type: ignore
        self.list_widget.setFont(create_font(11))
        self.list_widget.itemSelectionChanged.connect(self.on_list_changed)
        left_layout.addWidget(self.list_widget)

        # 报告按钮
        self.report_btn = QtWidgets.QPushButton("📊 报告")
        self.report_btn.setFont(create_font(11))
        self.report_btn.clicked.connect(self._open_report_window)
        left_layout.addWidget(self.report_btn)

        return left

    def _open_report_window(self):
        """打开报告窗口"""
        if self.report_window is None or not self.report_window.isVisible():
            self.report_window = ReportWindow(self.data_manager)
            self.report_window.show()
        else:
            self.report_window.activateWindow()

    def _update_reports(self):
        """更新统计报告"""
        if self.report_window and self.report_window.isVisible():
            self.report_window.update_data() # type: ignore

    def _format_duration(self, seconds):
        """格式化时长显示"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    # ========== 数据管理
    def _save_data_immediate(self):
        """立即保存数据"""
        if self.data_manager.save():
            self.status.showMessage("已保存", 1000)
        else:
            self.status.showMessage("保存失败", 3000)
        self.pending_save = False

    def save_data(self):
        """触发延迟保存"""
        self.pending_save = True
        self.save_timer.start(500)

    def quit_application(self):
        """退出应用，确保数据被保存"""
        # 停止所有正在运行的任务
        if self.active_task_widget:
            self.active_task_widget.stop_timer()
        
        if self.pending_save:
            self.save_timer.stop()
            self._save_data_immediate()
        QtWidgets.QApplication.quit()

    def closeEvent(self, event: QtGui.QCloseEvent):
        """窗口关闭事件 - 隐藏到托盘并显示悬浮圆环"""
        # 停止所有正在运行的任务
        if self.active_task_widget:
            self.active_task_widget.stop_timer()
        
        if self.pending_save:
            self.save_timer.stop()
            self._save_data_immediate()
        
        event.ignore()
        self.hide()
        
        # 显示悬浮圆环
        self.system_tray._hide_window()
        
        self.system_tray.show_message(
            "ToDo 任务清单",
            "程序已最小化到系统托盘，时间圆环已悬浮显示"
        )

    # ========== 列表管理
    def _populate_lists(self):
        """填充列表组件"""
        self.list_widget.clear()
        for name in self.data_manager.data.keys():
            item = QtWidgets.QListWidgetItem(name)
            self.list_widget.addItem(item)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def on_list_changed(self):
        """列表选择变化处理"""
        items = self.list_widget.selectedItems()
        if not items:
            self.current_list_label.setText("")
            self._clear_tasks()
            return
        name = items[0].text()
        self.current_list_label.setText(name)
        self._load_tasks(name)

    def add_list(self):
        """添加新列表"""
        name, ok = QtWidgets.QInputDialog.getText(self, "新建列表", "列表名称:")
        if ok and name:
            if name in self.data_manager.data:
                QtWidgets.QMessageBox.warning(self, "已存在", "已存在同名列表。")
                return
            self.data_manager.data[name] = []
            self._populate_lists()
            items = self.list_widget.findItems(name, QtCore.Qt.MatchExactly) # type: ignore
            if items:
                self.list_widget.setCurrentItem(items[0])
            self.save_data()

    def rename_list(self):
        """重命名列表"""
        items = self.list_widget.selectedItems()
        if not items:
            return
        old = items[0].text()
        new, ok = QtWidgets.QInputDialog.getText(
            self, "重命名列表", "新名称:", text=old
        )
        if ok and new and new != old:
            if new in self.data_manager.data:
                QtWidgets.QMessageBox.warning(self, "已存在", "已存在同名列表。")
                return
            self.data_manager.data[new] = self.data_manager.data.pop(old)
            self._populate_lists()
            items = self.list_widget.findItems(new, QtCore.Qt.MatchExactly) # type: ignore
            if items:
                self.list_widget.setCurrentItem(items[0])
            self.save_data()

    def delete_list(self):
        """删除列表"""
        items = self.list_widget.selectedItems()
        if not items:
            return
        name = items[0].text()
        ans = QtWidgets.QMessageBox.question(
            self, "删除列表", f"确定要删除列表 '{name}' 吗？此操作不可撤销。"
        )
        if ans == QtWidgets.QMessageBox.StandardButton.Yes:
            self.data_manager.data.pop(name, None)
            self._populate_lists()
            self.save_data()

    # ========== 任务管理
    def _clear_tasks(self):
        """清空任务显示"""
        # 停止所有正在运行的任务
        for i in range(self.tasks_layout.count() - 1):
            item = self.tasks_layout.itemAt(i)
            w = item.widget()
            if isinstance(w, TaskWidget) and w.is_running:
                w.stop_timer()
        
        while self.tasks_layout.count() > 1:
            item = self.tasks_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

    def _load_tasks(self, list_name: str):
        """加载指定列表的任务"""
        self._clear_tasks()
        tasks = self.data_manager.data.get(list_name, [])
        for t in tasks:
            widget = TaskWidget(t.get("text", ""), checked=bool(t.get("checked", False)))
            # 加载任务的累计时间
            widget.load_from_dict(t)
            widget.changed.connect(self.on_task_changed)
            widget.removed.connect(self.on_task_removed)
            # 连接计时相关信号
            widget.changed.connect(self._update_reports)
            self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, widget)

    def add_task_from_input(self):
        """从输入框添加任务"""
        txt = self.input_task.text().strip()
        if not txt:
            return
        items = self.list_widget.selectedItems()
        if not items:
            QtWidgets.QMessageBox.warning(self, "未选择列表", "请先选择一个列表。")
            return
        list_name = items[0].text()
        widget = TaskWidget(txt)
        widget.changed.connect(self.on_task_changed)
        widget.removed.connect(self.on_task_removed)
        # 连接计时相关信号
        widget.changed.connect(self._update_reports)
        self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, widget)
        self.data_manager.data[list_name].append(widget.to_dict())
        self.input_task.clear()
        self.save_data()

    def on_task_changed(self):
        """任务状态变化处理"""
        items = self.list_widget.selectedItems()
        if not items:
            return
        name = items[0].text()
        arr = []
        for i in range(self.tasks_layout.count() - 1):
            w = self.tasks_layout.itemAt(i).widget()
            if isinstance(w, TaskWidget):
                # 如果任务完成且正在计时，则停止计时并记录
                if w.toggle.isChecked() and w.is_running:
                    w.stop_timer()
                    # 记录任务完成数据
                    duration = w.total_elapsed
                    if duration > 0:  # 只记录有时间投入的任务
                        self.data_manager.record_task_completion(w.text, duration)
                        self._update_reports()
                
                arr.append(w.to_dict())
        self.data_manager.data[name] = arr
        self.save_data()  # 确保实时保存

    def on_task_removed(self, widget: TaskWidget):
        """任务删除处理"""
        # 停止计时
        if widget.is_running:
            widget.stop_timer()
        
        items = self.list_widget.selectedItems()
        if not items:
            return
        name = items[0].text()
        for i in range(self.tasks_layout.count()):
            it = self.tasks_layout.itemAt(i)
            if it and it.widget() is widget:
                w = it.widget()
                w.setParent(None)
                break
        self.on_task_changed()


class ReportWindow(QtWidgets.QWidget):
    """报告窗口 - 包含周度直方图和任务时间统计"""
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.setWindowTitle("任务统计报告")
        self.resize(800, 600)
        self.setWindowIcon(create_notebook_icon())
        
        # 当前选中的周
        self.current_start_date = self._get_monday_for_current_week()
        self.animation = None  # 存储过渡动画

        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 顶部日期选择控件
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # 左箭头按钮 - 选择上周
        self.btn_prev_week = QtWidgets.QPushButton("◀")
        self.btn_prev_week.setFixedSize(40, 40)
        self.btn_prev_week.setFont(create_font(12, bold=True))
        self.btn_prev_week.clicked.connect(self._prev_week)
        header_layout.addWidget(self.btn_prev_week)

        # 周期显示标签
        self.lbl_week_range = QtWidgets.QLabel()
        self.lbl_week_range.setFont(create_font(12, bold=True))
        self.lbl_week_range.setStyleSheet("color: #333333; padding: 5px 15px;")
        header_layout.addWidget(self.lbl_week_range)

        # 右箭头按钮 - 选择下周
        self.btn_next_week = QtWidgets.QPushButton("▶")
        self.btn_next_week.setFixedSize(40, 40)
        self.btn_next_week.setFont(create_font(12, bold=True))
        self.btn_next_week.clicked.connect(self._next_week)
        header_layout.addWidget(self.btn_next_week)

        main_layout.addLayout(header_layout)

        # 直方图区域
        self.histogram_widget = HistogramWidget(self.current_start_date, self.data_manager)
        main_layout.addWidget(self.histogram_widget)

        # 本周任务列表标题
        weekly_tasks_title = QtWidgets.QLabel("本周任务投入时间")
        weekly_tasks_title.setFont(create_font(12, bold=True))
        weekly_tasks_title.setStyleSheet("padding-top: 10px;")
        main_layout.addWidget(weekly_tasks_title)

        # 本周任务列表滚动区域
        self.tasks_scroll_area = QtWidgets.QScrollArea()
        self.tasks_scroll_area.setWidgetResizable(True)
        self.tasks_container = QtWidgets.QWidget()
        self.tasks_layout = QtWidgets.QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(8)
        self.tasks_scroll_area.setWidget(self.tasks_container)
        self.tasks_scroll_area.setMaximumHeight(200)
        main_layout.addWidget(self.tasks_scroll_area)

        # 底部统计信息
        bottom_layout = QtWidgets.QHBoxLayout()
        self.lbl_week_total = QtWidgets.QLabel("本周总计: 0小时 0分钟")
        self.lbl_week_total.setFont(create_font(10, bold=True))
        self.lbl_week_total.setStyleSheet("color: #333333;")
        bottom_layout.addWidget(self.lbl_week_total)

        self.lbl_month_total = QtWidgets.QLabel("本月总计: 0小时 0分钟")
        self.lbl_month_total.setFont(create_font(10, bold=True))
        self.lbl_month_total.setStyleSheet("color: #333333;")
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.lbl_month_total)

        main_layout.addLayout(bottom_layout)

        # 更新数据显示
        self._update_display()

    def _get_monday_for_current_week(self):
        """获取当前周的周一日期"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        return monday.date()

    def _prev_week(self):
        """切换到上一周"""
        self._animate_transition(direction='right')
        self.current_start_date -= timedelta(days=7)
        self._update_display()

    def _next_week(self):
        """切换到下一周"""
        self._animate_transition(direction='left')
        self.current_start_date += timedelta(days=7)
        self._update_display()

    def _animate_transition(self, direction='left'):
        """执行横向过渡动画"""
        # 创建淡入淡出动画
        opacity_effect = QtWidgets.QGraphicsOpacityEffect()
        self.histogram_widget.setGraphicsEffect(opacity_effect)
        
        anim = QtCore.QPropertyAnimation(opacity_effect, b"opacity")
        anim.setDuration(200)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.start(QtCore.QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        
        # 动画完成后恢复不透明度
        QtCore.QTimer.singleShot(200, lambda: self._restore_opacity(opacity_effect))

    def _restore_opacity(self, effect):
        """恢复直方图的不透明度"""
        anim = QtCore.QPropertyAnimation(effect, b"opacity")
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start(QtCore.QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _update_display(self):
        """更新显示内容"""
        # 更新周期标签
        end_date = self.current_start_date + timedelta(days=6)
        self.lbl_week_range.setText(f"{self.current_start_date.strftime('%m月%d日')} - {end_date.strftime('%m月%d日')}")

        # 更新直方图
        self.histogram_widget.update_data(self.current_start_date)

        # 更新任务列表
        self._update_tasks_list()

        # 更新底部统计
        self._update_bottom_stats()

    def _update_tasks_list(self):
        """更新本周任务列表"""
        # 清空现有内容
        for i in reversed(range(self.tasks_layout.count())):
            widget = self.tasks_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # 获取本周统计数据
        week_start_str = self.current_start_date.strftime("%Y-%m-%d")
        weekly_stats = self.data_manager.get_weekly_stats(week_start_str)

        # 按时间排序添加任务
        sorted_tasks = sorted(weekly_stats.items(), key=lambda x: x[1], reverse=True)

        for task_name, duration in sorted_tasks:
            task_row = QtWidgets.QHBoxLayout()
            lbl_task_name = QtWidgets.QLabel(task_name)
            lbl_task_name.setFont(create_font(10))
            lbl_task_duration = QtWidgets.QLabel(self._format_duration(duration))
            lbl_task_duration.setFont(create_font(10))
            lbl_task_duration.setStyleSheet("color: #666666;")
            task_row.addWidget(lbl_task_name)
            task_row.addStretch()
            task_row.addWidget(lbl_task_duration)
            self.tasks_layout.addLayout(task_row)

    def _update_bottom_stats(self):
        """更新底部统计信息"""
        # 本周统计
        week_start_str = self.current_start_date.strftime("%Y-%m-%d")
        weekly_stats = self.data_manager.get_weekly_stats(week_start_str)
        total_week_seconds = sum(weekly_stats.values())
        self.lbl_week_total.setText(f"本周总计: {self._format_duration(total_week_seconds)}")

        # 本月统计
        current_month = datetime.now().strftime("%Y-%m")
        monthly_stats = self.data_manager.get_monthly_stats(current_month)
        total_month_seconds = sum(monthly_stats.values())
        self.lbl_month_total.setText(f"本月总计: {self._format_duration(total_month_seconds)}")

    def _format_duration(self, seconds):
        """格式化时长显示"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if hours > 0:
            return f"{hours}小时 {minutes}分钟"
        elif minutes > 0:
            return f"{minutes}分钟"
        else:
            return f"{int(seconds)}秒"


class HistogramWidget(QtWidgets.QWidget):
    """周度时间直方图组件"""
    def __init__(self, start_date, data_manager):
        super().__init__()
        self.start_date = start_date
        self.data_manager = data_manager
        self.setMinimumHeight(250)
        self.days_data = [0] * 7  # 存储每天的时间数据
        self.day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

    def update_data(self, start_date):
        """更新直方图数据"""
        self.start_date = start_date
        for i in range(7):
            day_date = start_date + timedelta(days=i)
            day_str = day_date.strftime("%Y-%m-%d")
            daily_stats = self.data_manager.get_daily_stats(day_str)
            self.days_data[i] = sum(daily_stats.values())  # 总秒数
        self.update()  # 触发重绘

    def paintEvent(self, event):
        """绘制直方图"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        margin = 50  # 左右边距
        top_margin = 20  # 顶边距
        bottom_margin = 40  # 底边距

        # 计算柱状图区域
        chart_width = width - 2 * margin
        chart_height = height - top_margin - bottom_margin

        # 找到最大值以确定比例
        max_value = max(self.days_data) if self.days_data else 1
        if max_value == 0:
            max_value = 1  # 防止除零错误

        # 计算柱子的宽度和间距
        bar_count = 7
        spacing = chart_width // 20  # 间距
        bar_width = (chart_width - (bar_count + 1) * spacing) // bar_count

        # 绘制网格线和数值标签
        # 水平网格线
        for i in range(0, 6):  # 画5条水平线
            y_pos = top_margin + int(chart_height * i / 5)
            painter.setPen(QtGui.QPen(QtGui.QColor(230, 230, 230), 1))
            painter.drawLine(margin, y_pos, width - margin, y_pos)

        # 绘制柱子和标签
        for i in range(bar_count):
            # 计算柱子位置和高度
            x_pos = margin + i * (bar_width + spacing) + spacing
            value = self.days_data[i]
            bar_height = int((value / max_value) * chart_height) if max_value > 0 else 0
            y_pos = top_margin + chart_height - bar_height  # 从底部开始绘制

            # 选择颜色 - 根据数值大小调整深浅
            color_intensity = 50 + int(205 * (value / max_value)) if max_value > 0 else 50
            bar_color = QtGui.QColor(40, 120, 220)
            painter.setBrush(QtGui.QBrush(bar_color))
            painter.setPen(QtGui.QPen(bar_color.darker(150), 1))

            # 绘制柱子
            painter.drawRect(x_pos, y_pos, bar_width, bar_height)

            # 绘制数值标签
            painter.setPen(QtGui.QPen(QtGui.QColor(100, 100, 100), 1))
            text_rect = QtCore.QRect(x_pos, y_pos - 20, bar_width, 20)
            painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter, self._format_duration(value))

            # 绘制星期标签
            day_label_rect = QtCore.QRect(x_pos, height - bottom_margin + 5, bar_width, 20)
            painter.setPen(QtGui.QPen(QtGui.QColor(50, 50, 50), 1))
            painter.drawText(day_label_rect, QtCore.Qt.AlignmentFlag.AlignCenter, self.day_names[i])

        # 绘制Y轴标签
        for i in range(0, 6):  # 画6个刻度标签
            y_pos = top_margin + chart_height - int(chart_height * i / 5)
            value = int(max_value * i / 5)
            text = self._format_duration(value)
            painter.setPen(QtGui.QPen(QtGui.QColor(100, 100, 100), 1))
            text_rect = QtCore.QRect(5, y_pos - 10, margin - 10, 20)
            painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter, text)

    def mousePressEvent(self, event):
        """处理鼠标点击事件，显示当天总时长"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            width = self.width()
            margin = 50
            chart_width = width - 2 * margin
            spacing = chart_width // 20
            bar_width = (chart_width - 7 * spacing) // 7

            # 计算点击的是哪一天
            click_x = event.pos().x()
            for i in range(7):
                x_pos = margin + i * (bar_width + spacing) + spacing
                if x_pos <= click_x <= x_pos + bar_width:
                    # 弹出提示框显示当天总时长
                    day_date = self.start_date + timedelta(days=i)
                    day_str = day_date.strftime("%m月%d日")
                    duration_str = self._format_duration(self.days_data[i])
                    msg_box = QtWidgets.QMessageBox()
                    msg_box.setWindowTitle("当日总时长")
                    msg_box.setText(f"{day_str}\n\n总时长: {duration_str}")
                    msg_box.exec()
                    break

    def _format_duration(self, seconds):
        """格式化时长显示"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{int(seconds)}s"
