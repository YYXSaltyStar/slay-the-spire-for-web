#!/usr/bin/env python3
import os
import random
import time
import duckdb
from colorama import Fore, Style

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'slay_the_spire.db')

class MapNode:
    """地图节点类"""
    
    def __init__(self, node_type, x, y):
        self.node_type = node_type
        self.x = x
        self.y = y
        self.visited = False
        self.available = False
        
    def to_dict(self):
        """将地图节点序列化为字典"""
        return {
            'type': self.node_type,
            'x': self.x,
            'y': self.y,
            'visited': self.visited,
            'available': self.available
        }

class Event:
    """事件类"""
    
    def __init__(self, id, name, description, choices):
        self.id = id
        self.name = name
        self.description = description
        self.choices = choices  # 选项列表
        
    def to_dict(self):
        """将事件序列化为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'choices': self.choices
        }

class Card:
    """卡牌类"""
    def __init__(self, id, name, card_type, rarity, energy_cost, description, character_id=None, upgraded=False):
        self.id = id
        self.name = name
        self.card_type = card_type
        self.rarity = rarity
        self.cost = energy_cost
        self.description = description
        self.character_id = character_id
        self.upgraded = upgraded
        self.exhausted = False
        self.ethereal = False  # 虚无属性，打出后消耗
        self.innate = False  # 固有属性，初始手牌必定包含
        self.retain = False  # 保留属性，回合结束不丢弃
        
    def to_dict(self):
        """将卡牌序列化为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'card_type': self.card_type,
            'rarity': self.rarity,
            'cost': self.cost,
            'description': self.description,
            'character_id': self.character_id,
            'upgraded': self.upgraded,
            'exhausted': self.exhausted,
            'ethereal': self.ethereal,
            'innate': self.innate,
            'retain': self.retain
        }
        
    def upgrade(self):
        """升级卡牌"""
        if self.upgraded:
            return False
            
        self.upgraded = True
        
        # 根据卡牌名称应用不同的升级效果
        if "打击" in self.name:
            self.description = self.description.replace("6", "9")
        elif "防御" in self.name:
            self.description = self.description.replace("5", "8")
        elif self.name == "愤怒":
            self.description = self.description.replace("3", "5")
        elif self.name == "重击":
            self.description = self.description.replace("14", "18")
        elif self.name == "铁斩波":
            self.description = self.description.replace("8", "12")
        elif self.name == "顺势斩":
            self.description = self.description.replace("12", "16").replace("16", "20")
        elif self.name == "毒刃":
            self.description = self.description.replace("5", "7").replace("2", "3")
        elif self.name == "闪避":
            self.description = self.description.replace("8", "11")
        elif self.name == "致命毒素":
            self.description = self.description.replace("5", "7")
        elif self.name == "刀刃之舞":
            self.description = self.description.replace("4", "6")
        elif self.name == "闪电球" or self.name == "冰霜球":
            self.description = self.description.replace("1", "2")
        elif self.name == "双重施法":
            self.description = self.description.replace("下一张", "下两张")
        elif self.name == "自我修复":
            self.description = self.description.replace("3", "5")
        elif self.name == "火球术":
            self.description = self.description.replace("10", "14")
        elif self.name == "血肉奉献":
            self.description = self.description.replace("8", "10")
        elif self.name == "狂暴打击":
            self.description = self.description.replace("8", "10")
        elif self.name == "战斗呐喊":
            self.description = self.description.replace("1", "2")
        elif self.name == "暗影步伐":
            self.description = self.description.replace("6", "8")
        elif self.name == "毒雾弹":
            self.description = self.description.replace("4", "5").replace("3", "4")
        elif self.name == "伏击":
            self.description = self.description.replace("4", "6")
        elif self.name == "能量涌动":
            self.description = self.description.replace("2", "3")
        elif self.name == "核心过载":
            self.description = self.description.replace("1", "2")
        elif self.name == "数据分析":
            self.description = self.description.replace("3", "4")
            
        return True
        
    def play(self, player, targets=None):
        """打出卡牌"""
        # 检查能量是否足够
        if player.energy < self.cost:
            return False, "能量不足!"
        
        # 消耗能量
        player.energy -= self.cost
        
        # 根据卡牌类型和名称执行不同效果
        result = self._execute_card_effect(player, targets)
        
        # 处理双重施法效果
        if player.double_cast and self.card_type == "Skill":
            player.double_cast_count -= 1
            if player.double_cast_count <= 0:
                player.double_cast = False
            result = self._execute_card_effect(player, targets)
            
        # 处理虚无属性
        if self.ethereal:
            self.exhausted = True
            
        return True, result
        
    def _execute_card_effect(self, player, targets=None):
        """执行卡牌效果"""
        # 基础卡牌
        if self.name == "打击":
            if not targets or len(targets) == 0:
                return "需要选择目标!"
                
            damage = 6 if not self.upgraded else 9
            damage += player.strength
            target = targets[0]
            target.take_damage(damage)
            return f"对 {target.name} 造成 {damage} 点伤害!"
            
        elif self.name == "防御":
            block = 5 if not self.upgraded else 8
            block += player.dexterity
            player.block += block
            return f"获得 {block} 点格挡!"
            
        # 铁甲战士卡牌
        elif self.name == "愤怒":
            strength = 3 if not self.upgraded else 5
            player.temporary_strength += strength
            return f"获得 {strength} 点临时力量!"
            
        elif self.name == "重击":
            if not targets or len(targets) == 0:
                return "需要选择目标!"
                
            damage = 14 if not self.upgraded else 18
            damage += player.strength
            target = targets[0]
            target.take_damage(damage)
            return f"对 {target.name} 造成 {damage} 点伤害!"
            
        elif self.name == "铁斩波":
            if not targets or len(targets) == 0:
                return "需要选择目标!"
                
            damage = 8 if not self.upgraded else 12
            damage += player.strength
            target = targets[0]
            target.take_damage(damage)
            return f"对 {target.name} 造成 {damage} 点伤害!"
            
        elif self.name == "顺势斩":
            if not targets or len(targets) == 0:
                return "需要选择目标!"
                
            base_damage = 12 if not self.upgraded else 16
            bonus_damage = 4 if not self.upgraded else 4
            damage = base_damage + player.strength
            
            if player.block > 0:
                damage += bonus_damage
                
            target = targets[0]
            target.take_damage(damage)
            
            if player.block > 0:
                return f"你有格挡! 对 {target.name} 造成 {damage} 点伤害!"
            else:
                return f"对 {target.name} 造成 {damage} 点伤害!"
                
        # 静默猎手卡牌
        elif self.name == "毒刃":
            if not targets or len(targets) == 0:
                return "需要选择目标!"
                
            damage = 5 if not self.upgraded else 7
            damage += player.strength
            poison = 2 if not self.upgraded else 3
            
            target = targets[0]
            target.take_damage(damage)
            target.poison += poison
            
            return f"对 {target.name} 造成 {damage} 点伤害并给予 {poison} 层中毒!"
            
        elif self.name == "闪避":
            block = 8 if not self.upgraded else 11
            block += player.dexterity
            player.block += block
            
            # 抽一张牌
            player.draw_cards(1)
            
            return f"获得 {block} 点格挡并抽1张牌!"
            
        elif self.name == "致命毒素":
            if not targets or len(targets) == 0:
                return "需要选择目标!"
                
            poison = 5 if not self.upgraded else 7
            target = targets[0]
            target.poison += poison
            
            return f"给予 {target.name} {poison} 层中毒!"
            
        elif self.name == "刀刃之舞":
            damage = 4 if not self.upgraded else 6
            damage += player.strength
            
            total_damage = 0
            for target in player.current_enemies:
                if target.current_hp > 0:
                    target.take_damage(damage)
                    target.take_damage(damage)
                    total_damage += damage * 2
                    
            return f"对所有敌人造成 {damage} 点伤害两次，共 {total_damage} 点伤害!"
            
        # 故障机器人卡牌
        elif self.name == "闪电球":
            count = 1 if not self.upgraded else 2
            for _ in range(count):
                player.add_orb(Orb("Lightning", 3, 8))
            
            return f"生成 {count} 个闪电充能球!"
            
        elif self.name == "冰霜球":
            count = 1 if not self.upgraded else 2
            for _ in range(count):
                player.add_orb(Orb("Frost", 2, 5))
            
            return f"生成 {count} 个冰霜充能球!"
            
        elif self.name == "双重施法":
            player.double_cast = True
            player.double_cast_count = 1 if not self.upgraded else 2
            
            return f"本回合你的下{'一' if not self.upgraded else '两'}张技能牌打出两次!"
            
        elif self.name == "自我修复":
            heal_per_turn = 3 if not self.upgraded else 5
            player.end_turn_heal += heal_per_turn
            
            return f"每回合结束时回复 {heal_per_turn} 点生命!"
            
        elif self.name == "火球术":
            damage = 10 if not self.upgraded else 14
            damage += player.strength
            
            total_damage = 0
            for target in player.current_enemies:
                if target.current_hp > 0:
                    target.take_damage(damage)
                    total_damage += damage
                    
            return f"对所有敌人造成 {damage} 点伤害，共 {total_damage} 点伤害!"
            
        # 新增铁甲战士卡牌
        elif self.name == "血肉奉献":
            # 失去生命
            player.current_hp -= 3
            if player.current_hp < 1:
                player.current_hp = 1
            
            # 获得格挡
            block = 8 if not self.upgraded else 10
            block += player.dexterity
            player.block += block
            
            # 抽一张牌
            player.draw_cards(1)
            
            return f"失去3点生命，获得{block}点格挡并抽1张牌!"
            
        elif self.name == "狂暴打击":
            if not targets or len(targets) == 0:
                return "需要选择目标!"
                
            base_damage = 8 if not self.upgraded else 10
            # 力量加成翻倍
            damage = base_damage + (player.strength * 2)
            
            target = targets[0]
            target.take_damage(damage)
            
            return f"对 {target.name} 造成 {damage} 点伤害! (力量加成翻倍)"
            
        elif self.name == "战斗呐喊":
            # 添加一个效果，每当打出攻击牌时获得力量
            strength_per_attack = 1 if not self.upgraded else 2
            player.strength_per_attack += strength_per_attack
            
            return f"每当你打出一张攻击牌，获得{strength_per_attack}点力量!"
            
        # 新增静默猎手卡牌
        elif self.name == "暗影步伐":
            # 获得格挡
            block = 6 if not self.upgraded else 8
            block += player.dexterity
            player.block += block
            
            # 丢弃一张牌
            if player.hand:
                # 这里简化处理，直接丢弃第一张牌
                discarded_card = player.hand.pop(0)
                player.discard_pile.append(discarded_card)
                
                # 如果丢弃的是技能牌，抽两张牌
                if discarded_card.card_type == "Skill":
                    player.draw_cards(2)
                    return f"获得{block}点格挡，丢弃了{discarded_card.name}并抽2张牌!"
                else:
                    return f"获得{block}点格挡，丢弃了{discarded_card.name}!"
            else:
                return f"获得{block}点格挡，但没有牌可以丢弃!"
                
        elif self.name == "毒雾弹":
            # 给予所有敌人中毒
            initial_poison = 4 if not self.upgraded else 5
            next_turn_poison = 3 if not self.upgraded else 4
            
            for target in player.current_enemies:
                if target.current_hp > 0:
                    target.poison += initial_poison
            
            # 设置下回合开始时的效果
            player.next_turn_effects.append(
                lambda p: self._apply_delayed_poison(p, next_turn_poison)
            )
            
            return f"给予所有敌人{initial_poison}层中毒，在下回合开始时再给予所有敌人{next_turn_poison}层中毒!"
            
        elif self.name == "伏击":
            if not targets or len(targets) == 0:
                return "需要选择目标!"
                
            target = targets[0]
            base_damage = 4 if not self.upgraded else 6
            damage = base_damage + player.strength
            
            # 对目标造成伤害
            target.take_damage(damage)
            
            # 如果目标有中毒，再造成一次伤害
            if target.poison > 0:
                target.take_damage(damage)
                return f"对{target.name}造成{damage}点伤害两次! (目标已中毒)"
            else:
                return f"对{target.name}造成{damage}点伤害!"
                
        # 新增故障机器人卡牌
        elif self.name == "能量涌动":
            # 获得能量
            energy_gain = 2 if not self.upgraded else 3
            player.energy += energy_gain
            
            # 添加晕眩到弃牌堆
            # 这里简化处理，直接创建一个"晕眩"卡牌
            dazed_card = Card(
                id=999,
                name="晕眩",
                card_type="Status",
                rarity="Common",
                energy_cost=0,
                description="无法打出。回合结束时消耗。",
                character_id=None,
                upgraded=False
            )
            dazed_card.ethereal = True
            player.discard_pile.append(dazed_card)
            
            return f"获得{energy_gain}点能量，将1张晕眩加入你的弃牌堆!"
            
        elif self.name == "核心过载":
            # 设置每回合获得随机充能球的效果
            orbs_per_turn = 1 if not self.upgraded else 2
            player.orbs_per_turn += orbs_per_turn
            
            return f"每回合开始时，获得{orbs_per_turn}个随机充能球!"
            
        elif self.name == "数据分析":
            # 查看抽牌堆顶部的牌
            view_count = 3 if not self.upgraded else 4
            
            if len(player.draw_pile) < view_count:
                return f"抽牌堆中的牌不足{view_count}张!"
                
            # 这里简化处理，直接从抽牌堆顶部抽一张牌
            card = player.draw_pile.pop(0)
            player.hand.append(card)
            
            return f"查看了抽牌堆顶部的{view_count}张牌，选择了{card.name}加入手牌!"
            
        return "卡牌效果未实现!"
        
    def _apply_delayed_poison(self, player, poison_amount):
        """应用延迟中毒效果"""
        for target in player.current_enemies:
            if target.current_hp > 0:
                target.poison += poison_amount
        return f"给予所有敌人{poison_amount}层中毒!"
        
    @staticmethod
    def get_card_by_id(card_id):
        """根据ID获取卡牌"""
        con = duckdb.connect(DB_PATH)
        result = con.execute(
            "SELECT * FROM cards WHERE id = ?",
            [card_id]
        ).fetchone()
        con.close()
        
        if not result:
            return None
            
        return Card(
            id=result[0],
            name=result[1],
            card_type=result[2],
            rarity=result[3],
            energy_cost=result[4],
            description=result[5],
            character_id=result[6],
            upgraded=False
        )


