#!/usr/bin/env python3
import os
import sys
import random

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Character, Card, Enemy
from src.db_init import init_database, DB_PATH

def test_card(card_name, character_id=1):
    """测试指定的卡牌效果"""
    print(f"测试卡牌: {card_name}")
    
    # 确保数据库存在
    if not os.path.exists(DB_PATH):
        print("初始化数据库...")
        init_database()
    
    # 创建角色
    character = Character.load_from_db(character_id)
    print(f"角色: {character.name}")
    
    # 创建敌人
    enemy = Enemy(1, "测试敌人", 50)
    enemies = [enemy]
    
    # 查找卡牌
    import duckdb
    con = duckdb.connect(DB_PATH)
    card_data = con.execute(
        "SELECT * FROM cards WHERE name = ?",
        [card_name]
    ).fetchone()
    con.close()
    
    if not card_data:
        print(f"找不到卡牌: {card_name}")
        return
    
    # 创建卡牌
    card = Card(
        id=card_data[0],
        name=card_data[1],
        card_type=card_data[2],
        rarity=card_data[3],
        energy_cost=card_data[4],
        description=card_data[5],
        character_id=card_data[6]
    )
    
    # 测试卡牌效果
    print(f"卡牌信息: {card}")
    print("使用卡牌前:")
    print(f"  角色生命: {character.current_hp}/{character.max_hp}")
    print(f"  角色格挡: {character.block}")
    print(f"  角色力量: {character.strength}")
    print(f"  敌人生命: {enemy.current_hp}/{enemy.max_hp}")
    print(f"  敌人中毒: {enemy.poison}")
    
    # 使用卡牌
    result = card.play(character, enemies)
    
    print("\n卡牌效果:", result)
    print("\n使用卡牌后:")
    print(f"  角色生命: {character.current_hp}/{character.max_hp}")
    print(f"  角色格挡: {character.block}")
    print(f"  角色力量: {character.strength}")
    print(f"  敌人生命: {enemy.current_hp}/{enemy.max_hp}")
    print(f"  敌人中毒: {enemy.poison}")
    
    # 测试升级后的卡牌
    print("\n测试升级后的卡牌:")
    card.upgraded = True
    
    # 重置状态
    character.current_hp = character.max_hp
    character.block = 0
    character.strength = 0
    enemy.current_hp = enemy.max_hp
    enemy.poison = 0
    
    print("使用卡牌前:")
    print(f"  角色生命: {character.current_hp}/{character.max_hp}")
    print(f"  角色格挡: {character.block}")
    print(f"  角色力量: {character.strength}")
    print(f"  敌人生命: {enemy.current_hp}/{enemy.max_hp}")
    print(f"  敌人中毒: {enemy.poison}")
    
    # 使用升级后的卡牌
    result = card.play(character, enemies)
    
    print("\n卡牌效果:", result)
    print("\n使用卡牌后:")
    print(f"  角色生命: {character.current_hp}/{character.max_hp}")
    print(f"  角色格挡: {character.block}")
    print(f"  角色力量: {character.strength}")
    print(f"  敌人生命: {enemy.current_hp}/{enemy.max_hp}")
    print(f"  敌人中毒: {enemy.poison}")

def test_all_new_cards():
    """测试所有新添加的卡牌"""
    # 铁甲战士新卡牌
    test_card("血肉奉献", 1)
    test_card("狂暴打击", 1)
    test_card("战斗呐喊", 1)
    
    # 静默猎手新卡牌
    test_card("暗影步伐", 2)
    test_card("毒雾弹", 2)
    test_card("伏击", 2)
    
    # 故障机器人新卡牌
    test_card("能量涌动", 3)
    test_card("核心过载", 3)
    test_card("数据分析", 3)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 测试指定卡牌
        card_name = sys.argv[1]
        character_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        test_card(card_name, character_id)
    else:
        # 测试所有新卡牌
        test_all_new_cards() 