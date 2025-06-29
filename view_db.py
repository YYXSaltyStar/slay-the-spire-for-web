#!/usr/bin/env python3
import duckdb
import os
from src.db_init import DB_PATH

def view_database():
    """查看游戏数据库的表和内容"""
    if not os.path.exists(DB_PATH):
        print(f"错误：数据库文件 {DB_PATH} 不存在")
        return
    
    print(f"连接到数据库: {DB_PATH}")
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    # 获取所有表名
    tables = conn.execute("SHOW TABLES").fetchall()
    print("\n=== 数据库中的表 ===")
    for i, (table_name,) in enumerate(tables, 1):
        print(f"{i}. {table_name}")
    
    while True:
        print("\n请选择操作:")
        print("1. 查看表结构")
        print("2. 查看表内容")
        print("3. 执行自定义SQL查询")
        print("q. 退出")
        
        choice = input("请输入选项: ")
        
        if choice == 'q':
            break
        elif choice == '1':
            table_name = input("请输入要查看结构的表名: ")
            try:
                schema = conn.execute(f"DESCRIBE {table_name}").fetchall()
                print(f"\n=== {table_name} 表结构 ===")
                for col in schema:
                    print(f"列名: {col[0]}, 类型: {col[1]}")
            except Exception as e:
                print(f"错误: {e}")
        elif choice == '2':
            table_name = input("请输入要查看内容的表名: ")
            try:
                limit = input("要显示多少行? (默认10): ") or "10"
                rows = conn.execute(f"SELECT * FROM {table_name} LIMIT {limit}").fetchall()
                columns = [col[0] for col in conn.description]
                
                print(f"\n=== {table_name} 表内容 (前 {limit} 行) ===")
                print(" | ".join(columns))
                print("-" * 80)
                for row in rows:
                    print(" | ".join(str(item) for item in row))
                
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                print(f"\n总行数: {count}")
            except Exception as e:
                print(f"错误: {e}")
        elif choice == '3':
            query = input("请输入SQL查询: ")
            try:
                result = conn.execute(query).fetchall()
                if conn.description:
                    columns = [col[0] for col in conn.description]
                    print("\n=== 查询结果 ===")
                    print(" | ".join(columns))
                    print("-" * 80)
                    for row in result[:20]:  # 只显示前20行
                        print(" | ".join(str(item) for item in row))
                    
                    if len(result) > 20:
                        print(f"\n显示了20行，共有 {len(result)} 行结果")
                else:
                    print("查询执行成功，但没有返回结果")
            except Exception as e:
                print(f"错误: {e}")
        else:
            print("无效选项，请重新输入")
    
    conn.close()
    print("数据库连接已关闭")

if __name__ == "__main__":
    view_database() 