class Orb:
    """充能球类"""
    def __init__(self, orb_type, passive_value=None, evoke_value=None):
        self.orb_type = orb_type
        
        # 设置默认值
        if passive_value is None:
            if orb_type == "Lightning":
                passive_value = 3
            elif orb_type == "Frost":
                passive_value = 2
        
        if evoke_value is None:
            if orb_type == "Lightning":
                evoke_value = 8
            elif orb_type == "Frost":
                evoke_value = 5
                
        self.passive_value = passive_value
        self.evoke_value = evoke_value
    
    def to_dict(self):
        """将充能球序列化为字典"""
        return {
            'orb_type': self.orb_type,
            'passive_value': self.passive_value,
            'evoke_value': self.evoke_value
        }
    
    def passive_effect(self, player, enemies=None):
        """充能球的被动效果"""
        if self.orb_type == "Lightning":
            if enemies and enemies[0].current_hp > 0:
                target = random.choice([e for e in enemies if e.current_hp > 0])
                damage = self.passive_value
                target.take_damage(damage)
                return f"闪电球对 {target.name} 造成 {damage} 点伤害"
        elif self.orb_type == "Frost":
            block = self.passive_value
            player.block += block
            return f"冰霜球给予 {block} 点格挡"
        return None
    
    def evoke(self, player, enemies=None):
        """触发充能球效果"""
        if self.orb_type == "Lightning":
            if enemies and enemies[0].current_hp > 0:
                target = random.choice([e for e in enemies if e.current_hp > 0])
                damage = self.evoke_value
                target.take_damage(damage)
                return f"闪电球被触发，对 {target.name} 造成 {damage} 点伤害"
        elif self.orb_type == "Frost":
            block = self.evoke_value
            player.block += block
            return f"冰霜球被触发，给予 {block} 点格挡"
        return None


