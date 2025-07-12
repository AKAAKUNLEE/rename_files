import os
import sys
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QRadioButton, QCheckBox, QFileDialog, QTextEdit, 
                            QStatusBar, QGroupBox, QMessageBox, QGraphicsBlurEffect)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QTimer, QRect, QRectF
from PyQt5.QtGui import (QFont, QColor, QPalette, QPainter, QPen, QBrush, 
                        QIcon, QPixmap, QLinearGradient, QPainterPath, QRegion)

def get_real_exe_path():
    """获取打包后的exe实际路径（解决PyInstaller临时目录问题）"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))

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
        
        # 根据模式设置替换规则
        if mode == 'to-dot':
            self.old_str = '-part'
            self.new_str = '.part'
            self.mode_desc = "将 '-part' 替换为 '.part'"
        elif mode == 'to-dash':
            self.old_str = '.part'
            self.new_str = '-part'
            self.mode_desc = "将 '.part' 替换为 '-part'"
        elif mode == 'rev-to-rar':
            self.old_str = '.part'  # 用于匹配 .part01.rev
            self.new_str = '-part'  # 用于替换为 -part01.rar
            self.mode_desc = "将 '.partXX.rev' 替换为 '-partXX.rar'"
        elif mode == 'rar-to-rev':
            self.old_str = '-part'  # 用于匹配 -part01.rar
            self.new_str = '.part'  # 用于替换为 .part01.rev
            self.mode_desc = "将 '-partXX.rar' 替换为 '.partXX.rev'"
        
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
                    
                    # 根据不同模式执行不同的替换逻辑
                    if self.mode in ['to-dot', 'to-dash']:
                        # 简单替换 -part 和 .part
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
                    
                    elif self.mode in ['rev-to-rar', 'rar-to-rev']:
                        # 复杂替换：.part01.rev ↔ -part01.rar
                        if self.mode == 'rev-to-rar' and filename.endswith('.rev') and self.old_str in filename:
                            # 从 .part01.rev 转换为 -part01.rar
                            base_part = filename.rsplit('.', 2)[0]  # 获取 "filename.part01"
                            new_filename = base_part.replace(self.old_str, self.new_str) + '.rar'
                            new_name = os.path.join(root, new_filename)
                            
                            if new_name == old_name:
                                skipped_count += 1
                                continue
                                
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
                        
                        elif self.mode == 'rar-to-rev' and filename.endswith('.rar') and self.old_str in filename:
                            # 从 -part01.rar 转换为 .part01.rev
                            base_part = filename.rsplit('.', 1)[0]  # 获取 "filename-part01"
                            new_filename = base_part.replace(self.old_str, self.new_str) + '.rev'
                            new_name = os.path.join(root, new_filename)
                            
                            if new_name == old_name:
                                skipped_count += 1
                                continue
                                
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

class AcrylicWidget(QWidget):
    """实现亚克力效果的基础窗口类"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        
        # 亚克力效果参数
        self.blur_radius = 15
        self.acrylic_color = QColor(240, 240, 240, 180)  # RGBA
        self.border_radius = 15
        
        # 窗口拖动支持
        self.dragging = False
        self.drag_position = QPoint()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建路径并绘制亚克力背景
        path = QPainterPath()
        # 使用QRectF替代QRect以解决类型错误
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 
                           self.border_radius, self.border_radius)
        
        # 绘制半透明背景
        painter.fillPath(path, self.acrylic_color)
        
        # 绘制边框
        pen = QPen(QColor(255, 255, 255, 100), 2)
        painter.setPen(pen)
        painter.drawPath(path)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()

