import os
import sys
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QRadioButton, QCheckBox, QFileDialog, QTextEdit, 
                            QStatusBar, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

class RenameThread(QThread):
    """文件重命名线程，用于后台执行重命名操作，避免界面卡顿"""
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int, int)
    
    def __init__(self, directory, mode, recursive, dry_run):
        super().__init__()
        self.directory = directory
        self.mode = mode
        self.recursive = recursive
        self.dry_run = dry_run
        self.old_str = '-part' if mode == 'to-dot' else '.part'
        self.new_str = '.part' if mode == 'to-dot' else '-part'
        self.mode_desc = "将 '-part' 替换为 '.part'" if mode == 'to-dot' else "将 '.part' 替换为 '-part'"
        
    def run(self):
        renamed_count = 0
        skipped_count = 0
        
        self.log_signal.emit(f"\n开始在目录 '{self.directory}' 中执行重命名操作...")
        self.log_signal.emit(f"模式: {self.mode_desc}")
        self.log_signal.emit(f"递归: {self.recursive}")
        self.log_signal.emit(f"模拟运行: {self.dry_run}")
        self.log_signal.emit("-" * 50)
        
        try:
            # 遍历目录
            if self.recursive:
                walk_func = os.walk
            else:
                def walk_func(path):
                    yield next(os.walk(path))
            
            for root, _, files in walk_func(self.directory):
                for filename in files:
                    old_name = os.path.join(root, filename)
                    
                    # 检查是否包含目标字符串
                    if self.old_str in filename:
                        new_filename = filename.replace(self.old_str, self.new_str)
                        new_name = os.path.join(root, new_filename)
                        
                        # 避免自身重命名
                        if new_name == old_name:
                            skipped_count += 1
                            continue
                            
                        # 执行重命名或仅显示操作
                        try:
                            if self.dry_run:
                                log_msg = f"模拟: 将 '{filename}' 重命名为 '{new_filename}'"
                                self.log_signal.emit(log_msg)
                            else:
                                os.rename(old_name, new_name)
                                self.log_signal.emit(f"已重命名: {filename} -> {new_filename}")
                                renamed_count += 1
                        except Exception as e:
                            self.log_signal.emit(f"错误: 无法重命名 '{filename}': {str(e)}")
                    else:
                        skipped_count += 1
            
            # 输出统计信息
            self.log_signal.emit("-" * 50)
            self.log_signal.emit(f"{self.mode_desc}操作完成:")
            self.log_signal.emit(f"已重命名的文件: {renamed_count}")
            self.log_signal.emit(f"未修改的文件: {skipped_count}")
            
            if self.dry_run:
                self.log_signal.emit("\n提示: 当前为模拟运行模式，未实际修改任何文件。")
                self.log_signal.emit("若要执行实际重命名，请取消'模拟运行'选项。")
            
            self.status_signal.emit(f"操作完成: 重命名 {renamed_count} 个文件")
            self.finished_signal.emit(renamed_count, skipped_count)
            
        except Exception as e:
            self.log_signal.emit(f"错误: {str(e)}")
            self.status_signal.emit(f"操作失败: {str(e)}")