class Character:
    """角色类"""
    def __init__(self, id, name, max_hp, starting_gold, description):
        self.id = id
        self.name = name
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.gold = starting_gold
        self.description = description
        self.energy = 3
        self.max_energy = 3
        self.block = 0
        self.strength = 0
        self.dexterity = 0
        self.cards = []
        self.relics = []
        self.potions = []  # 药水列表
        self.max_potions = 3  # 最大药水数量
        self.draw_pile = []
        self.hand = []
        self.discard_pile = []
        self.exhaust_pile = []
        # 充能球系统
        self.orb_slots = 3
        self.orbs = []
        # 双重施法效果
        self.double_cast = False
        self.double_cast_count = 0
        # 临时力量
        self.temporary_strength = 0
        # 每回合回复生命
        self.end_turn_heal = 0
        # 每打出攻击牌获得力量
        self.strength_per_attack = 0
        # 下回合开始时的效果
        self.next_turn_effects = []
        # 每回合获得的随机充能球数量
        self.orbs_per_turn = 0
        # 当前敌人引用，用于遗物效果
        self.current_enemies = []

    @classmethod
    def load_from_db(cls, character_id):
        """从数据库加载角色"""
        con = duckdb.connect(DB_PATH)
        result = con.execute(
            "SELECT * FROM characters WHERE id = ?", 
            [character_id]
        ).fetchone()
        
        if not result:
            con.close()
            raise ValueError(f"角色ID {character_id} 不存在")
        
        character = cls(
            id=result[0],
            name=result[1],
            max_hp=result[2],
            starting_gold=result[3],
            description=result[4]
        )
        
        # 加载初始卡牌
        cards = con.execute(
            "SELECT * FROM cards WHERE character_id = ? AND is_starter = TRUE",
            [character_id]
        ).fetchall()
        
        for card_data in cards:
            card = Card(
                id=card_data[0],
                name=card_data[1],
                card_type=card_data[2],
                rarity=card_data[3],
                energy_cost=card_data[4],
                description=card_data[5],
                character_id=card_data[6]
            )
            # 每张初始卡牌添加5张到牌组
            for _ in range(5 if card.name == "打击" or card.name == "防御" else 1):
                character.cards.append(card)
        
        # 加载初始遗物
        relics = con.execute(
            "SELECT * FROM relics WHERE character_id = ? AND rarity = 'Starter'",
            [character_id]
        ).fetchall()
        
        for relic_data in relics:
            relic = Relic(
                id=relic_data[0],
                name=relic_data[1],
                rarity=relic_data[2],
                description=relic_data[3],
                character_id=relic_data[4]
            )
            character.relics.append(relic)
        
        con.close()
        return character
    
    def heal(self, amount):
        """回复生命值"""
        if amount <= 0:
            return
        
        self.current_hp = min(self.max_hp, self.current_hp + amount)
    
    def take_damage(self, amount):
        """受到伤害"""
        if amount <= 0:
            return 0
        
        actual_damage = max(0, amount - self.block)
        self.block = max(0, self.block - amount)
        
        if actual_damage > 0:
            self.current_hp = max(0, self.current_hp - actual_damage)
        
        return actual_damage
    
    def draw_cards(self, count):
        """抽取指定数量的卡牌"""
        for _ in range(count):
            if not self.draw_pile and not self.discard_pile:
                break  # 没有牌可抽了
            
            if not self.draw_pile:
                # 重洗弃牌堆
                self.draw_pile = self.discard_pile
                self.discard_pile = []
                random.shuffle(self.draw_pile)
            
            if self.draw_pile:
                self.hand.append(self.draw_pile.pop(0))
    
    def add_orb(self, orb):
        """添加充能球"""
        if len(self.orbs) >= self.orb_slots:
            # 如果充能球槽已满，移除第一个球并触发其效果
            self.evoke_first_orb()
        
        self.orbs.append(orb)
    
    def evoke_first_orb(self):
        """触发第一个充能球"""
        if self.orbs:
            orb = self.orbs.pop(0)
            return orb.evoke(self, self.current_enemies)
        return None


