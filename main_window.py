import os
from typing import Dict, List, Optional

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

        # 列表组件
        self.list_widget: QtWidgets.QListWidget = QtWidgets.QListWidget()
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection) # type: ignore
        self.list_widget.setFont(create_font(11))
        self.list_widget.itemSelectionChanged.connect(self.on_list_changed)
        left_layout.addWidget(self.list_widget)

        # "我的任务"组 - 包含操作按钮
        my_tasks_group = QtWidgets.QGroupBox("我的任务")
        my_tasks_layout = QtWidgets.QHBoxLayout(my_tasks_group)  # 使用水平布局
        
        # 按钮组 - 使用更小的按钮
        for label, callback, width in [
            ("+", self.add_list, 30),
            ("R", self.rename_list, 30),
            ("×", self.delete_list, 30),
        ]:
            btn = QtWidgets.QPushButton(label)
            btn.setFont(create_font(10))
            if width:
                btn.setFixedWidth(width)
            btn.clicked.connect(callback)
            my_tasks_layout.addWidget(btn)
        
        left_layout.addWidget(my_tasks_group)

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
            self.report_window.update_data()

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
    """报告窗口"""
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.setWindowTitle("任务统计报告")
        self.resize(400, 500)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # 日统计
        daily_title = QtWidgets.QLabel("📅 今日统计")
        daily_title.setFont(create_font(12, bold=True))
        layout.addWidget(daily_title)
        
        self.daily_report = QtWidgets.QLabel()
        self.daily_report.setFont(create_font(10))
        self.daily_report.setStyleSheet("color: #666666;")
        self.daily_report.setWordWrap(True)
        layout.addWidget(self.daily_report)
        
        layout.addWidget(QtWidgets.QLabel(""))  # 空白间隔
        
        # 周统计
        weekly_title = QtWidgets.QLabel("🗓️ 本周统计")
        weekly_title.setFont(create_font(12, bold=True))
        layout.addWidget(weekly_title)
        
        self.weekly_report = QtWidgets.QLabel()
        self.weekly_report.setFont(create_font(10))
        self.weekly_report.setStyleSheet("color: #666666;")
        self.weekly_report.setWordWrap(True)
        layout.addWidget(self.weekly_report)
        
        layout.addWidget(QtWidgets.QLabel(""))  # 空白间隔
        
        # 月统计
        monthly_title = QtWidgets.QLabel("📆 本月统计")
        monthly_title.setFont(create_font(12, bold=True))
        layout.addWidget(monthly_title)
        
        self.monthly_report = QtWidgets.QLabel()
        self.monthly_report.setFont(create_font(10))
        self.monthly_report.setStyleSheet("color: #666666;")
        self.monthly_report.setWordWrap(True)
        layout.addWidget(self.monthly_report)
        
        # 更新数据
        self.update_data()
    
    def update_data(self):
        """更新报告数据"""
        # 日统计
        daily_stats = self.data_manager.get_daily_stats()
        total_daily = sum(daily_stats.values())
        daily_text = f"总计: {self._format_duration(total_daily)}\n"
        if len(daily_stats) > 0:
            top_task = max(daily_stats, key=daily_stats.get)
            daily_text += f"最耗时: {top_task} ({self._format_duration(daily_stats[top_task])})"
        self.daily_report.setText(daily_text)

        # 周统计
        weekly_stats = self.data_manager.get_weekly_stats()
        total_weekly = sum(weekly_stats.values())
        weekly_text = f"总计: {self._format_duration(total_weekly)}\n"
        if len(weekly_stats) > 0:
            top_task = max(weekly_stats, key=weekly_stats.get)
            weekly_text += f"最耗时: {top_task} ({self._format_duration(weekly_stats[top_task])})"
        self.weekly_report.setText(weekly_text)

        # 月统计
        monthly_stats = self.data_manager.get_monthly_stats()
        total_monthly = sum(monthly_stats.values())
        monthly_text = f"总计: {self._format_duration(total_monthly)}\n"
        if len(monthly_stats) > 0:
            top_task = max(monthly_stats, key=monthly_stats.get)
            monthly_text += f"最耗时: {top_task} ({self._format_duration(monthly_stats[top_task])})"
        self.monthly_report.setText(monthly_text)
    
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