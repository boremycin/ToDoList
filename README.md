# Record Today

`Record Today` 是一个基于 `PySide6` 的桌面任务记录工具，适合用来追踪当天任务、专注计时，以及回看一周和一月的投入情况。

它现在的重点不只是待办清单，还包括：

- 任务计时
- 每日/每周/每月统计
- 可拖拽调整的主界面布局
- 更现代的玻璃感与卡片式界面
- Windows 下可直接打包为 `exe`

## 当前功能

- 新建、编辑、删除任务列表
- 新建、编辑、删除单个任务
- 点击任务名称开始/停止计时
- 单任务同时只允许一个任务处于计时状态
- 自动保存任务数据到本地 `JSON`
- 统计任务实际计时会话
- 报告窗口查看周统计和月统计
- 报告窗口实时显示当前进行中的计时片段
- 主界面支持上下、左右拖拽调整布局
- 报告窗口支持上下拖拽调整图表和任务统计区

## 项目结构

```text
RecordToday/
├── todolist.py          # 程序入口
├── main_window.py       # 主窗口、报告窗口、布局与交互逻辑
├── widgets.py           # 任务项组件
├── data_manager.py      # 任务与统计数据持久化
├── time_rings.py        # 顶部时间环组件
├── system_tray.py       # 系统托盘逻辑
├── utils.py             # 图标、字体等通用工具
├── todo_data.json       # 本地数据文件
├── RecordToday.spec     # PyInstaller 打包配置
├── requirements.txt     # 依赖列表
└── icon.png / icon.ico  # 应用图标
```

## 数据说明

程序会把数据保存在运行目录下的 `todo_data.json` 中，结构大致如下：

- `tasks`: 各任务列表及其任务内容
- `stats`: 按日期记录的计时统计

当前统计逻辑按“真实计时会话”记录，而不是仅在任务勾选完成时一次性写入，所以日报会更准确。

## 本地运行

### 环境要求

- Windows
- Python 3.10+
- 已安装 `pip`

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动程序

```bash
python todolist.py
```

## 打包为 exe

项目已经提供了 `PyInstaller` 配置文件，可以直接打包：

```bash
pyinstaller RecordToday.spec --noconfirm
```

打包完成后，产物默认位于：

```text
dist/RecordToday.exe
```

## 使用说明

### 主界面

- 左侧用于管理任务列表
- 右侧用于查看和管理当前列表中的任务
- 顶部是时间环区域，可点击切换工作/休息模式
- 主界面中间的分割条可拖动，调整上下与左右布局比例

### 任务计时

- 点击任务名称可开始计时
- 再次点击当前任务名称可停止计时
- 若启动另一个任务，旧任务会自动停止并记录当前会话

### 报告窗口

- 点击左侧的“报告”按钮打开
- 可以查看本周任务投入时间
- 可以查看本周总计与本月总计
- 正在运行中的任务会实时反映到报告中
- 图表区和任务统计区之间可拖动调整高度

## 设计特点

- 顶部玻璃感卡片式时间区
- 下方信息卡片布局
- 中文按钮字体优化，避免 Windows 下按钮文字异常或挤压
- 轻量本地存储，无需数据库

## 常见开发命令

```bash
python -m py_compile main_window.py widgets.py data_manager.py utils.py time_rings.py
```

```bash
pyinstaller RecordToday.spec --noconfirm
```

## 许可证

MIT License