class Enemy:
    """敌人类"""
    def __init__(self, id, name, hp, is_elite=False, is_boss=False):
        self.id = id
        self.name = name
        self.max_hp = hp
        self.current_hp = hp
        self.is_elite = is_elite
        self.is_boss = is_boss
        self.intent = "Attack"  # 意图：Attack, Defend, Buff
        self.intent_value = 0   # 意图值（伤害/格挡/增益）
        self.block = 0
        self.strength = 0
        self.poison = 0
    
    def to_dict(self):
        """将敌人序列化为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'health': self.current_hp,
            'maxHealth': self.max_hp,
            'block': self.block,
            'strength': self.strength,
            'isElite': self.is_elite,
            'isBoss': self.is_boss,
            'intent': self.intent,
            'intentValue': self.intent_value,
            'poison': self.poison
        }
    
    def take_damage(self, amount):
        """受到伤害"""
        if amount <= 0:
            return 0
        
        actual_damage = max(0, amount - self.block)
        self.block = max(0, self.block - amount)
        
        if actual_damage > 0:
            self.current_hp = max(0, self.current_hp - actual_damage)
        
        return actual_damage
    
    def get_intent_description(self):
        """获取意图描述"""
        if self.intent == "Attack":
            return f"攻击 ({self.intent_value})"
        elif self.intent == "Defend":
            return f"防御 ({self.intent_value})"
        elif self.intent == "Buff":
            return f"增益 ({self.intent_value})"
        return "未知"


class Relic:
    """遗物类"""
    def __init__(self, id, name, rarity, description, character_id=None):
        self.id = id
        self.name = name
        self.rarity = rarity
        self.description = description
        self.character_id = character_id
    
    def to_dict(self):
        """将遗物序列化为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'rarity': self.rarity,
            'description': self.description,
            'character_id': self.character_id
        }
    
    def on_pickup(self, player):
        """拾取遗物时触发"""
        return None


