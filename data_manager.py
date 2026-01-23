"""数据持久化模块 - 处理 JSON 数据的读写"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List


class DataManager:
    """数据管理类"""
    
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.data: Dict[str, List[Dict]] = {}
        self.stats: Dict[str, List[Dict]] = {}  # 统计数据
        self.load()
    
    def load(self):
        """加载数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                
                # 兼容性处理：如果数据格式较老
                if isinstance(loaded_data, list):
                    # 老格式：直接是任务列表
                    self.data = {"我的任务": loaded_data}
                else:
                    # 新格式：包含任务列表和统计数据
                    self.data = loaded_data.get("tasks", {})
                    self.stats = loaded_data.get("stats", {})
                    
                # 确保至少有一个默认列表
                if not self.data:
                    self.data = {"我的任务": []}
            except Exception as e:
                print(f"加载数据失败: {e}")
                self.data = {"我的任务": []}
        else:
            self.data = {"我的任务": []}
    
    def save(self) -> bool:
        """保存数据"""
        try:
            # 准备保存的数据
            save_data = {
                "tasks": self.data,
                "stats": self.stats
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存数据失败: {e}")
            return False
    
    def record_task_completion(self, task_text: str, duration: float, date: str = None): # type: ignore
        """记录任务完成数据"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if date not in self.stats:
            self.stats[date] = []
        
        self.stats[date].append({
            "task": task_text,
            "duration": duration,  # 以秒为单位
            "timestamp": datetime.now().isoformat()
        })
    
    def get_daily_stats(self, date: str = None) -> Dict[str, float]: # type: ignore
        """获取某天的统计数据"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        stats = {}
        if date in self.stats:
            for entry in self.stats[date]:
                task = entry["task"]
                duration = entry["duration"]
                if task in stats:
                    stats[task] += duration
                else:
                    stats[task] = duration
        return stats
    
    def get_weekly_stats(self, start_date: str = None) -> Dict[str, float]: # type: ignore
        """获取周统计数据"""
        if start_date is None:
            # 获取本周周一的日期
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            start_date = start_of_week.strftime("%Y-%m-%d")
        else:
            start_of_week = datetime.strptime(start_date, "%Y-%m-%d")
            # 确保是周一
            start_of_week = start_of_week - timedelta(days=start_of_week.weekday())
        
        stats = {}
        for i in range(7):
            date = (start_of_week + timedelta(days=i)).strftime("%Y-%m-%d")
            daily_stats = self.get_daily_stats(date)
            for task, duration in daily_stats.items():
                if task in stats:
                    stats[task] += duration
                else:
                    stats[task] = duration
        return stats
    
    def get_monthly_stats(self, month: str = None) -> Dict[str, float]: # type: ignore
        """获取月统计数据 (格式: YYYY-MM)"""
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        
        stats = {}
        # 遍历当月每一天
        year, mon = map(int, month.split('-'))
        for day in range(1, 32):
            try:
                date = datetime(year, mon, day).strftime("%Y-%m-%d")
                daily_stats = self.get_daily_stats(date)
                for task, duration in daily_stats.items():
                    if task in stats:
                        stats[task] += duration
                    else:
                        stats[task] = duration
            except ValueError:
                # 日期无效（如2月30日），跳出循环
                break
        return stats