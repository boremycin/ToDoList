# Record Today!
不仅是待办事项的处理, 更是每日进度的可视化监测与长期总结支持. 相信记录的力量!

## 项目完成路径
本项目高度依赖vibe-coding, 同时进行了必要的人工代码审查和修改以保证项目的效果与稳健性.

## 功能特性
- ✅ 添加、编辑和删除任务
- ✅ 数据持久化存储
- ✅ 直观的图形用户界面
- ✅ 添加工作模式和任务计时
- ✅ 支持时间成本可视化

## 未来规划
- 🔧 添加每日记录功能
- 📊 支持导出分析报告
- 📱 实现移动端与跨平台适配

## 技术栈
- **Python**: 应用程序的主要编程语言
- **PySide6**: Qt for Python，用于构建跨平台GUI
- **JSON**: 本地数据存储格式

## 安装与运行

### 系统要求
- Python 3.7+
- pip包管理器

### 安装步骤

1. 克隆或下载本项目：
   ```bash
   git clone <repository-url>
   cd todo-list-ap
   ```
2. 安装依赖
   ```bash
   pip install PySide6
   ```
3. 运行应用程序
   ```python
   python todolist.py
   ```

### 使用说明
1. 添加任务：点击"添加任务"按钮，在弹出对话框中输入任务内容
2. 完成任务：点击任务前的圆形复选框标记任务为已完成
3. 编辑任务：点击任务右侧的"编辑"按钮修改任务内容
4. 删除任务：点击任务右侧的"删除"按钮移除任务
5. 数据保存：所有任务会自动保存到本地JSON文件

### 项目结构
```
todo-list-app/
├── todolist.py          # 主入口文件
├── main_window.py       # 主窗口实现
├── widgets.py           # 自定义UI控件
├── utils.py             # 工具函数
├── todo_data.json       # 任务数据存储文件
└── README.md            # 项目说明文档
```

### 许可证
MIT License

### 作者
[Boremycin](https://boremycin.github.io/)