class Potion:
    """药水类"""
    def __init__(self, id, name, rarity, description, effect_value=0):
        self.id = id
        self.name = name
        self.rarity = rarity
        self.description = description
        self.effect_value = effect_value
    
    def to_dict(self):
        """将药水序列化为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'rarity': self.rarity,
            'description': self.description,
            'effect_value': self.effect_value
        }
    
    def use(self, player, targets=None):
        """使用药水"""
        # 根据药水名称执行不同效果
        if self.name == "力量药水":
            player.strength += self.effect_value
            return f"获得 {self.effect_value} 点力量!"
        elif self.name == "敏捷药水":
            player.dexterity += self.effect_value
            return f"获得 {self.effect_value} 点敏捷!"
        elif self.name == "治疗药水":
            heal_amount = self.effect_value
            player.heal(heal_amount)
            return f"回复 {heal_amount} 点生命!"
        elif self.name == "能量药水":
            player.energy += self.effect_value
            return f"获得 {self.effect_value} 点能量!"
        elif self.name == "火焰药水":
            if not targets or len(targets) == 0:
                return "需要选择目标!"
            damage = self.effect_value
            target = targets[0]
            target.take_damage(damage)
            return f"对 {target.name} 造成 {damage} 点伤害!"
        elif self.name == "毒药水":
            if not targets or len(targets) == 0:
                return "需要选择目标!"
            poison = self.effect_value
            target = targets[0]
            target.poison += poison
            return f"给予 {target.name} {poison} 层中毒!"
        elif self.name == "烟雾弹":
            block = self.effect_value
            player.block += block
            return f"获得 {block} 点格挡!"
        elif self.name == "恐惧药水":
            if not targets or len(targets) == 0:
                return "需要选择目标!"
            target = targets[0]
            target.strength -= self.effect_value
            return f"{target.name} 失去 {self.effect_value} 点力量!"
        elif self.name == "抽牌药水":
            player.draw_cards(self.effect_value)
            return f"抽 {self.effect_value} 张牌!"
        elif self.name == "弱化药水":
            if not targets or len(targets) == 0:
                return "需要选择目标!"
            target = targets[0]
            target.strength -= self.effect_value
            return f"{target.name} 失去 {self.effect_value} 点力量!"
        
        return "药水效果未实现!"


class GameState:
    """游戏状态类"""
    def __init__(self):
        self.player = None
        self.floor = 1
        self.current_enemies = []
        self.in_combat = False
        self.game_over = False
        self.rewards = {}  # 奖励
        self.current_event = None  # 当前事件
        self.screen = 'map'  # 当前界面
        self.shop_prices = {}  # 商店价格
    
    def new_game(self, character_id, player_name):
        """创建新游戏"""
        # 加载角色
        self.player = Character.load_from_db(character_id)
        
        # 初始化游戏状态
        self.floor = 1
        self.current_enemies = []
        self.in_combat = False
        self.game_over = False
        
        # 洗牌
        self.player.cards = self.player.cards.copy()
        random.shuffle(self.player.cards)
        
        # 初始化牌堆
        self.player.draw_pile = self.player.cards.copy()
        self.player.hand = []
        self.player.discard_pile = []
        self.player.exhaust_pile = []
        
        # 初始化药水
        self.player.potions = []
        
        # 保存游戏
        self.save_game(player_name)
        
        return self
    
    def start_combat(self, enemy_count=1, is_elite=False, is_boss=False):
        """开始战斗"""
        self.in_combat = True
        
        # 根据当前楼层确定敌人所在的章节
        act = 1
        if self.floor > 17:
            act = 3
        elif self.floor > 8:
            act = 2
        
        # 使用新的敌人生成系统
        self.current_enemies = self.get_random_enemy(is_elite=is_elite, is_boss=is_boss, act=act)
        
        # 设置玩家初始状态
        self.player.energy = self.player.max_energy
        self.player.block = 0
        
        # 抽初始手牌
        self.player.hand = []
        self.player.draw_cards(5)
        
        # 将当前敌人引用传递给玩家，用于遗物效果
        self.player.current_enemies = self.current_enemies
        
        return True
    
    def _set_enemy_intent(self, enemy):
        """设置敌人意图"""
        intents = ["Attack", "Defend", "Buff"]
        weights = [70, 20, 10]
        
        intent = random.choices(intents, weights=weights)[0]
        enemy.intent = intent
        
        if intent == "Attack":
            if enemy.is_boss:
                enemy.intent_value = random.randint(15, 25)
            elif enemy.is_elite:
                enemy.intent_value = random.randint(10, 18)
            else:
                enemy.intent_value = random.randint(5, 12)
        elif intent == "Defend":
            if enemy.is_boss:
                enemy.intent_value = random.randint(12, 20)
            elif enemy.is_elite:
                enemy.intent_value = random.randint(8, 15)
            else:
                enemy.intent_value = random.randint(5, 10)
        elif intent == "Buff":
            enemy.intent_value = random.randint(1, 3)
    
    def update_stats(self, stat_name, value=1):
        """更新游戏统计信息"""
        # 统计信息字段列表
        stats_fields = [
            "battles_won", "battles_lost", "elites_killed", "bosses_killed",
            "cards_obtained", "cards_upgraded", "relics_obtained", 
            "gold_collected", "damage_dealt", "damage_taken"
        ]
        
        # 如果是有效的统计字段，更新它
        if stat_name in stats_fields:
            if not hasattr(self, 'stats'):
                self.stats = {field: 0 for field in stats_fields}
            
            self.stats[stat_name] = self.stats.get(stat_name, 0) + value
            return True
        
        return False
    
    def get_random_enemy(self, is_elite=False, is_boss=False, act=1):
        """获取随机敌人"""
        # 根据不同章节和类型返回不同的敌人
        if is_boss:
            if act == 1:
                return self._create_boss_hexaghost()
            elif act == 2:
                return self._create_boss_collector()
            elif act == 3:
                return self._create_boss_time_eater()
            else:
                return self._create_boss_heart()
        elif is_elite:
            if act == 1:
                elite_types = ["Gremlin Nob", "Lagavulin", "Sentries"]
            elif act == 2:
                elite_types = ["Slavers", "Book of Stabbing", "Gremlin Leader"]
            else:
                elite_types = ["Giant Head", "Nemesis", "Reptomancer"]
                
            elite_type = random.choice(elite_types)
            return self._create_elite_enemy(elite_type)
        else:
            # 普通敌人
            if act == 1:
                enemy_types = [
                    "Cultist", "Jaw Worm", "Louse", "Acid Slime", "Spike Slime", 
                    "Fungi Beast", "Gremlin Gang"
                ]
            elif act == 2:
                enemy_types = [
                    "Spheric Guardian", "Chosen", "Byrd", "Snecko", 
                    "Snake Plant", "Centurion & Mystic", "Shelled Parasite"
                ]
            else:
                enemy_types = [
                    "Darkling", "Orb Walker", "Spire Growth", "Transient", 
                    "Writhing Mass", "Maw", "Jaw Worm Horde"
                ]
                
            enemy_type = random.choice(enemy_types)
            return self._create_normal_enemy(enemy_type)
    
    def _create_normal_enemy(self, enemy_type):
        """创建普通敌人"""
        enemies = []
        
        if enemy_type == "Cultist":
            enemy = Enemy(
                id=1,
                name="邪教徒",
                hp=random.randint(45, 50),
                is_elite=False,
                is_boss=False
            )
            enemy.intent = "Buff"
            enemy.intent_value = 3
            enemies.append(enemy)
            
        elif enemy_type == "Jaw Worm":
            enemy = Enemy(
                id=2,
                name="颚虫",
                hp=random.randint(40, 44),
                is_elite=False,
                is_boss=False
            )
            enemy.strength = 3
            enemies.append(enemy)
            
        elif enemy_type == "Louse":
            # 50%几率是红色或绿色虱子
            louse_type = random.choice(["红色", "绿色"])
            enemy = Enemy(
                id=3,
                name=f"{louse_type}虱子",
                hp=random.randint(10, 15) if louse_type == "绿色" else random.randint(12, 18),
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Acid Slime":
            size = random.choice(["小", "中", "大"])
            hp_range = {"小": (8, 12), "中": (28, 32), "大": (65, 70)}
            enemy = Enemy(
                id=4,
                name=f"{size}型酸液史莱姆",
                hp=random.randint(*hp_range[size]),
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Spike Slime":
            size = random.choice(["小", "中", "大"])
            hp_range = {"小": (10, 14), "中": (28, 32), "大": (65, 70)}
            enemy = Enemy(
                id=5,
                name=f"{size}型尖刺史莱姆",
                hp=random.randint(*hp_range[size]),
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Fungi Beast":
            enemy = Enemy(
                id=6,
                name="真菌兽",
                hp=random.randint(22, 28),
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Gremlin Gang":
            # 随机选择4个不同的小鬼
            gremlin_types = ["疯狂", "盗贼", "胖", "巫师", "护盾"]
            selected_gremlins = random.sample(gremlin_types, min(4, len(gremlin_types)))
            
            for i, gremlin_type in enumerate(selected_gremlins):
                hp_range = {
                    "疯狂": (20, 24),
                    "盗贼": (10, 14),
                    "胖": (14, 18),
                    "巫师": (10, 14),
                    "护盾": (12, 15)
                }
                enemy = Enemy(
                    id=7 + i,
                    name=f"{gremlin_type}小鬼",
                    hp=random.randint(*hp_range[gremlin_type]),
                    is_elite=False,
                    is_boss=False
                )
                enemies.append(enemy)
                
        elif enemy_type == "Spheric Guardian":
            enemy = Enemy(
                id=11,
                name="球形守卫",
                hp=random.randint(60, 65),
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Chosen":
            enemy = Enemy(
                id=12,
                name="天选者",
                hp=random.randint(95, 103),
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Byrd":
            # 随机1-3只飞鸟
            num_byrds = random.randint(1, 3)
            for i in range(num_byrds):
                enemy = Enemy(
                    id=13 + i,
                    name="飞鸟",
                    hp=random.randint(25, 29),
                    is_elite=False,
                    is_boss=False
                )
                enemies.append(enemy)
                
        elif enemy_type == "Snecko":
            enemy = Enemy(
                id=16,
                name="异蛇",
                hp=random.randint(114, 120),
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Snake Plant":
            enemy = Enemy(
                id=17,
                name="蛇形草",
                hp=random.randint(75, 82),
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Centurion & Mystic":
            enemy1 = Enemy(
                id=18,
                name="百夫长",
                hp=random.randint(76, 80),
                is_elite=False,
                is_boss=False
            )
            enemy2 = Enemy(
                id=19,
                name="秘术师",
                hp=random.randint(48, 52),
                is_elite=False,
                is_boss=False
            )
            enemies.extend([enemy1, enemy2])
            
        elif enemy_type == "Shelled Parasite":
            enemy = Enemy(
                id=20,
                name="硬壳寄生虫",
                hp=random.randint(68, 72),
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Darkling":
            # 随机2-3只暗黑物
            num_darklings = random.randint(2, 3)
            for i in range(num_darklings):
                enemy = Enemy(
                    id=21 + i,
                    name="暗黑物",
                    hp=random.randint(48, 52),
                    is_elite=False,
                    is_boss=False
                )
                enemies.append(enemy)
                
        elif enemy_type == "Orb Walker":
            enemy = Enemy(
                id=24,
                name="球体行者",
                hp=random.randint(90, 96),
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Spire Growth":
            enemy = Enemy(
                id=25,
                name="尖塔滋长物",
                hp=random.randint(170, 175),
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Transient":
            enemy = Enemy(
                id=26,
                name="瞬身人",
                hp=999,  # 特殊敌人，几回合后会消失
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Writhing Mass":
            enemy = Enemy(
                id=27,
                name="蠕动之物",
                hp=random.randint(160, 165),
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Maw":
            enemy = Enemy(
                id=28,
                name="巨口",
                hp=random.randint(300, 305),
                is_elite=False,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif enemy_type == "Jaw Worm Horde":
            # 3只颚虫
            for i in range(3):
                enemy = Enemy(
                    id=29 + i,
                    name="颚虫",
                    hp=random.randint(40, 44),
                    is_elite=False,
                    is_boss=False
                )
                enemy.strength = 3
                enemies.append(enemy)
        
        # 为每个敌人设置意图
        for enemy in enemies:
            if not enemy.intent:
                self._set_enemy_intent(enemy)
                
        return enemies
    
    def _create_elite_enemy(self, elite_type):
        """创建精英敌人"""
        enemies = []
        
        if elite_type == "Gremlin Nob":
            enemy = Enemy(
                id=32,
                name="小鬼头目",
                hp=random.randint(82, 86),
                is_elite=True,
                is_boss=False
            )
            enemy.strength = 2
            enemies.append(enemy)
            
        elif elite_type == "Lagavulin":
            enemy = Enemy(
                id=33,
                name="拉加弗林",
                hp=random.randint(109, 112),
                is_elite=True,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif elite_type == "Sentries":
            # 3个哨卫
            for i in range(3):
                enemy = Enemy(
                    id=34 + i,
                    name="哨卫",
                    hp=random.randint(38, 42),
                    is_elite=True,
                    is_boss=False
                )
                enemies.append(enemy)
                
        elif elite_type == "Slavers":
            # 蓝色、红色和任务奴隶主
            enemy1 = Enemy(
                id=37,
                name="蓝色奴隶主",
                hp=random.randint(46, 50),
                is_elite=True,
                is_boss=False
            )
            enemy2 = Enemy(
                id=38,
                name="红色奴隶主",
                hp=random.randint(54, 58),
                is_elite=True,
                is_boss=False
            )
            enemy3 = Enemy(
                id=39,
                name="任务奴隶主",
                hp=random.randint(48, 52),
                is_elite=True,
                is_boss=False
            )
            enemies.extend([enemy1, enemy2, enemy3])
            
        elif elite_type == "Book of Stabbing":
            enemy = Enemy(
                id=40,
                name="刺击之书",
                hp=random.randint(160, 170),
                is_elite=True,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif elite_type == "Gremlin Leader":
            # 小鬼首领和两个随机小鬼
            leader = Enemy(
                id=41,
                name="小鬼首领",
                hp=random.randint(140, 148),
                is_elite=True,
                is_boss=False
            )
            enemies.append(leader)
            
            gremlin_types = ["疯狂", "盗贼", "胖", "巫师", "护盾"]
            selected_gremlins = random.sample(gremlin_types, 2)
            
            for i, gremlin_type in enumerate(selected_gremlins):
                hp_range = {
                    "疯狂": (20, 24),
                    "盗贼": (10, 14),
                    "胖": (14, 18),
                    "巫师": (10, 14),
                    "护盾": (12, 15)
                }
                enemy = Enemy(
                    id=42 + i,
                    name=f"{gremlin_type}小鬼",
                    hp=random.randint(*hp_range[gremlin_type]),
                    is_elite=True,
                    is_boss=False
                )
                enemies.append(enemy)
                
        elif elite_type == "Giant Head":
            enemy = Enemy(
                id=44,
                name="巨型头颅",
                hp=random.randint(500, 520),
                is_elite=True,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif elite_type == "Nemesis":
            enemy = Enemy(
                id=45,
                name="复仇女神",
                hp=random.randint(185, 200),
                is_elite=True,
                is_boss=False
            )
            enemies.append(enemy)
            
        elif elite_type == "Reptomancer":
            # 爬行法师和两个飞刀
            enemy1 = Enemy(
                id=46,
                name="爬行法师",
                hp=random.randint(180, 190),
                is_elite=True,
                is_boss=False
            )
            enemies.append(enemy1)
            
            for i in range(2):
                enemy = Enemy(
                    id=47 + i,
                    name="飞刀",
                    hp=random.randint(20, 25),
                    is_elite=True,
                    is_boss=False
                )
                enemies.append(enemy)
        
        # 为每个敌人设置意图
        for enemy in enemies:
            if not enemy.intent:
                self._set_enemy_intent(enemy)
                
        return enemies
    
    def _create_boss_hexaghost(self):
        """创建第一章Boss：六火亡魂"""
        enemy = Enemy(
            id=49,
            name="六火亡魂",
            hp=random.randint(250, 260),
            is_elite=False,
            is_boss=True
        )
        enemy.intent = "Attack"
        enemy.intent_value = 6 * 2  # 6次2点伤害
        
        return [enemy]
    
    def _create_boss_collector(self):
        """创建第二章Boss：收藏家"""
        enemy = Enemy(
            id=50,
            name="收藏家",
            hp=random.randint(282, 300),
            is_elite=False,
            is_boss=True
        )
        enemy.intent = "Attack"
        enemy.intent_value = 18
        
        return [enemy]
    
    def _create_boss_time_eater(self):
        """创建第三章Boss：时间吞噬者"""
        enemy = Enemy(
            id=51,
            name="时间吞噬者",
            hp=random.randint(456, 480),
            is_elite=False,
            is_boss=True
        )
        enemy.intent = "Attack"
        enemy.intent_value = 25
        
        return [enemy]
    
    def _create_boss_heart(self):
        """创建最终Boss：腐化之心"""
        enemy = Enemy(
            id=52,
            name="腐化之心",
            hp=random.randint(750, 800),
            is_elite=False,
            is_boss=True
        )
        enemy.intent = "Attack"
        enemy.intent_value = 40
        
        return [enemy]
    
    @classmethod
    def load_game(cls, player_name):
        """从数据库加载游戏状态"""
        con = duckdb.connect(DB_PATH)
        
        # 获取存档
        save = con.execute(
            """
            SELECT id, player_name, character_id, current_hp, max_hp, gold, floor
            FROM saves 
            WHERE player_name = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            [player_name]
        ).fetchone()
        
        if not save:
            con.close()
            return None
        
        # 创建游戏状态
        game_state = cls()
        
        # 加载角色
        game_state.player = Character.load_from_db(save[2])
        game_state.player.current_hp = save[3]
        game_state.player.max_hp = save[4]
        game_state.player.gold = save[5]
        game_state.floor = save[6]
        
        # 加载卡组
        cards = con.execute(
            """
            SELECT c.id, c.name, c.type, c.rarity, c.energy_cost, c.description, c.character_id, pc.upgraded
            FROM player_cards pc
            JOIN cards c ON pc.card_id = c.id
            WHERE pc.save_id = ?
            """,
            [save[0]]
        ).fetchall()
        
        game_state.player.cards = []
        for card_data in cards:
            card = Card(
                id=card_data[0],
                name=card_data[1],
                card_type=card_data[2],
                rarity=card_data[3],
                energy_cost=card_data[4],
                description=card_data[5],
                character_id=card_data[6],
                upgraded=card_data[7]
            )
            game_state.player.cards.append(card)
        
        # 加载遗物
        relics = con.execute(
            """
            SELECT r.id, r.name, r.rarity, r.description, r.character_id
            FROM player_relics pr
            JOIN relics r ON pr.relic_id = r.id
            WHERE pr.save_id = ?
            """,
            [save[0]]
        ).fetchall()
        
        game_state.player.relics = []
        for relic_data in relics:
            relic = Relic(
                id=relic_data[0],
                name=relic_data[1],
                rarity=relic_data[2],
                description=relic_data[3],
                character_id=relic_data[4]
            )
            game_state.player.relics.append(relic)
        
        # 加载药水
        potions = con.execute(
            """
            SELECT p.id, p.name, p.rarity, p.description, p.effect_value
            FROM player_potions pp
            JOIN potions p ON pp.potion_id = p.id
            WHERE pp.save_id = ?
            """,
            [save[0]]
        ).fetchall()
        
        game_state.player.potions = []
        for potion_data in potions:
            potion = Potion(
                id=potion_data[0],
                name=potion_data[1],
                rarity=potion_data[2],
                description=potion_data[3],
                effect_value=potion_data[4]
            )
            game_state.player.potions.append(potion)
        
        con.close()
        return game_state
    
    def save_game(self, player_name):
        """保存游戏状态到数据库"""
        if not self.player:
            return False
        
        try:
            con = duckdb.connect(DB_PATH)
            
            # 检查是否已有存档
            existing_save = con.execute(
                "SELECT id FROM saves WHERE player_name = ?",
                [player_name]
            ).fetchone()
            
            # 创建新存档，不更新旧存档
            # 这样可以避免外键约束问题
            con.execute(
                """
                INSERT INTO saves (player_name, character_id, current_hp, max_hp, gold, floor, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                [player_name, self.player.id, self.player.current_hp, self.player.max_hp, self.player.gold, self.floor]
            )
            
            # 获取新创建的存档ID
            save_id = con.execute(
                "SELECT id FROM saves WHERE player_name = ? ORDER BY created_at DESC LIMIT 1",
                [player_name]
            ).fetchone()[0]
            
            # 保存卡组
            for card in self.player.cards:
                con.execute(
                    """
                    INSERT INTO player_cards (save_id, card_id, upgraded)
                    VALUES (?, ?, ?)
                    """,
                    [save_id, card.id, card.upgraded]
                )
            
            # 保存遗物
            for relic in self.player.relics:
                con.execute(
                    """
                    INSERT INTO player_relics (save_id, relic_id)
                    VALUES (?, ?)
                    """,
                    [save_id, relic.id]
                )
            
            # 保存药水
            for potion in self.player.potions:
                con.execute(
                    """
                    INSERT INTO player_potions (save_id, potion_id)
                    VALUES (?, ?)
                    """,
                    [save_id, potion.id]
                )
            
            con.close()
            return True
        except Exception as e:
            print(f"保存游戏出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False