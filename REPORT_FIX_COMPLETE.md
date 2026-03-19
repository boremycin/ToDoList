# 报告模块实时更新 - 修复完成总结

## 问题
当任务正在计时时，打开统计报告窗口无法立即看到该任务的实时统计数据，只有已完成的任务才会显示统计信息。

## 根本原因
ReportWindow 的 `_update_tasks_list()` 和 `_update_bottom_stats()` 方法只从 DataManager 读取已完成任务的统计数据，完全忽略了当前正在运行的任务的时间。

## 解决方案概述

### 核心改进

1. **ReportWindow 初始化改动**
   - 修改 `ReportWindow.__init__()` 接收 parent_window 参数
   - 修改 `MainWindow._open_report_window()` 在创建 ReportWindow 时传递 self（parent_window）
   - 现在 ReportWindow 可以访问 MainWindow 的 `current_running_task` 属性

2. **新增两个数据合并方法**
   
   **方法1: `_include_running_task_time(stats, week_start_str)`**
   - 检查是否存在正在运行的任务
   - 验证任务是否在指定周内
   - 计算任务的实时总时长：`total_elapsed + (time.time() - start_time)`
   - 将该时间合并到周统计字典中
   - 返回更新后的统计数据

   **方法2: `_include_running_task_time_for_month(stats, current_month)`**
   - 功能同上，但针对月统计
   - 验证任务是否在指定月份内

3. **现有方法改动**

   **修改 `_update_tasks_list()`**
   ```python
   weekly_stats = self.data_manager.get_weekly_stats(week_start_str)
   # 新增：添加当前正在运行任务的时间
   weekly_stats = self._include_running_task_time(weekly_stats, week_start_str)
   ```

   **修改 `_update_bottom_stats()`**
   ```python
   weekly_stats = self._include_running_task_time(weekly_stats, week_start_str)
   monthly_stats = self._include_running_task_time_for_month(monthly_stats, current_month)
   ```

### 数据流程改进

```
10ms 全局定时器 (_update_all_timers)
    ↓
    - 更新 UI 显示
    - 更新 DataManager 中的任务时间
    ↓
    - emit update_report_signal
    ↓
MainWindow._update_reports()
    ↓
ReportWindow.update_data()
    ↓
ReportWindow._update_display()
    ↓
    - _update_tasks_list()
      • 获取周统计 (已完成 + 已保存)
      • _include_running_task_time() ← ★ 新增：合并当前运行任务时间
      • 显示完整列表（已完成 + 正在计时）
    
    - _update_bottom_stats()
      • 获取周统计
      • _include_running_task_time() ← ★ 新增：合并运行任务时间
      • 获取月统计
      • _include_running_task_time_for_month() ← ★ 新增：合并运行任务时间
      • 显示完整统计（已完成 + 正在计时）
    
    - 显示直方图和其他统计
    ↓
实时显示 (包含正在计时的任务)
```

## 关键设计决策

1. **使用 parent_window 引用而不是信号**
   - 原因：需要实时访问 current_running_task 对象
   - 避免了信号的开销和延迟
   - ReportWindow 和 MainWindow 紧密协作

2. **只在显示时合并，不修改存储**
   - 保持 DataManager 数据结构不变
   - 运行任务的时间不会被持久化为"已完成"
   - 更改显示逻辑，而非底层数据

3. **防御性编程**
   - `if self.parent_window and self.parent_window.current_running_task:`
   - 处理 parent_window 为 None 的情况
   - 处理 current_running_task 为 None 的情况

4. **时间范围验证**
   - 周统计：`0 <= days_since_week_start <= 6`
   - 月统计：`year == current_month_date.year and month == current_month_date.month`
   - 只合并在时间范围内的任务

## 修改清单

### main_window.py

| 位置 | 改动 | 类型 |
|------|------|------|
| 第227-232行 | `_open_report_window()` | 修改 |
| 第691-697行 | `ReportWindow.__init__()` | 修改 |
| 第844-858行 | `_update_tasks_list()` 内容 | 修改 |
| 第869-878行 | `_update_bottom_stats()` 内容 | 修改 |
| 第883-910行 | 新增 `_include_running_task_time()` | 新增 |
| 第912-937行 | 新增 `_include_running_task_time_for_month()` | 新增 |

### 无其他文件修改

## 验证步骤

### 功能验证
1. 启动应用
2. 创建几个任务
3. 点击任何任务开始计时
4. **立即** 点击"查看报告"按钮
5. ✓ 应该看到该任务在"本周任务投入时间"列表中
6. ✓ 时间应该不断增长（实时刷新）
7. ✓ "本周总计"和"本月总计"应该包含该任务时间

### 边界情况
1. 没有正在运行的任务时，报告正常显示已完成任务
2. 多个任务在不同列表中，只显示当前列表的运行任务
3. 切换周期时，如果任务不在该周内，不应该显示

### 性能验证
1. 报告窗口打开/关闭无卡顿
2. 实时更新的频率合理（100ms）
3. CPU 使用率正常

## 代码质量

- ✓ 语法检查通过 (python -m py_compile)
- ✓ 无缺失的方法引用
- ✓ 正确的属性访问 (task.text, task.total_elapsed, task.is_running, task.start_time)
- ✓ 防御性的 None 检查
- ✓ 类型提示正确
- ✓ 注释清晰

## 后续扩展建议

1. **任务时间的持久化**
   - 当任务完成时，保存其最终时间到 DataManager.stats
   - 当任务停止但未完成时，保存中间时间

2. **历史数据追踪**
   - 记录任务在不同时间的运行时长
   - 用于时间趋势分析

3. **实时通知**
   - 当任务超过预定时间时提醒用户
   - 周期性的"辛苦了"激励信息

4. **性能优化**
   - 缓存统计计算结果
   - 仅在数据变化时更新显示
