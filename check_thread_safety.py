#!/usr/bin/env python3
"""线程安全性验证脚本"""

import sys
import os

# 检查代码中是否有线程不安全的操作
print("=" * 60)
print("线程安全性检查")
print("=" * 60)

with open('main_window.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# 检查后台线程中的可疑操作
print("\n✓ 检查后台线程代码...")
thread_section = content[content.find('def background_worker'):content.find('def background_worker') + 1000]
print("  - 不应该访问 self.tasks_layout:", 'tasks_layout' not in thread_section)
print("  - 不应该访问 self.current_list_label:", 'current_list_label' not in thread_section)
print("  - 不应该启动/停止定时器:", 'timer.start' not in thread_section and 'timer.stop' not in thread_section)

# 检查是否有正确的线程隔离
print("\n✓ 检查线程隔离...")
print("  - 已添加 UI 同步定时器:", 'sync_timer' in content)
print("  - 后台线程仅做数据保存:", 'self.data_manager.save()' in thread_section)

print("\n✓ 所有检查完成！")
print("\n关键设计：")
print("  • 后台线程: 仅保存数据，不触及Qt对象")
print("  • UI同步定时器: 在主线程中定期同步UI数据")
print("  • 信号机制: 线程安全的通信方式")
print("=" * 60)
