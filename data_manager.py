"""数据持久化模块 - 处理 JSON 数据的读写"""
import json
import os
from typing import Dict, List


class DataManager:
    """管理应用数据的持久化"""

    def __init__(self, data_file: str):
        self.data_file = data_file
        self.data: Dict[str, List[Dict]] = {}

    def load(self) -> Dict[str, List[Dict]]:
        """从文件加载数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            else:
                self.data = {}
        except Exception as e:
            print(f"Failed to load data: {e}")
            self.data = {}
        return self.data

    def save(self) -> bool:
        """保存数据到文件"""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Save failed: {e}")
            return False

    def get_data(self) -> Dict[str, List[Dict]]:
        """获取数据"""
        return self.data

    def set_data(self, data: Dict[str, List[Dict]]):
        """设置数据"""
        self.data = data
