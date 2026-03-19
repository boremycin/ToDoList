# 报告模块数据实时刷新修复

## 问题
任务计时后无法快速反馈到任务统计报告模块中，打开报告后没有统计信息，特别是对于正在计时的任务。

## 根本原因
报告模块之前只从 `DataManager.stats` 中读取已完成任务的统计数据，但不包括当前正在运行的任务的时间。

## 解决方案

### 1. 核心修改（main_window.py）

#### 修改 `_update_tasks_list()` 方法（ReportWindow 内）
- **位置**: 第834-860行
- **改进**: 在获取周统计数据后，调用 `_include_running_task_time()` 来合并当前运行任务的时间

```python
weekly_stats = self.data_manager.get_weekly_stats(week_start_str)
# 添加当前正在运行任务的时间
weekly_stats = self._include_running_task_time(weekly_stats, week_start_str)
```

#### 修改 `_update_bottom_stats()` 方法（ReportWindow 内）
- **位置**: 第864-879行
- **改进**: 在获取周、月统计数据后，调用新的辅助方法来合并运行任务时间

```python
weekly_stats = self._include_running_task_time(weekly_stats, week_start_str)
monthly_stats = self._include_running_task_time_for_month(monthly_stats, current_month)
```

#### 新增 `_include_running_task_time()` 方法
- **签名**: `def _include_running_task_time(self, stats: dict, week_start_str: str) -> dict:`
- **功能**: 
  - 检查是否有当前运行的任务
  - 验证任务是否在指定周内
  - 计算任务的实时总时长（已累积 + 当前运行时间）
  - 将任务时间合并到统计字典中
  - 返回更新后的统计数据

#### 新增 `_include_running_task_time_for_month()` 方法
- **签名**: `def _include_running_task_time_for_month(self, stats: dict, current_month: str) -> dict:`
- **功能**: 
  - 类似于周统计方法
  - 验证任务是否在指定月份内
  - 合并月统计数据中的运行任务时间

### 2. 数据流程

```
100ms 全局定时器触发
    ↓
MainWindow._update_all_timers()
    ↓
    - 更新当前运行任务的显示
    - 更新 DataManager 中的任务时间
    - emit update_report_signal
    ↓
MainWindow._update_reports()
    ↓
ReportWindow.update_data()
    ↓
ReportWindow._update_display()
    ↓
    - ReportWindow._update_tasks_list()
      → 调用 _include_running_task_time() 合并运行时间
    - ReportWindow._update_bottom_stats()
      → 调用 _include_running_task_time_for_month() 合并运行时间
    ↓
显示最新统计数据（包含正在计时的任务）
```

### 3. 时间计算逻辑

对于正在运行的任务，实时总时长计算如下：

```python
current_total = task.total_elapsed  # 已累积时长（秒）

# 如果任务还在运行，加上当前经过的时间
if task.is_running and task.start_time is not None:
    current_total += time.time() - task.start_time
```

## 关键改进

1. **实时性**: 报告窗口每100ms自动刷新数据，显示最新的任务计时信息
2. **准确性**: 包含了当前正在运行的任务的时间，避免了之前的时间遗漏
3. **隔离性**: 只合并在指定时间范围内的运行任务数据
4. **非侵入性**: 不修改原有的 DataManager 数据结构，只在报告显示时动态合并

## 验证步骤

1. 启动应用
2. 点击任务开始计时
3. 立即打开报告窗口
4. 验证该任务出现在列表中，并显示实时计时时间
5. 继续计时，观察报告中的时间持续增加
6. 完成任务后，再次检查统计信息

## 相关文件修改

- `main_window.py`: 新增两个方法，修改两个既有方法
