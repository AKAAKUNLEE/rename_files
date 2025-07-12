import os
import argparse
from pathlib import Path

def rename_files(directory='.', recursive=False, dry_run=False):
    """
    将目录中的所有 `-part` 替换为 `.part`
    
    参数:
    directory (str): 要处理的目录路径，默认为当前目录
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
    
    # 遍历并重命名文件
    for item in files:
        # 跳过目录
        if item.is_dir():
            continue
            
        old_name = item.name
        # 检查是否包含 `-part`
        if '-part' in old_name:
            new_name = old_name.replace('-part', '.part')
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
    print(f"\n操作完成:")
    print(f"已重命名的文件: {renamed_count}")
    print(f"未修改的文件: {skipped_count}")

if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='将目录中的所有 `-part` 替换为 `.part`')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归处理子目录')
    parser.add_argument('-d', '--dry-run', action='store_true', help='模拟运行，不实际重命名文件')
    parser.add_argument('-p', '--path', default='.', help='指定要处理的目录路径，默认为当前目录')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 执行重命名操作
    rename_files(args.path, args.recursive, args.dry_run)    