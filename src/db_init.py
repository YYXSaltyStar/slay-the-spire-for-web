#!/usr/bin/env python3
import os
import duckdb
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'slay_the_spire.db')

def init_database():
    """初始化数据库，创建表并插入基础数据"""
    
    # 确保数据目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 如果数据库已存在，先备份
    if os.path.exists(DB_PATH):
        backup_path = f"{DB_PATH}.bak"
        logger.info(f"数据库已存在，备份到 {backup_path}")
        try:
            os.rename(DB_PATH, backup_path)
        except Exception as e:
            logger.error(f"备份数据库失败: {e}")
    
    logger.info(f"初始化数据库: {DB_PATH}")
    
    # 连接数据库
    con = duckdb.connect(DB_PATH)
    
    try:
        # 创建角色表
        con.execute("""
        CREATE TABLE characters (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            max_hp INTEGER NOT NULL,
            starting_gold INTEGER NOT NULL,
            description TEXT
        )
        """)
        
        # 创建卡牌表
        con.execute("""
        CREATE TABLE cards (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            card_type VARCHAR NOT NULL,
            rarity VARCHAR NOT NULL,
            energy_cost INTEGER NOT NULL,
            description TEXT,
            character_id INTEGER,
            upgraded BOOLEAN DEFAULT FALSE,
            is_starter BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
        """)
        
        # 创建敌人表
        con.execute("""
        CREATE TABLE enemies (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            hp INTEGER NOT NULL,
            is_elite BOOLEAN DEFAULT FALSE,
            is_boss BOOLEAN DEFAULT FALSE,
            act INTEGER DEFAULT 1
        )
        """)
        
        # 创建遗物表
        con.execute("""
        CREATE TABLE relics (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            rarity VARCHAR NOT NULL,
            description TEXT,
            character_id INTEGER,
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
        """)
        
        # 创建药水表
        con.execute("""
        CREATE TABLE potions (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            rarity VARCHAR NOT NULL,
            description TEXT,
            effect_value INTEGER DEFAULT 0
        )
        """)
        
        # 创建事件表
        con.execute("""
        CREATE TABLE events (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            description TEXT,
            choices TEXT, -- JSON格式存储选项
            act INTEGER DEFAULT 1
        )
        """)
        
        # 创建存档表
        con.execute("""
        CREATE TABLE saves (
            player_name VARCHAR PRIMARY KEY,
            character_id INTEGER NOT NULL,
            floor INTEGER NOT NULL,
            gold INTEGER NOT NULL,
            max_hp INTEGER NOT NULL,
            current_hp INTEGER NOT NULL,
            save_data TEXT, -- JSON格式存储完整游戏状态
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
        """)
        
        # 插入角色数据
        con.execute("""
        INSERT INTO characters (id, name, max_hp, starting_gold, description) VALUES
        (1, '铁甲战士', 80, 100, '一名来自北方部落的战士，依靠力量和战斗技巧生存。'),
        (2, '静默猎手', 70, 100, '精通匕首和毒药的致命刺客。'),
        (3, '缺陷机器人', 75, 100, '一个自我修复的机器人，能够生成强大的充能球。')
        """)
        
        # 插入卡牌数据 - 铁甲战士
        con.execute("""
        INSERT INTO cards (id, name, card_type, rarity, energy_cost, description, character_id, is_starter) VALUES
        (1, '打击', '攻击', '基础', 1, '造成6点伤害', 1, TRUE),
        (2, '防御', '技能', '基础', 1, '获得5点格挡', 1, TRUE),
        (3, '愤怒', '技能', '普通', 0, '获得3点临时力量', 1, FALSE),
        (4, '重击', '攻击', '普通', 2, '造成14点伤害', 1, FALSE),
        (5, '铁斩波', '攻击', '普通', 1, '造成8点伤害', 1, FALSE),
        (6, '顺势斩', '攻击', '普通', 1, '造成12点伤害，如果你有格挡，则造成16点伤害', 1, FALSE),
        (7, '战斗呐喊', '技能', '稀有', 0, '获得1点力量', 1, FALSE),
        (8, '血肉奉献', '技能', '稀有', 2, '获得8点力量，失去6点生命', 1, FALSE),
        (9, '狂暴打击', '攻击', '稀有', 3, '对所有敌人造成8点伤害3次', 1, FALSE)
        """)
        
        # 插入卡牌数据 - 静默猎手
        con.execute("""
        INSERT INTO cards (id, name, card_type, rarity, energy_cost, description, character_id, is_starter) VALUES
        (10, '打击', '攻击', '基础', 1, '造成6点伤害', 2, TRUE),
        (11, '防御', '技能', '基础', 1, '获得5点格挡', 2, TRUE),
        (12, '毒刃', '攻击', '普通', 1, '造成5点伤害，给予2层中毒', 2, FALSE),
        (13, '闪避', '技能', '普通', 1, '获得8点格挡，抽1张牌', 2, FALSE),
        (14, '致命毒素', '技能', '普通', 1, '给予5层中毒', 2, FALSE),
        (15, '刀刃之舞', '攻击', '普通', 1, '造成4点伤害2次', 2, FALSE),
        (16, '暗影步伐', '技能', '稀有', 1, '获得6点格挡，抽2张牌', 2, FALSE),
        (17, '毒雾弹', '技能', '稀有', 2, '给予所有敌人4层中毒，抽3张牌', 2, FALSE),
        (18, '伏击', '攻击', '稀有', 0, '造成4点伤害，抽1张牌', 2, FALSE)
        """)
        
        # 插入卡牌数据 - 缺陷机器人
        con.execute("""
        INSERT INTO cards (id, name, card_type, rarity, energy_cost, description, character_id, is_starter) VALUES
        (19, '打击', '攻击', '基础', 1, '造成6点伤害', 3, TRUE),
        (20, '防御', '技能', '基础', 1, '获得5点格挡', 3, TRUE),
        (21, '闪电球', '技能', '普通', 1, '生成1个闪电球', 3, FALSE),
        (22, '冰霜球', '技能', '普通', 1, '生成1个冰霜球', 3, FALSE),
        (23, '双重施法', '技能', '普通', 1, '下一张技能牌打出两次', 3, FALSE),
        (24, '自我修复', '技能', '普通', 1, '回复3点生命，抽1张牌', 3, FALSE),
        (25, '火球术', '攻击', '普通', 1, '造成10点伤害', 3, FALSE),
        (26, '能量涌动', '技能', '稀有', 2, '获得2点能量，抽2张牌', 3, FALSE),
        (27, '核心过载', '能力', '稀有', 3, '每回合开始时生成1个闪电球和1个冰霜球', 3, FALSE),
        (28, '数据分析', '技能', '稀有', 1, '抽3张牌，丢弃1张牌', 3, FALSE)
        """)
        
        # 插入敌人数据
        con.execute("""
        INSERT INTO enemies (id, name, hp, is_elite, is_boss, act) VALUES
        (1, '小鬼', 10, FALSE, FALSE, 1),
        (2, '强盗', 15, FALSE, FALSE, 1),
        (3, '史莱姆', 12, FALSE, FALSE, 1),
        (4, '精英强盗', 40, TRUE, FALSE, 1),
        (5, '精英史莱姆', 35, TRUE, FALSE, 1),
        (6, '守卫', 45, TRUE, FALSE, 1),
        (7, '六边形幽灵', 250, FALSE, TRUE, 1),
        (8, '收藏家', 300, FALSE, TRUE, 2),
        (9, '时间吞噬者', 350, FALSE, TRUE, 3),
        (10, '腐化之心', 800, FALSE, TRUE, 4)
        """)
        
        # 插入遗物数据
        con.execute("""
        INSERT INTO relics (id, name, rarity, description, character_id) VALUES
        (1, '燃烧之血', '初始', '战斗结束后回复6点生命', 1),
        (2, '蛇之戒指', '初始', '每回合第一张攻击牌打出两次', 2),
        (3, '裂缝核心', '初始', '每回合开始时生成1个闪电球', 3),
        (4, '黑星', '普通', '精英战斗结束时获得25金币', NULL),
        (5, '血瓶', '普通', '拾取时回复10%最大生命', NULL),
        (6, '青铜鳞片', '普通', '每当你受到伤害时，给予攻击者3层中毒', NULL),
        (7, '燃烧鲜血', '稀有', '每回合开始时获得1点力量，失去1点生命', NULL),
        (8, '鸟居', '稀有', '每回合第一张能力牌不消耗能量', NULL),
        (9, '死亡面具', '稀有', '每回合开始时失去1点生命，获得1点能量', NULL),
        (10, '奈亚拉托提普', '稀有', '每当你打出一张稀有牌，抽1张牌', NULL)
        """)
        
        # 插入药水数据
        con.execute("""
        INSERT INTO potions (id, name, rarity, description, effect_value) VALUES
        (1, '力量药水', '普通', '获得2点力量', 2),
        (2, '敏捷药水', '普通', '获得2点敏捷', 2),
        (3, '治疗药水', '普通', '回复20%最大生命', 20),
        (4, '能量药水', '普通', '获得2点能量', 2),
        (5, '火焰药水', '普通', '对所有敌人造成20点伤害', 20),
        (6, '毒药水', '普通', '给予6层中毒', 6),
        (7, '烟雾弹', '稀有', '给予敌人3层虚弱和3层易伤', 3),
        (8, '万能药水', '稀有', '复制一张手牌', 0),
        (9, '仙灵药水', '稀有', '获得3张随机技能牌', 3),
        (10, '神圣药水', '稀有', '在本场战斗中，你打出的下3张攻击牌伤害翻倍', 3)
        """)
        
        # 插入事件数据
        con.execute("""
        INSERT INTO events (id, name, description, choices, act) VALUES
        (1, '神秘商人', '一个神秘的商人出现在你面前，提供特殊商品。', '["购买药水 (50金币)", "购买遗物 (150金币)", "离开"]', 1),
        (2, '古老的石碑', '你发现一块刻有奇怪符文的石碑。', '["研究符文 (获得一张稀有牌，失去3点生命)", "触摸石碑 (获得一个随机遗物，失去6点生命)", "离开"]', 1),
        (3, '被遗忘的神龛', '你发现一个被遗忘的神龛，上面覆盖着灰尘。', '["祈祷 (回复全部生命，移除一张牌)", "亵渎 (获得金币，被诅咒)", "离开"]', 1),
        (4, '诡异面具商', '一个戴着诡异面具的商人向你招手。', '["购买面具 (获得一个随机遗物，失去面额为遗物价格的生命)", "离开"]', 2),
        (5, '时间迷宫', '你发现自己在一个奇怪的迷宫中，墙壁上的时钟都走得很快。', '["向左走 (获得金币，失去生命)", "向右走 (升级一张牌，跳过下一个宝箱)", "原路返回"]', 2),
        (6, '灵魂商人', '一个没有实体的商人漂浮在你面前。', '["出售灵魂 (获得金币，最大生命永久-5)", "购买服务 (移除一张牌，失去所有金币)", "离开"]', 3)
        """)
        
        logger.info("数据库初始化成功！")
        
    except Exception as e:
        logger.error(f"初始化数据库失败: {e}")
        raise
    finally:
        con.close()

if __name__ == "__main__":
    init_database() 