class FileRenamerApp(QMainWindow):
    """文件重命名工具主窗口"""
    def __init__(self):
        super().__init__()
        
        # 设置窗口标题和大小
        self.setWindowTitle("文件重命名工具")
        self.setGeometry(100, 100, 700, 500)
        
        # 设置中文字体
        font = QFont()
        font.setFamily("SimHei")
        font.setPointSize(10)
        self.setFont(font)
        
        # 创建中心部件和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
        
        # 创建UI组件
        self.create_directory_section()
        self.create_mode_section()
        self.create_options_section()
        self.create_log_section()
        self.create_buttons_section()
        
        # 初始化
        self.rename_thread = None
        self.default_dir = os.path.dirname(os.path.abspath(__file__))
        self.dir_path.setText(self.default_dir)
        self.log_text.append("欢迎使用文件重命名工具")
        self.log_text.append(f"默认目录: {self.default_dir}")
        self.log_text.append("请选择重命名模式，然后点击'开始重命名'按钮")
    
    def create_directory_section(self):
        """创建目录选择部分"""
        dir_layout = QHBoxLayout()
        
        self.dir_label = QLabel("选择目录:")
        self.dir_path = QLineEdit()
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_directory)
        
        dir_layout.addWidget(self.dir_label)
        dir_layout.addWidget(self.dir_path, 1)
        dir_layout.addWidget(self.browse_btn)
        
        self.main_layout.addLayout(dir_layout)
    
    def create_mode_section(self):
        """创建重命名模式选择部分"""
        mode_group = QGroupBox("重命名模式")
        mode_layout = QVBoxLayout()
        
        self.to_dot_radio = QRadioButton("将 '-part' 替换为 '.part'")
        self.to_dash_radio = QRadioButton("将 '.part' 替换为 '-part'")
        
        self.to_dot_radio.setChecked(True)
        
        mode_layout.addWidget(self.to_dot_radio)
        mode_layout.addWidget(self.to_dash_radio)
        
        mode_group.setLayout(mode_layout)
        self.main_layout.addWidget(mode_group)
    
    def create_options_section(self):
        """创建选项部分"""
        options_group = QGroupBox("选项")
        options_layout = QHBoxLayout()
        
        self.recursive_check = QCheckBox("递归处理子目录")
        self.dry_run_check = QCheckBox("模拟运行（不实际修改文件）")
        self.dry_run_check.setChecked(True)
        
        options_layout.addWidget(self.recursive_check)
        options_layout.addWidget(self.dry_run_check)
        
        options_group.setLayout(options_layout)
        self.main_layout.addWidget(options_group)
    
    def create_log_section(self):
        """创建日志显示部分"""
        log_layout = QVBoxLayout()
        
        self.log_label = QLabel("操作日志:")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        
        log_layout.addWidget(self.log_label)
        log_layout.addWidget(self.log_text)
        
        self.main_layout.addLayout(log_layout)
    
    def create_buttons_section(self):
        """创建按钮部分"""
        buttons_layout = QHBoxLayout()
        
        self.rename_btn = QPushButton("开始重命名")
        self.rename_btn.setMinimumHeight(40)
        self.rename_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.rename_btn.clicked.connect(self.start_rename)
        
        self.exit_btn = QPushButton("退出")
        self.exit_btn.setMinimumHeight(40)
        self.exit_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.exit_btn.clicked.connect(self.close)
        
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.rename_btn)
        buttons_layout.addWidget(self.exit_btn)
        buttons_layout.addStretch(1)
        
        self.main_layout.addLayout(buttons_layout)
    
    def browse_directory(self):
        """浏览并选择目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择目录", self.dir_path.text(), QFileDialog.ShowDirsOnly
        )
        
        if directory:
            self.dir_path.setText(directory)
    
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.append(message)
        # 滚动到底部
        self.log_text.moveCursor(self.log_text.textCursor().End)
    
    def update_status(self, message):
        """更新状态栏消息"""
        self.statusBar.showMessage(message)
    
    def start_rename(self):
        """开始重命名操作"""
        directory = self.dir_path.text()
        mode = 'to-dot' if self.to_dot_radio.isChecked() else 'to-dash'
        recursive = self.recursive_check.isChecked()
        dry_run = self.dry_run_check.isChecked()
        
        # 检查目录是否存在
        if not os.path.isdir(directory):
            QMessageBox.critical(self, "错误", f"指定的目录不存在: {directory}")
            return
        
        # 清空日志
        self.log_text.clear()
        
        # 创建并启动重命名线程
        self.rename_thread = RenameThread(directory, mode, recursive, dry_run)
        self.rename_thread.log_signal.connect(self.log_message)
        self.rename_thread.status_signal.connect(self.update_status)
        self.rename_thread.finished_signal.connect(self.on_rename_finished)
        self.rename_thread.start()
        
        # 更新UI状态
        self.rename_btn.setEnabled(False)
        self.update_status("正在处理...")
    
    def on_rename_finished(self, renamed_count, skipped_count):
        """重命名完成后的回调函数"""
        self.rename_btn.setEnabled(True)
        
        # 显示操作结果对话框
        result_msg = f"操作完成!\n\n已重命名的文件: {renamed_count}\n未修改的文件: {skipped_count}"
        if renamed_count > 0:
            QMessageBox.information(self, "操作完成", result_msg)
        else:
            QMessageBox.warning(self, "操作完成", result_msg + "\n\n未找到需要重命名的文件。")

if __name__ == "__main__":
    # 确保中文显示正常
    os.environ["QT_FONT_DPI"] = "96"
    
    app = QApplication(sys.argv)
    window = FileRenamerApp()
    window.show()
    sys.exit(app.exec_())    