class FileRenamerApp(AcrylicWidget):
    """文件重命名工具主窗口"""
    def __init__(self):
        super().__init__()
        
        # 设置窗口标题和大小
        self.setWindowTitle("文件重命名工具")
        self.resize(700, 500)
        
        # 设置中文字体
        font = QFont()
        font.setFamily("SimHei")
        font.setPointSize(10)
        self.setFont(font)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # 创建UI组件
        self.create_title_bar()
        self.create_directory_section()
        self.create_mode_section()
        self.create_options_section()
        self.create_log_section()
        self.create_buttons_section()
        
        # 初始化
        self.rename_thread = None
        self.default_dir = get_real_exe_path()  # 使用新函数获取真实路径
        self.dir_path.setText(self.default_dir)
        self.log_text.append("欢迎使用文件重命名工具")
        self.log_text.append(f"默认目录: {self.default_dir}")
        self.log_text.append("请选择重命名模式，然后点击'开始重命名'按钮")
    
    def create_title_bar(self):
        """创建标题栏"""
        title_layout = QHBoxLayout()
        
        self.title_label = QLabel("文件重命名工具")
        self.title_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333;")
        
        # 关闭按钮
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(25, 25)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff4757;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        
        # 最小化按钮
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedSize(25, 25)
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffd166;
                color: white;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffc107;
            }
        """)
        self.minimize_btn.clicked.connect(self.showMinimized)
        
        title_layout.addWidget(self.title_label)
        title_layout.addStretch(1)
        title_layout.addWidget(self.minimize_btn)
        title_layout.addWidget(self.close_btn)
        
        self.main_layout.addLayout(title_layout)
    
    def create_directory_section(self):
        """创建目录选择部分"""
        dir_layout = QHBoxLayout()
        
        self.dir_label = QLabel("选择目录:")
        self.dir_label.setStyleSheet("font-weight: bold;")
        
        self.dir_path = QLineEdit()
        self.dir_path.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a69bd;
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #3c6382;
            }
        """)
        self.browse_btn.clicked.connect(self.browse_directory)
        
        dir_layout.addWidget(self.dir_label)
        dir_layout.addWidget(self.dir_path, 1)
        dir_layout.addWidget(self.browse_btn)
        
        self.main_layout.addLayout(dir_layout)
    
    def create_mode_section(self):
        """创建重命名模式选择部分"""
        mode_group = QGroupBox("重命名模式")
        mode_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.6);
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                font-weight: bold;
            }
        """)
        
        mode_layout = QVBoxLayout()
        
        self.to_dot_radio = QRadioButton("将 '-part' 替换为 '.part'")
        self.to_dash_radio = QRadioButton("将 '.part' 替换为 '-part'")
        self.rev_to_rar_radio = QRadioButton("将 '.partXX.rev' 替换为 '-partXX.rar'")
        self.rar_to_rev_radio = QRadioButton("将 '-partXX.rar' 替换为 '.partXX.rev'")
        
        self.to_dot_radio.setChecked(True)
        
        # 修复单选按钮样式
        radio_style = """
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:checked {
                border-radius: 9px;
                background-color: #4a69bd;
                border: 2px solid white;
                width: 14px;
                height: 14px;
            }
            QRadioButton::indicator:unchecked {
                border-radius: 9px;
                border: 2px solid #4a69bd;
            }
        """
        self.to_dot_radio.setStyleSheet(radio_style)
        self.to_dash_radio.setStyleSheet(radio_style)
        self.rev_to_rar_radio.setStyleSheet(radio_style)
        self.rar_to_rev_radio.setStyleSheet(radio_style)
        
        mode_layout.addWidget(self.to_dot_radio)
        mode_layout.addWidget(self.to_dash_radio)
        mode_layout.addWidget(self.rev_to_rar_radio)
        mode_layout.addWidget(self.rar_to_rev_radio)
        
        mode_group.setLayout(mode_layout)
        self.main_layout.addWidget(mode_group)
    
    def create_options_section(self):
        """创建选项部分"""
        options_group = QGroupBox("选项")
        options_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.6);
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                font-weight: bold;
            }
        """)
        
        options_layout = QHBoxLayout()
        
        self.recursive_check = QCheckBox("递归处理子目录")
        self.dry_run_check = QCheckBox("模拟运行（不实际修改文件）")
        self.dry_run_check.setChecked(True)
        
        # 使用纯CSS重新实现复选框样式，不依赖图标
        check_style = """
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #4a69bd;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #4a69bd;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxNiAxNiI+PHBhdGggZD0iTTE0LjI4MyAyLjI4M0w2LjAwMyAxMC4wNjNsLTMuMjgzLTMuMjgzQzIuMjgzIDYuNDQzIDIuMDM3IDYuMjk3IDEuNzUgNi4yOTdDMS40NjMgNi4yOTcgMS4yMTYgNi40NDQgMS4yMTYgNi43MDFjMCAwLjI1NyAwLjI0NyAwLjUwMyAwLjUyNyAwLjUwM2MwLjIxNyAwIDAuNDE4LTAuMDkzIDAuNTczLTAuMjU0bDIuNzYgMi43NjdDNS41NjMgMTAuOTMzIDUuNzYzIDExIDYgMTFjMC4yMzYgMCAwLjQzNy0wLjA2NyAwLjU5My0wLjIwN2w3Ljc3LTEwLjU1M2MwLjE5LS4yNjMuMTctMC42MDYtMC4wNS0wLjgzM2MtMC4yMi0wLjIyLTAuNTctMC4yNC0wLjgzLTAuMDVMMTYgMy45NjdjMC4xOSAwLjIzIDAuMTkgMC42MSAwIDAuODQzTDYuODAzIDE1LjI3N2MtMC4yMDMuMjEtMC41NDUuMjEtMC43NDggMGwtNC4wNjMtNC4wNjRjLTAuMjEtMC4yMS0wLjIxLTAuNTU0IDAtMC43NjRjMC4yMS0wLjIxIDAuNTU0LTAuMjEgMC43NjQgMEw2IDExLjI1N2w3LjU4LTAuMDQzTDkuMjE1IDQuMjA0bC0wLjAwMi0wLjAwMnoiIGZpbGw9IiNmZmYiLz48L3N2Zz4=);
            }
            QCheckBox::indicator:unchecked {
                background-color: transparent;
            }
        """
        self.recursive_check.setStyleSheet(check_style)
        self.dry_run_check.setStyleSheet(check_style)
        
        options_layout.addWidget(self.recursive_check)
        options_layout.addWidget(self.dry_run_check)
        
        options_group.setLayout(options_layout)
        self.main_layout.addWidget(options_group)
    
    def create_log_section(self):
        """创建日志显示部分"""
        log_layout = QVBoxLayout()
        
        self.log_label = QLabel("操作日志:")
        self.log_label.setStyleSheet("font-weight: bold;")
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        log_layout.addWidget(self.log_label)
        log_layout.addWidget(self.log_text)
        
        self.main_layout.addLayout(log_layout)
    
    def create_buttons_section(self):
        """创建按钮部分"""
        buttons_layout = QHBoxLayout()
        
        self.rename_btn = QPushButton("开始重命名")
        self.rename_btn.setMinimumHeight(40)
        self.rename_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.rename_btn.clicked.connect(self.start_rename)
        
        self.exit_btn = QPushButton("退出")
        self.exit_btn.setMinimumHeight(40)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
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
        # 由于无边框窗口没有默认状态栏，这里可以考虑添加一个自定义状态栏
        # 简化处理，使用日志显示
        self.log_message(f"[状态] {message}")
    
    def start_rename(self):
        """开始重命名操作"""
        directory = self.dir_path.text()
        # 根据选中的单选按钮确定重命名模式
        if self.to_dot_radio.isChecked():
            mode = 'to-dot'
        elif self.to_dash_radio.isChecked():
            mode = 'to-dash'
        elif self.rev_to_rar_radio.isChecked():
            mode = 'rev-to-rar'
        elif self.rar_to_rev_radio.isChecked():
            mode = 'rar-to-rev'
        
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
    
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    
    # 设置应用全局样式
    app.setStyleSheet("""
        QToolTip {
            background-color: rgba(255, 255, 255, 220);
            color: #333;
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 5px;
        }
    """)
    
    window = FileRenamerApp()
    window.show()
    sys.exit(app.exec_())    