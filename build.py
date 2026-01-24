import os
import subprocess
import shutil

def build_executable():
    # 清理之前的构建文件
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # PyInstaller命令参数
    cmd = [
        'pyinstaller',
        '--name=RecordToday',  # 可执行文件名称
        '--windowed',  # 图形界面应用，不显示控制台
        '--onedir',  # 打包为单个目录
        '--add-data=data;data',  # 包含数据文件夹
        '--hidden-import=PySide6.QtSvg',  # 显式包含PySide6组件
        '--hidden-import=PySide6.QtPrintSupport',
        'main.py'  # 主入口文件
    ]
    
    subprocess.run(cmd)

if __name__ == "__main__":
    build_executable()