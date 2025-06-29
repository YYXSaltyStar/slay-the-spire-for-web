#!/usr/bin/env python3
import os
import shutil
from src.db_init import init_database, DB_PATH

def reset_database():
    """重置数据库并重新初始化"""
    # 检查数据库文件是否存在
    if os.path.exists(DB_PATH):
        # 创建备份
        backup_path = DB_PATH + '.bak'
        print(f"备份原数据库到 {backup_path}")
        shutil.copy2(DB_PATH, backup_path)
        
        # 删除原数据库
        print(f"删除原数据库 {DB_PATH}")
        os.remove(DB_PATH)
    
    # 重新初始化数据库
    print("重新初始化数据库...")
    init_database()
    print("数据库重置完成！")

if __name__ == "__main__":
    reset_database() 