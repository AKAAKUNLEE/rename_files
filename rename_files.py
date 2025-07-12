import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading

class FileRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文件重命名工具")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # 设置中文字体
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("SimHei", 10))
        self.style.configure("TButton", font=("SimHei", 10))
        self.style.configure("TCheckbutton", font=("SimHei", 10))
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 源目录选择
        ttk.Label(main_frame, text="选择目录:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # 获取程序所在目录作为默认值
        self.default_dir = os.path.dirname(os.path.abspath(__file__))
        self.dir_var = tk.StringVar(value=self.default_dir)
        
        dir_entry = ttk.Entry(main_frame, textvariable=self.dir_var, width=50)
        dir_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        browse_btn = ttk.Button(main_frame, text="浏览...", command=self.browse_directory)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # 重命名模式选择
        ttk.Label(main_frame, text="重命名模式:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.mode_var = tk.StringVar(value="to-dot")
        
        to_dot_radio = ttk.Radiobutton(main_frame, text="将 '-part' 替换为 '.part'", 
                                     variable=self.mode_var, value="to-dot")
        to_dot_radio.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        to_dash_radio = ttk.Radiobutton(main_frame, text="将 '.part' 替换为 '-part'", 
                                      variable=self.mode_var, value="to-dash")
        to_dash_radio.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # 选项
        options_frame = ttk.LabelFrame(main_frame, text="选项", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.recursive_var = tk.BooleanVar(value=False)
        recursive_check = ttk.Checkbutton(options_frame, text="递归处理子目录", 
                                        variable=self.recursive_var)
        recursive_check.pack(side=tk.LEFT, padx=10)
        
        self.dry_run_var = tk.BooleanVar(value=True)
        dry_run_check = ttk.Checkbutton(options_frame, text="模拟运行（不实际修改文件）", 
                                       variable=self.dry_run_var)
        dry_run_check.pack(side=tk.LEFT, padx=10)
        
        # 按钮
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=4, column=0, columnspan=3, pady=15)
        
        self.rename_btn = ttk.Button(buttons_frame, text="开始重命名", 
                                    command=self.start_rename, width=15)
        self.rename_btn.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(buttons_frame, text="退出", command=root.quit, width=10).pack(side=tk.LEFT)
        
        # 进度和日志
        ttk.Label(main_frame, text="操作日志:").grid(row=5, column=0, sticky=tk.W, pady=5)
        
        self.log_text = tk.Text(main_frame, height=10, width=70, wrap=tk.WORD)
        self.log_text.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=6, column=3, sticky=(tk.N, tk.S))
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 初始化日志
        self.log("欢迎使用文件重命名工具")
        self.log(f"默认目录: {self.default_dir}")
        self.log("请选择重命名模式，然后点击'开始重命名'按钮")
    
    def browse_directory(self):
        """浏览并选择目录"""
        directory = filedialog.askdirectory(initialdir=self.dir_var.get(), 
                                           title="选择目录")
        if directory:
            self.dir_var.set(directory)
    
    def log(self, message):
        """添加日志到文本框"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
    
    def rename_files(self):
        """执行文件重命名操作"""
        directory = self.dir_var.get()
        mode = self.mode_var.get()
        recursive = self.recursive_var.get()
        dry_run = self.dry_run_var.get()
        
        # 检查目录是否存在
        if not os.path.isdir(directory):
            messagebox.showerror("错误", f"指定的目录不存在: {directory}")
            self.rename_btn.config(state=tk.NORMAL)
            self.update_status("就绪")
            return
        
        try:
            self.log(f"\n开始在目录 '{directory}' 中执行重命名操作...")
            
            # 根据模式设置替换规则
            if mode == 'to-dot':
                old_str, new_str = '-part', '.part'
                mode_desc = "将 '-part' 替换为 '.part'"
            else:  # to-dash
                old_str, new_str = '.part', '-part'
                mode_desc = "将 '.part' 替换为 '-part'"
            
            self.log(f"模式: {mode_desc}")
            self.log(f"递归: {recursive}")
            self.log(f"模拟运行: {dry_run}")
            self.log("-" * 50)
            
            # 计数器
            renamed_count = 0
            skipped_count = 0
            
            # 遍历目录
            if recursive:
                walk_func = os.walk
            else:
                def walk_func(path):
                    yield next(os.walk(path))
            
            for root, _, files in walk_func(directory):
                for filename in files:
                    old_name = os.path.join(root, filename)
                    
                    # 检查是否包含目标字符串
                    if old_str in filename:
                        new_filename = filename.replace(old_str, new_str)
                        new_name = os.path.join(root, new_filename)
                        
                        # 避免自身重命名
                        if new_name == old_name:
                            skipped_count += 1
                            continue
                            
                        # 执行重命名或仅显示操作
                        try:
                            if dry_run:
                                log_msg = f"模拟: 将 '{filename}' 重命名为 '{new_filename}'"
                                self.log(log_msg)
                            else:
                                os.rename(old_name, new_name)
                                self.log(f"已重命名: {filename} -> {new_filename}")
                                renamed_count += 1
                        except Exception as e:
                            self.log(f"错误: 无法重命名 '{filename}': {str(e)}")
                    else:
                        skipped_count += 1
            
            # 输出统计信息
            self.log("-" * 50)
            self.log(f"{mode_desc}操作完成:")
            self.log(f"已重命名的文件: {renamed_count}")
            self.log(f"未修改的文件: {skipped_count}")
            
            if dry_run:
                self.log("\n提示: 当前为模拟运行模式，未实际修改任何文件。")
                self.log("若要执行实际重命名，请取消'模拟运行'选项。")
            
            self.update_status(f"操作完成: 重命名 {renamed_count} 个文件")
            
        except Exception as e:
            self.log(f"错误: {str(e)}")
            self.update_status(f"操作失败: {str(e)}")
        finally:
            self.rename_btn.config(state=tk.NORMAL)
    
    def start_rename(self):
        """开始重命名线程"""
        self.log_text.delete(1.0, tk.END)  # 清空日志
        self.rename_btn.config(state=tk.DISABLED)
        self.update_status("正在处理...")
        
        # 在单独的线程中执行重命名，避免界面卡顿
        thread = threading.Thread(target=self.rename_files)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = FileRenamerApp(root)
    root.mainloop()    