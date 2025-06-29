#!/usr/bin/env python3
import os
import sys
from src.game import SlayTheSpireGame
from src.db_init import init_database

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    # 初始化数据库
    print("初始化数据库...")
    init_database()
    
    # 创建游戏实例并显示主菜单
    print("创建游戏实例...")
    game = SlayTheSpireGame()
    print("显示主菜单...")
    game.show_main_menu()


if __name__ == "__main__":
    main() 