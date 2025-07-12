import os
import argparse
from pathlib import Path

def rename_files(directory='.', mode='to-dot', recursive=False, dry_run=False):
    """
    批量重命名文件
    
    参数:
    directory (str): 要处理的目录路径，默认为当前目录
    mode (str): 重命名模式，'to-dot' 表示 '-part' 替换为 '.part'，'to-dash' 表示 '.part' 替换为 '-part'
    recursive (bool): 是否递归处理子目录，默认为 False
    dry_run (bool): 是否执行模拟运行，只显示操作不实际重命名，默认为 False
    """
    # 转换目录路径为绝对路径
    directory = Path(directory).resolve()
    
    # 确保目录存在
    if not directory.exists() or not directory.is_dir():
        print(f"错误: 指定的目录 '{directory}' 不存在或不是一个目录")
        return
    
    # 确定要遍历的文件
    if recursive:
        files = directory.rglob('*')
    else:
        files = directory.glob('*')
    
    # 计数器
    renamed_count = 0
    skipped_count = 0
    
    # 根据模式设置替换规则
    if mode == 'to-dot':
        old_str, new_str = '-part', '.part'
        mode_desc = "将 '-part' 替换为 '.part'"
    elif mode == 'to-dash':
        old_str, new_str = '.part', '-part'
        mode_desc = "将 '.part' 替换为 '-part'"
    else:
        print(f"错误: 未知模式 '{mode}'，请使用 'to-dot' 或 'to-dash'")
        return
    
    print(f"开始{mode_desc}...")
    
    # 遍历并重命名文件
    for item in files:
        # 跳过目录
        if item.is_dir():
            continue
            
        old_name = item.name
        # 检查是否包含目标字符串
        if old_str in old_name:
            new_name = old_name.replace(old_str, new_str)
            new_path = item.with_name(new_name)
            
            # 避免自身重命名
            if new_path == item:
                skipped_count += 1
                continue
                
            # 执行重命名或仅显示操作
            if dry_run:
                print(f"将 '{old_name}' 重命名为 '{new_name}' (模拟运行)")
            else:
                try:
                    item.rename(new_path)
                    print(f"已将 '{old_name}' 重命名为 '{new_name}'")
                    renamed_count += 1
                except Exception as e:
                    print(f"无法重命名 '{old_name}': {e}")
        else:
            skipped_count += 1
    
    # 输出统计信息
    print(f"\n{mode_desc}操作完成:")
    print(f"已重命名的文件: {renamed_count}")
    print(f"未修改的文件: {skipped_count}")

if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='批量重命名文件')
    parser.add_argument('-m', '--mode', choices=['to-dot', 'to-dash'], default='to-dot',
                        help="'to-dot' 表示将 '-part' 替换为 '.part' (默认), 'to-dash' 表示将 '.part' 替换为 '-part'")
    parser.add_argument('-r', '--recursive', action='store_true', help='递归处理子目录')
    parser.add_argument('-d', '--dry-run', action='store_true', help='模拟运行，不实际重命名文件')
    parser.add_argument('-p', '--path', default='.', help='指定要处理的目录路径，默认为当前目录')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 执行重命名操作
    rename_files(args.path, args.mode, args.recursive, args.dry_run)    