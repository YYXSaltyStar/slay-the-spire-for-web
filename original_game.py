#!/usr/bin/env python3
import os
import sys
import random
import time
from colorama import init, Fore, Back, Style
from pyfiglet import Figlet
from termcolor import colored

from src.models import GameState, Character, Enemy
from src.models import DB_PATH  # 导入数据库路径

# 初始化colorama
init()

# 敌人和角色的emoji表示
EMOJI = {
    # 敌人
    "史莱姆": "🟢",
    "强盗": "👤",
    "精英强盗": "👹",
    "守卫": "🛡️",
    "史莱姆老大": "🟣",
    
    # 角色
    "铁甲战士": "⚔️",
    "静默猎手": "🏹",
    "故障机器人": "🤖",
    
    # 卡牌类型
    "Attack": "⚔️",
    "Skill": "🛡️",
    "Power": "⭐",
    
    # 地图节点
    "普通战斗": "👾",
    "精英战斗": "💀",
    "休息处": "🔥",
    "商店": "💰",
    "宝箱": "📦",
    "未知事件": "❓",
    "Boss": "👑",
    "玩家": "🧙",
    "路径": "➖",
    "上行路径": "↗️",
    "下行路径": "↘️",
    "当前位置": "🟢"
}

# 地图节点类型
NODE_TYPES = ["普通战斗", "精英战斗", "休息处", "商店", "宝箱", "未知事件", "Boss"]
NODE_WEIGHTS = [60, 10, 15, 10, 5, 0, 0]  # 节点类型的权重

class MapNode:
    """地图节点类"""
    def __init__(self, x, y, node_type):
        self.x = x
        self.y = y
        self.node_type = node_type
        self.connections = []  # 连接到的其他节点
        self.visited = False
        self.paths = []  # 记录通过此节点的路径索引
        self.jitter_x = 0  # 节点显示的水平抖动
        self.jitter_y = 0  # 节点显示的垂直抖动
    
    def add_connection(self, node):
        """添加到另一个节点的连接"""
        if node not in self.connections:
            self.connections.append(node)
    
    def get_emoji(self):
        """获取节点的emoji表示"""
        return EMOJI.get(self.node_type, "❓")

class SlayTheSpireGame:
    def __init__(self):
        """初始化游戏"""
        self.game_state = GameState()
        self.player_name = ""
        self.terminal_width = 80
        self.map_nodes = []  # 地图节点列表
        self.current_node = None  # 当前所在节点
        self.map_height = 15  # 地图高度（层数）
        self.map_width = 7   # 每层的节点数
        
        # 加载表情符号
        global EMOJI
        EMOJI = {
            "普通战斗": "👹",
            "精英战斗": "👺",
            "休息处": "🔥",
            "商店": "💰",
            "宝箱": "📦",
            "未知事件": "❓",
            "Boss": "👑",
            "当前位置": "🧙",
            "铁甲战士": "🛡️",
            "静默猎手": "🗡️",
            "故障机器人": "🤖",
            "路径": "➖",
            "上行路径": "↗️",
            "下行路径": "↘️"
        }
        
        # 初始化地图
        self.generate_map()
        
        try:
            self.terminal_width = os.get_terminal_size().columns
            # 限制终端宽度，避免过长的分隔线
            self.terminal_width = min(self.terminal_width, 80)
        except:
            pass
    
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_title(self):
        """打印游戏标题"""
        f = Figlet(font='slant')
        title = f.renderText('Slay The Spire')
        print(Fore.RED + title + Style.RESET_ALL)
        print(Fore.YELLOW + "命令行版本" + Style.RESET_ALL)
        print()
    
    def print_separator(self):
        """打印分隔线"""
        print(Fore.BLUE + "=" * self.terminal_width + Style.RESET_ALL)
    
    def wait_for_key(self):
        """等待按键"""
        try:
        input(Fore.GREEN + "按回车键继续..." + Style.RESET_ALL)
        except EOFError:
            # 如果在管道输入中，直接返回
            pass
    
    def show_main_menu(self):
        """显示主菜单"""
        while True:
            self.clear_screen()
            self.print_title()
            
            print(Fore.CYAN + "主菜单:" + Style.RESET_ALL)
            print("1. 开始新游戏")
            print("2. 加载游戏")
            print("3. 卡牌图鉴")
            print("4. 遗物图鉴")
            print("5. 存档列表")
            print("6. 退出游戏")
            print()
            
            choice = input("> ")
            
            if choice == "1":
                self.start_new_game()
            elif choice == "2":
                self.load_game()
            elif choice == "3":
                self.show_card_collection()
            elif choice == "4":
                self.show_relic_collection()
            elif choice == "5":
                self.show_save_list()
            elif choice == "6":
                print("感谢游玩！")
                break
            else:
                print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
                self.wait_for_key()
    
    def start_new_game(self):
        """开始新游戏"""
        self.clear_screen()
        self.print_title()
        
        print(Fore.CYAN + "请输入你的名字:" + Style.RESET_ALL)
        self.player_name = input("> ")
        
        if not self.player_name:
            self.player_name = "无名英雄"
        
        self.clear_screen()
        self.print_title()
        
        print(Fore.CYAN + "选择你的角色:" + Style.RESET_ALL)
        print(f"1. {EMOJI['铁甲战士']} 铁甲战士 - 平衡型角色，擅长防御和力量提升")
        print(f"2. {EMOJI['静默猎手']} 静默猎手 - 擅长中毒和丢弃牌")
        print(f"3. {EMOJI['故障机器人']} 故障机器人 - 擅长能量操控和充能球")
        print()
        
        while True:
            choice = input("> ")
            
            if choice in ["1", "2", "3"]:
                character_id = int(choice)
                break
            else:
                print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
        
        # 创建新游戏
        self.game_state.new_game(character_id, self.player_name)
        
        # 重新生成地图
        self.generate_map()
        
        # 设置初始节点为第一层的第一个节点
        if self.map_nodes and self.map_nodes[0]:
            self.current_node = self.map_nodes[0][0]
            self.current_node.visited = True
        
        print(Fore.GREEN + f"欢迎，{self.player_name}！你选择了 {self.game_state.player.name}。" + Style.RESET_ALL)
        self.wait_for_key()
        
        # 显示玩家状态
        if self.print_player_status():
            # 如果玩家选择了继续游戏，进入游戏循环
        self.game_loop()
    
    def load_game(self):
        """加载游戏"""
        self.clear_screen()
        self.print_title()
        
        print(Fore.CYAN + "请输入你的存档名:" + Style.RESET_ALL)
        player_name = input("> ")
        
        # 加载游戏
        try:
            game_state = GameState.load_game(player_name)
            
            if game_state:
                self.game_state = game_state
                self.player_name = player_name
                
                # 重新生成地图
                self.generate_map()
                
                # 设置当前节点为第一层的第一个节点
                if self.map_nodes and self.map_nodes[0]:
                    self.current_node = self.map_nodes[0][0]
                    self.current_node.visited = True
                
                print(Fore.GREEN + f"欢迎回来，{player_name}！你的角色是 {self.game_state.player.name}。" + Style.RESET_ALL)
                print(Fore.GREEN + f"当前楼层: {self.game_state.floor}" + Style.RESET_ALL)
            self.wait_for_key()
            
                # 显示玩家状态
                if self.print_player_status():
                    # 如果玩家选择了继续游戏，进入游戏循环
            self.game_loop()
        else:
                print(Fore.RED + f"找不到存档 '{player_name}'。" + Style.RESET_ALL)
            self.wait_for_key()
                self.show_main_menu()
        except Exception as e:
            print(Fore.RED + f"加载游戏失败: {str(e)}" + Style.RESET_ALL)
            import traceback
            traceback.print_exc()
            self.wait_for_key()
            self.show_main_menu()
    
    def game_loop(self):
        """游戏主循环"""
        while not self.game_state.game_over:
            # 检查是否在战斗中
            if self.game_state.in_combat:
                self.combat_loop()
            else:
                # 如果map_screen返回False，表示要返回主菜单
                if not self.map_screen():
                    break
    
    def generate_map(self):
        """生成随机地图，类似于杀戮尖塔原版的地图布局"""
        self.map_nodes = []
        
        # 创建7x15的网格
        grid_width = 7
        grid_height = 15
        
        # 初始化空网格
        grid = [[None for _ in range(grid_width)] for _ in range(grid_height)]
        
        # 定义每层的节点数量
        nodes_per_layer = [3, 4, 3, 4, 3, 3, 2, 3, 1, 3, 2, 3, 1, 2, 1]
        
        # 生成路径
        paths = []
        
        # 第一层的起始点（均匀分布）
        first_layer_positions = [1, 3, 5]  # 在位置1、3、5放置第一层节点
        
        # 为每个起始点创建路径
        for start_x in first_layer_positions:
            # 创建路径
            path = [(0, start_x)]
            current_x = start_x
            
            # 向上延伸路径到顶层
            for y in range(1, grid_height):
                # 根据当前层决定移动策略
                if y < 5:  # 前5层路径分散
                    dx_range = [-1, 0, 1]
                elif y < 10:  # 中间层路径开始收敛
                    dx_range = [-1, 0, 1]
                    # 向中心偏移的概率更高
                    if current_x < grid_width // 2:
                        dx_range = [0, 1]
                    elif current_x > grid_width // 2:
                        dx_range = [-1, 0]
                else:  # 最后几层路径强制收敛
                    if current_x < grid_width // 2:
                        dx_range = [1]
                    elif current_x > grid_width // 2:
                        dx_range = [-1]
                    else:
                        dx_range = [0]
                
                # 可能的下一个位置
                possible_moves = []
                for dx in dx_range:
                    next_x = current_x + dx
                    if 0 <= next_x < grid_width:
                        possible_moves.append(next_x)
                
                if possible_moves:
                    # 随机选择一个可能的移动
                    next_x = random.choice(possible_moves)
                    path.append((y, next_x))
                    current_x = next_x
                else:
                    # 如果没有可能的移动，保持当前位置
                    path.append((y, current_x))
            
            paths.append(path)
        
        # 添加额外的分支路径
        for _ in range(3):  # 添加3条额外分支
            # 选择一条现有路径作为起点
            source_path = random.choice(paths)
            
            # 选择分叉点（第2-5层之间）
            fork_index = random.randint(2, min(5, len(source_path) - 1))
            fork_y, fork_x = source_path[fork_index]
            
            # 创建新路径，从分叉点开始
            new_path = source_path[:fork_index+1]
            current_x = fork_x
            
            # 向上延伸新分支
            for y in range(fork_y + 1, grid_height):
                # 决定移动方向
                if current_x < grid_width // 2:
                    dx_range = [0, 1]
                elif current_x > grid_width // 2:
                    dx_range = [-1, 0]
                else:
                    dx_range = [-1, 1]
                
                # 可能的下一个位置
                possible_moves = []
                for dx in dx_range:
                    next_x = current_x + dx
                    if 0 <= next_x < grid_width:
                        possible_moves.append(next_x)
                
                if possible_moves:
                    # 随机选择一个可能的移动
                    next_x = random.choice(possible_moves)
                    new_path.append((y, next_x))
                    current_x = next_x
                else:
                    # 如果没有可能的移动，保持当前位置
                    new_path.append((y, current_x))
            
            paths.append(new_path)
        
        # 创建节点并添加到网格
        for path_index, path in enumerate(paths):
            for y, x in path:
                if grid[y][x] is None:
                    # 创建新节点
                    node_type = self.get_node_type(y, grid_height)
                    grid[y][x] = MapNode(x, y, node_type)
                
                # 标记此节点属于此路径
                if not hasattr(grid[y][x], 'paths'):
                    grid[y][x].paths = []
                grid[y][x].paths.append(path_index)
        
        # 建立节点之间的连接
        for path_index, path in enumerate(paths):
            for i in range(len(path) - 1):
                y1, x1 = path[i]
                y2, x2 = path[i + 1]
                if grid[y1][x1] and grid[y2][x2]:
                    grid[y1][x1].add_connection(grid[y2][x2])
        
        # 将节点添加到地图中
        for y in range(grid_height):
            layer_nodes = []
            for x in range(grid_width):
                if grid[y][x]:
                    layer_nodes.append(grid[y][x])
            self.map_nodes.append(layer_nodes)
        
        # 添加Boss节点
        boss_node = MapNode(grid_width // 2, grid_height, "Boss")
        boss_layer = [boss_node]
        
        # 连接最后一层的所有节点到Boss
        for node in self.map_nodes[-1]:
            node.add_connection(boss_node)
        
        self.map_nodes.append(boss_layer)
        
        # 设置起始节点
        self.current_node = self.map_nodes[0][0]
        self.current_node.visited = True
        
        return self.map_nodes
    
    def get_node_type(self, y, grid_height):
        """根据位置确定节点类型"""
        if y == 0:
            # 第一层总是普通战斗
            return "普通战斗"
        elif y == grid_height - 1:
            # 最后一层总是休息处
            return "休息处"
        elif y == grid_height // 2:
            # 中间层有宝箱
            return "宝箱"
        else:
            # 其他层随机选择节点类型
            # 不同楼层有不同的权重
            if y < 6:
                # 前6层没有精英和休息处
                weights = [80, 0, 0, 15, 5, 0]  # 普通战斗、精英战斗、休息处、商店、宝箱、未知事件
            else:
                # 6层以后可以有精英和休息处
                weights = [45, 16, 15, 10, 5, 9]  # 普通战斗、精英战斗、休息处、商店、宝箱、未知事件
            
            node_types = ["普通战斗", "精英战斗", "休息处", "商店", "宝箱", "未知事件"]
            return random.choices(node_types, weights=weights)[0]
    
    def display_map(self):
        """显示地图"""
        self.clear_screen()
        self.print_title()
        
        print(Fore.CYAN + "地图:" + Style.RESET_ALL)
        
        # 计算地图显示尺寸
        grid_width = 7
        grid_height = 16  # 包括Boss层
        map_display_height = grid_height * 3
        map_display_width = grid_width * 10
        
        # 创建空白地图
        map_display = [[' ' for _ in range(map_display_width)] for _ in range(map_display_height)]
        
        # 首先绘制连接线，这样节点会覆盖在线上
        for y in range(len(self.map_nodes)):
            layer = self.map_nodes[y]
            for node in layer:
                # 计算节点在显示中的位置
                display_x = int(node.x * 10) + 5
                display_y = node.y * 3
                
                # 绘制连接
                for connected_node in node.connections:
                    # 只绘制向上的连接
                    if connected_node.y > node.y:
                        # 计算连接线的起点和终点
                        start_x = display_x
                        start_y = display_y + 1
                        end_x = int(connected_node.x * 10) + 5
                        end_y = connected_node.y * 3 - 1
                        
                                                 # 绘制连接线 - 使用虚线风格
                        if start_x < end_x:  # 右上方向
                            # 使用虚线连接
                            dx = end_x - start_x
                            dy = end_y - start_y
                            steps = max(dx, dy) * 2  # 增加步数使虚线更密集
                            if steps > 0:
                                for i in range(steps + 1):
                                    # 只在偶数步绘制，形成虚线效果
                                    if i % 2 == 0:
                                        x = int(start_x + (dx * i / steps))
                                        y = int(start_y + (dy * i / steps))
                                        if 0 <= y < map_display_height and 0 <= x < map_display_width:
                                            map_display[y][x] = Fore.LIGHTBLACK_EX + "-" + Style.RESET_ALL
                        
                        elif start_x > end_x:  # 左上方向
                            # 使用虚线连接
                            dx = end_x - start_x
                            dy = end_y - start_y
                            steps = max(abs(dx), dy) * 2  # 增加步数使虚线更密集
                            if steps > 0:
                                for i in range(steps + 1):
                                    # 只在偶数步绘制，形成虚线效果
                                    if i % 2 == 0:
                                        x = int(start_x + (dx * i / steps))
                                        y = int(start_y + (dy * i / steps))
                                        if 0 <= y < map_display_height and 0 <= x < map_display_width:
                                            map_display[y][x] = Fore.LIGHTBLACK_EX + "-" + Style.RESET_ALL
                        
                        else:  # 垂直向上
                            for i in range(end_y - start_y + 1):
                                # 每隔一个位置绘制，形成虚线效果
                                if i % 2 == 0 and start_y + i < map_display_height:
                                    map_display[start_y + i][start_x] = Fore.LIGHTBLACK_EX + "·" + Style.RESET_ALL
        
        # 然后绘制节点，覆盖在连接线上
        for y in range(len(self.map_nodes)):
            layer = self.map_nodes[y]
            for node in layer:
                # 计算节点在显示中的位置
                display_x = int(node.x * 10) + 5
                display_y = node.y * 3
                
                # 绘制节点
                node_emoji = node.get_emoji()
                
                # 如果已访问，加上标记
                if node.visited:
                    node_emoji += "✓"
                
                # 为节点添加样式和边框
                node_style = ""
                
                # 为不同类型节点设置不同样式
                if node.node_type == "普通战斗":
                    node_emoji = Fore.WHITE + node_emoji + Style.RESET_ALL
                elif node.node_type == "精英战斗":
                    node_emoji = Fore.MAGENTA + node_emoji + Style.RESET_ALL
                elif node.node_type == "Boss":
                    node_emoji = Fore.RED + Back.BLACK + node_emoji + Style.RESET_ALL
                elif node.node_type == "休息处":
                    node_emoji = Fore.GREEN + node_emoji + Style.RESET_ALL
                elif node.node_type == "商店":
                    node_emoji = Fore.YELLOW + node_emoji + Style.RESET_ALL
                elif node.node_type == "宝箱":
                    node_emoji = Fore.CYAN + node_emoji + Style.RESET_ALL
                elif node.node_type == "未知事件":
                    node_emoji = Fore.LIGHTBLACK_EX + node_emoji + Style.RESET_ALL
                
                # 如果是当前节点，添加高亮效果
                if node == self.current_node:
                    node_emoji = Back.BLUE + node_emoji + Style.RESET_ALL
                
                # 放置节点emoji
                for i, char in enumerate(node_emoji):
                    if 0 <= display_x + i < map_display_width and display_y < map_display_height:
                        map_display[display_y][display_x + i] = char
        
        # 计算可见区域
        visible_height = min(30, map_display_height)  # 限制高度以适应屏幕
        start_row = 0
        
        # 如果当前节点在地图中，确保它可见
        if self.current_node:
            current_y = self.current_node.y * 3
            if current_y >= visible_height:
                start_row = max(0, current_y - visible_height // 2)
        
        # 打印地图的可见部分
        for i in range(visible_height):
            row_idx = start_row + i
            if row_idx < map_display_height:
                print(''.join(map_display[row_idx]))
        
        # 打印图例
        print("\n" + Fore.YELLOW + "图例:" + Style.RESET_ALL)
        print(f"{Fore.WHITE}{EMOJI['普通战斗']}{Style.RESET_ALL} 普通战斗  {Fore.MAGENTA}{EMOJI['精英战斗']}{Style.RESET_ALL} 精英战斗  {Fore.GREEN}{EMOJI['休息处']}{Style.RESET_ALL} 休息处  {Fore.YELLOW}{EMOJI['商店']}{Style.RESET_ALL} 商店")
        print(f"{Fore.CYAN}{EMOJI['宝箱']}{Style.RESET_ALL} 宝箱  {EMOJI['未知事件']} 未知事件  {Fore.RED}{EMOJI['Boss']}{Style.RESET_ALL} Boss  {EMOJI['当前位置']} 当前位置")
        print(f"路径: {Fore.LIGHTBLACK_EX}· - {Style.RESET_ALL} 虚线连接")
        
        self.print_separator()
        self.wait_for_key()
    
    def map_screen(self):
        """地图/事件选择界面"""
        # 确保地图已初始化
        if not self.map_nodes or not self.current_node:
            self.generate_map()
            
        while True:
        self.clear_screen()
        
        print(Fore.YELLOW + f"楼层: {self.game_state.floor}" + Style.RESET_ALL)
            
            # 显示玩家基本信息
            player = self.game_state.player
            print(f"名称: {self.player_name}")
            print(f"角色: {player.name}")
            print(f"生命: {player.current_hp}/{player.max_hp}")
            print(f"金币: {player.gold}")
            
            # 显示当前位置
            if self.current_node:
                print(f"当前位置: {self.current_node.node_type} {EMOJI.get(self.current_node.node_type, '')}")
                
        self.print_separator()
        
            # 显示可选择的路径
            if self.current_node and self.current_node.connections:
                print(Fore.CYAN + "可选择的路径:" + Style.RESET_ALL)
                for i, node in enumerate(self.current_node.connections, 1):
                    print(f"{i}. {node.node_type} {EMOJI[node.node_type]}")
                print()
            
        print(Fore.CYAN + "你可以选择:" + Style.RESET_ALL)
            if self.current_node and self.current_node.connections:
                print("1-9. 选择路径")
            print("A. 遭遇战斗")
            print("R. 休息")
            print("S. 商店")
            print("D. 查看卡组")
            print("E. 查看遗物")
            print("C. 卡牌图鉴")
            print("T. 遗物图鉴")
            print("V. 保存游戏")
            print("Q. 返回主菜单")
            print("M. 查看地图")
            print("H. 帮助")
        print()
        
            choice = input("> ").upper()
            
            # 处理路径选择
            if choice.isdigit() and 1 <= int(choice) <= 9:
                path_index = int(choice) - 1
                if self.current_node and self.current_node.connections and path_index < len(self.current_node.connections):
                    next_node = self.current_node.connections[path_index]
                    self.move_to_node(next_node)
                    # 如果移动到了新节点，执行节点操作
                    self.execute_node_action()
                    continue
                else:
                    print(Fore.RED + "无效的路径选择" + Style.RESET_ALL)
                    self.wait_for_key()
                    continue
            
            # 处理其他选项
            if choice == "A":
            # 开始战斗
            enemy_count = 1
            if self.game_state.floor % 10 == 0:  # Boss战
                print(Fore.RED + "你遇到了Boss!" + Style.RESET_ALL)
                self.game_state.start_combat(1, False, True)
            elif self.game_state.floor % 5 == 0:  # 精英战
                print(Fore.MAGENTA + "你遇到了精英敌人!" + Style.RESET_ALL)
                self.game_state.start_combat(1, True, False)
                else:  # 普通战斗
                    self.game_state.start_combat(1, False, False)
                
                # 进入战斗循环
                self.combat_loop()
            
            elif choice == "R":
            # 休息
            self.rest()
        
            elif choice == "S":
            # 商店
            self.shop()
        
            elif choice == "D":
            # 查看卡组
            self.view_deck()
        
            elif choice == "E":
            # 查看遗物
            self.view_relics()
        
            elif choice == "C":
                # 卡牌图鉴
                self.show_card_collection()
                
            elif choice == "T":
                # 遗物图鉴
                self.show_relic_collection()
                
            elif choice == "V":
            # 保存游戏
            self.game_state.save_game(self.player_name)
                print(Fore.GREEN + "游戏已保存!" + Style.RESET_ALL)
            self.wait_for_key()
        
            elif choice == "Q":
            # 返回主菜单
                return False
                
            elif choice == "M":
                # 查看地图
                self.display_map()
            
            elif choice == "H":
                # 帮助
            self.show_help()
        
        else:
            print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
            self.wait_for_key()
                continue
    
    def move_to_node(self, node):
        """移动到指定节点"""
        self.current_node = node
        self.current_node.visited = True
        
        # 移动到新节点时增加楼层数
        self.game_state.floor += 1
        
        # 如果是Boss节点，进入Boss战斗
        if node.node_type == "Boss":
            print(Fore.RED + "你遇到了Boss!" + Style.RESET_ALL)
            self.wait_for_key()
            self.game_state.start_combat(1, False, True)
            self.combat_loop()
    
    def execute_node_action(self):
        """执行当前节点的操作"""
        node_type = self.current_node.node_type
        
        if node_type == "普通战斗":
            print(Fore.RED + "你遇到了敌人!" + Style.RESET_ALL)
            self.wait_for_key()
            self.game_state.start_combat(1, False, False)
            self.combat_loop()
        elif node_type == "精英战斗":
            print(Fore.MAGENTA + "你遇到了精英敌人!" + Style.RESET_ALL)
            self.wait_for_key()
            self.game_state.start_combat(1, True, False)
            self.combat_loop()
        elif node_type == "Boss":
            print(Fore.RED + "你遇到了Boss!" + Style.RESET_ALL)
            self.wait_for_key()
            self.game_state.start_combat(1, False, True)
            self.combat_loop()
        elif node_type == "休息处":
            self.rest()
        elif node_type == "商店":
            self.shop()
        elif node_type == "宝箱":
            self.open_chest()
        elif node_type == "未知事件":
            self.random_event()
        else:
            print(Fore.YELLOW + "什么也没发生..." + Style.RESET_ALL)
            self.wait_for_key()
    
    def open_chest(self):
        """打开宝箱"""
        self.clear_screen()
        print(Fore.YELLOW + "你找到了一个宝箱!" + Style.RESET_ALL)
        
        # 随机决定宝箱内容
        chest_type = random.choices(["gold", "relic", "card"], weights=[40, 40, 20])[0]
        
        if chest_type == "gold":
            # 获得金币
            gold_amount = random.randint(25, 75)
            self.game_state.player.gold += gold_amount
            print(Fore.YELLOW + f"你获得了 {gold_amount} 金币!" + Style.RESET_ALL)
        elif chest_type == "relic":
            # 获得随机遗物
            relic = self.get_random_relic()
            if relic:
                relic_name = self.add_relic_to_player(relic)
                print(Fore.CYAN + f"你获得了遗物: {relic.name} - {relic.description}" + Style.RESET_ALL)
            else:
                print(Fore.RED + "没有可用的遗物!" + Style.RESET_ALL)
        elif chest_type == "card":
            # 获得随机卡牌
            self.offer_card_reward()
        
        self.wait_for_key()
    
    def get_random_relic(self):
        """获取随机遗物"""
        import duckdb
        
        # 已拥有的遗物ID
        owned_relic_ids = [relic.id for relic in self.game_state.player.relics]
        
        # 连接数据库
        con = duckdb.connect(DB_PATH)
        
        # 构建查询
        query = """
        SELECT * FROM relics 
        WHERE id NOT IN (""" + ",".join(["?" for _ in owned_relic_ids]) + """) 
        AND (character_id IS NULL OR character_id = ?)
        """
        
        params = owned_relic_ids + [self.game_state.player.id]
        
        # 执行查询
        relics = con.execute(query, params).fetchall()
        con.close()
        
        if not relics:
            return None
        
        # 按稀有度分组
        relics_by_rarity = {
            "Common": [],
            "Uncommon": [],
            "Rare": [],
            "Boss": []
        }
        
        for relic in relics:
            if relic[2] in relics_by_rarity:
                relics_by_rarity[relic[2]].append(relic)
        
        # 根据稀有度确定概率
        rarity_weights = {
            "Common": 60,
            "Uncommon": 30,
            "Rare": 9,
            "Boss": 1
        }
        
        # 选择稀有度
        rarities = []
        weights = []
        
        for rarity, relic_list in relics_by_rarity.items():
            if relic_list:  # 只添加有遗物的稀有度
                rarities.append(rarity)
                weights.append(rarity_weights[rarity])
        
        if not rarities:
            return None
        
        # 根据权重随机选择稀有度
        selected_rarity = random.choices(rarities, weights=weights)[0]
        
        # 从选定稀有度中随机选择遗物
        selected_relic = random.choice(relics_by_rarity[selected_rarity])
        
        # 创建遗物对象
        from src.models import Relic
        relic = Relic(
            id=selected_relic[0],
            name=selected_relic[1],
            rarity=selected_relic[2],
            description=selected_relic[3],
            character_id=selected_relic[4]
        )
        
        return relic
    
    def get_random_potion(self):
        """获取随机药水"""
        from src.models import Potion
        
        # 获取角色ID
        character_id = self.game_state.player.id
        
        # 获取随机药水
        potion = Potion.get_random_potion(character_id)
        
        return potion
    
    def add_potion_to_player(self, potion):
        """将药水添加到玩家药水栏"""
        if len(self.game_state.player.potions) >= self.game_state.player.max_potions:
            return False
        
        self.game_state.player.potions.append(potion)
        return True

    def add_relic_to_player(self, relic):
        """将遗物添加给玩家"""
        # 检查是否已有此遗物
        for existing_relic in self.game_state.player.relics:
            if existing_relic.id == relic.id:
                return False
        
        # 添加遗物
        self.game_state.player.relics.append(relic)
        
        # 更新统计信息
        try:
            self.game_state.update_stats("relics_obtained", 1)
        except Exception as e:
            print(f"统计更新失败: {e}")
        
        # 处理特殊遗物效果
        if relic.name == "勇士腰带":
            self.game_state.player.max_hp += 15
            self.game_state.player.current_hp += 15
        elif relic.name == "血瓶":
            self.game_state.player.heal(10)
        
        # 触发遗物的拾起效果
        message = relic.on_pickup(self.game_state.player)
        if message:
            print(Fore.CYAN + message + Style.RESET_ALL)
        
        return True
    
    def offer_card_reward(self):
        """提供卡牌奖励选择"""
        import duckdb
        
            self.clear_screen()
        print(Fore.GREEN + "选择一张卡牌添加到你的牌组:" + Style.RESET_ALL)
        
        # 连接数据库
        con = duckdb.connect(DB_PATH)
        
        # 获取可用的卡牌
        query = """
        SELECT * FROM cards 
        WHERE (character_id IS NULL OR character_id = ?) 
        AND rarity != 'Basic'
        """
        
        result = con.execute(query, [self.game_state.player.id]).fetchall()
        con.close()
        
        if not result:
            print(Fore.RED + "没有可用的卡牌!" + Style.RESET_ALL)
            self.wait_for_key()
            return
        
        # 按稀有度分类
        common_cards = [c for c in result if c[3] == 'Common']
        uncommon_cards = [c for c in result if c[3] == 'Uncommon']
        rare_cards = [c for c in result if c[3] == 'Rare']
        
        # 随机选择3张卡牌
        card_choices = []
        
        # 确定稀有度分布
        rarity_roll = random.random()
        if rarity_roll < 0.70:  # 70% 概率获得普通卡牌
            if common_cards:
                card_choices.extend(random.sample(common_cards, min(3, len(common_cards))))
        elif rarity_roll < 0.95:  # 25% 概率获得不常见卡牌
            if uncommon_cards:
                card_choices.extend(random.sample(uncommon_cards, min(3, len(uncommon_cards))))
        else:  # 5% 概率获得稀有卡牌
            if rare_cards:
                card_choices.extend(random.sample(rare_cards, min(3, len(rare_cards))))
        
        # 如果没有足够的卡牌，从其他稀有度补充
        if len(card_choices) < 3:
            remaining_cards = []
            if common_cards:
                remaining_cards.extend(common_cards)
            if uncommon_cards:
                remaining_cards.extend(uncommon_cards)
            if rare_cards:
                remaining_cards.extend(rare_cards)
            
            # 从剩余卡牌中移除已选择的卡牌
            remaining_cards = [c for c in remaining_cards if c not in card_choices]
            
            if remaining_cards:
                additional_cards = random.sample(remaining_cards, min(3 - len(card_choices), len(remaining_cards)))
                card_choices.extend(additional_cards)
        
        # 显示卡牌选择
        from src.models import Card
        cards = []
        for i, card_data in enumerate(card_choices):
            card = Card(
                id=card_data[0],
                name=card_data[1],
                card_type=card_data[2],
                rarity=card_data[3],
                energy_cost=card_data[4],
                description=card_data[5],
                character_id=card_data[6],
                upgraded=False
            )
            cards.append(card)
            self.print_card_simple(card, i+1)
        
        print("\n[s] 跳过")
        print()
        
        # 获取玩家选择
        while True:
            choice = input("> ")
            
            if choice.lower() == 's':
                print(Fore.YELLOW + "你选择跳过了卡牌奖励。" + Style.RESET_ALL)
                break
            
            try:
                index = int(choice) - 1  # 转换为0-based索引
                if 0 <= index < len(cards):
                    selected_card = cards[index]
                    # 添加到玩家牌组
                    self.game_state.player.cards.append(selected_card)
                    print(Fore.GREEN + f"你将 {selected_card.name} 添加到了你的牌组!" + Style.RESET_ALL)
                    break
                else:
                    print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
            except ValueError:
                print(Fore.RED + "请输入有效的数字" + Style.RESET_ALL)
        
        self.wait_for_key()
    
    def show_relics_by_filter(self, character_id=None):
        """按角色显示遗物"""
        import duckdb
        
        self.clear_screen()
        
        # 连接数据库
        con = duckdb.connect(DB_PATH)
        
        # 构建查询
        query = "SELECT * FROM relics"
        params = []
        
        if character_id is not None:
            query += " WHERE character_id = ?"
            params.append(character_id)
        
        query += " ORDER BY rarity, name"
        
        # 执行查询
        relics = con.execute(query, params).fetchall()
        con.close()
        
        # 显示标题
        if character_id is None:
            print(Fore.CYAN + "所有遗物:" + Style.RESET_ALL)
        else:
            character_names = {1: "铁甲战士", 2: "静默猎手", 3: "故障机器人"}
            print(Fore.CYAN + f"{character_names.get(character_id, '未知角色')}遗物:" + Style.RESET_ALL)
        
        # 按稀有度分组
        relics_by_rarity = {}
        for relic in relics:
            rarity = relic[2]
            if rarity not in relics_by_rarity:
                relics_by_rarity[rarity] = []
            relics_by_rarity[rarity].append(relic)
        
        # 稀有度顺序
        rarity_order = ["Starter", "Common", "Uncommon", "Rare", "Boss"]
        
        # 显示遗物
        for rarity in rarity_order:
            if rarity in relics_by_rarity:
                rarity_color = Fore.WHITE
                if rarity == "Common":
                    rarity_color = Fore.GREEN
                elif rarity == "Uncommon":
                    rarity_color = Fore.BLUE
                elif rarity == "Rare":
                    rarity_color = Fore.MAGENTA
                elif rarity == "Boss":
                    rarity_color = Fore.RED
                elif rarity == "Starter":
                    rarity_color = Fore.YELLOW
                
                print(rarity_color + f"\n{rarity} 遗物:" + Style.RESET_ALL)
                for relic in relics_by_rarity[rarity]:
                    character_specific = ""
                    if relic[4] is not None:
                        character_names = {1: "铁甲战士", 2: "静默猎手", 3: "故障机器人"}
                        character_specific = f" ({character_names.get(relic[4], '未知角色')}专属)"
                    
                    print(rarity_color + f"  {relic[1]}{character_specific} - {relic[3]}" + Style.RESET_ALL)
        
        self.wait_for_key()
    
    def show_character_info(self):
        """显示所有角色的详细信息"""
        import duckdb
        
        try:
            # 连接数据库
            con = duckdb.connect(DB_PATH)
            
            # 获取所有角色信息
            characters = con.execute(
                "SELECT id, name, max_hp, starting_gold, description FROM characters ORDER BY id"
            ).fetchall()
            
            con.close()
            
            self.clear_screen()
            print(Fore.YELLOW + "角色信息" + Style.RESET_ALL)
            self.print_separator()
            
            for char in characters:
                char_id, name, max_hp, starting_gold, description = char
                emoji = EMOJI.get(name, "👤")
                
                print(f"\n{Fore.CYAN}{emoji} {name}{Style.RESET_ALL}")
                print(f"生命值: {max_hp}")
                print(f"初始金币: {starting_gold}")
                print(f"描述: {description}")
                
                # 获取该角色的初始遗物
                con = duckdb.connect(DB_PATH)
                relics = con.execute(
                    "SELECT name, description FROM relics WHERE character_id = ?", 
                    [char_id]
                ).fetchall()
                con.close()
                
                if relics:
                    print(f"初始遗物:")
                    for relic in relics:
                        relic_name, relic_desc = relic
                        print(f"  • {relic_name}: {relic_desc}")
                
                # 获取该角色的初始卡牌
                con = duckdb.connect(DB_PATH)
                starter_cards = con.execute(
                    """
                    SELECT name, COUNT(*) as count 
                    FROM cards 
                    WHERE character_id = ? AND is_starter = TRUE 
                    GROUP BY name
                    """, 
                    [char_id]
                ).fetchall()
                con.close()
                
                if starter_cards:
                    print(f"初始卡牌:")
                    for card in starter_cards:
                        card_name, count = card
                        print(f"  • {card_name} x{count}")
            
            self.print_separator()
            print("按回车键返回...")
            try:
                input()
            except EOFError:
                # 如果在管道输入中，直接返回
                pass
        except Exception as e:
            print(f"显示角色信息出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self.wait_for_key()
    
    def show_relic_collection(self):
        """显示遗物图鉴"""
        import duckdb
        
        try:
            while True:
                self.clear_screen()
                self.print_title()
                
                print(Fore.CYAN + "遗物图鉴:" + Style.RESET_ALL)
                print("1. 所有遗物")
                print("2. 通用遗物")
                print("3. 铁甲战士遗物")
                print("4. 静默猎手遗物")
                print("5. 故障机器人遗物")
                print("6. 按稀有度查看")
                print("7. 返回")
            print()
            
                try:
                    choice = input("> ")
                    
                    if choice == "1":
                        self.show_relics_by_filter()
                    elif choice == "2":
                        self.show_relics_by_filter(character_id=None)
                    elif choice == "3":
                        self.show_relics_by_filter(character_id=1)
                    elif choice == "4":
                        self.show_relics_by_filter(character_id=2)
                    elif choice == "5":
                        self.show_relics_by_filter(character_id=3)
                    elif choice == "6":
                        self.show_relics_by_rarity()
                    elif choice == "7":
                        return
                    else:
                        print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
                    self.wait_for_key()
                except EOFError:
                    # 如果在管道输入中，直接返回
                    return
        except Exception as e:
            print(f"显示遗物图鉴出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self.wait_for_key()
    
    def show_relics_by_rarity(self):
        """按稀有度显示遗物"""
        import duckdb
        
        self.clear_screen()
        self.print_title()
        
        print(Fore.CYAN + "按稀有度查看遗物:" + Style.RESET_ALL)
        print("1. 初始遗物 (Starter)")
        print("2. 普通遗物 (Common)")
        print("3. 非普通遗物 (Uncommon)")
        print("4. 稀有遗物 (Rare)")
        print("5. Boss遗物")
        print("6. 返回")
        print()
        
        choice = input("> ")
        
        rarity_map = {
            "1": "Starter",
            "2": "Common",
            "3": "Uncommon",
            "4": "Rare",
            "5": "Boss"
        }
        
        if choice in rarity_map:
            self.show_relics_by_rarity_filter(rarity_map[choice])
        elif choice == "6":
            return
        else:
            print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
            self.wait_for_key()
    
    def show_relics_by_rarity_filter(self, rarity):
        """显示指定稀有度的遗物"""
        import duckdb
        
        self.clear_screen()
        
        # 连接数据库
        con = duckdb.connect(DB_PATH)
        
        # 执行查询
        relics = con.execute(
            "SELECT * FROM relics WHERE rarity = ? ORDER BY character_id, name",
            [rarity]
        ).fetchall()
        con.close()
        
        # 显示标题
        rarity_color = Fore.WHITE
        if rarity == "Common":
            rarity_color = Fore.GREEN
        elif rarity == "Uncommon":
            rarity_color = Fore.BLUE
        elif rarity == "Rare":
            rarity_color = Fore.MAGENTA
        elif rarity == "Boss":
            rarity_color = Fore.RED
        elif rarity == "Starter":
            rarity_color = Fore.YELLOW
        
        print(rarity_color + f"{rarity} 遗物:" + Style.RESET_ALL)
        
        # 按角色分组
        relics_by_character = {
            None: [],
            1: [],
            2: [],
            3: []
        }
        
        for relic in relics:
            character_id = relic[4]
            if character_id not in relics_by_character:
                relics_by_character[character_id] = []
            relics_by_character[character_id].append(relic)
        
        # 显示通用遗物
        if relics_by_character[None]:
            print("\n通用遗物:")
            for relic in relics_by_character[None]:
                print(rarity_color + f"  {relic[1]} - {relic[3]}" + Style.RESET_ALL)
        
        # 显示角色专属遗物
        character_names = {1: "铁甲战士", 2: "静默猎手", 3: "故障机器人"}
        for character_id, character_relics in relics_by_character.items():
            if character_id is not None and character_relics:
                print(f"\n{character_names.get(character_id, '未知角色')}专属遗物:")
                for relic in character_relics:
                    print(rarity_color + f"  {relic[1]} - {relic[3]}" + Style.RESET_ALL)
        
        self.wait_for_key()

    def show_card_collection(self):
        """显示卡牌图鉴"""
        import duckdb
        import sys
        
        print("进入卡牌图鉴函数")
        
        try:
            while True:
                self.clear_screen()
                self.print_title()
                
                print(Fore.CYAN + "卡牌图鉴:" + Style.RESET_ALL)
                print("1. 铁甲战士卡牌")
                print("2. 静默猎手卡牌")
                print("3. 故障机器人卡牌")
                print("4. 角色信息")
                print("5. 返回主菜单")
                print()
                
                try:
                    choice = input("> ")
                    print(f"用户选择了: {choice}")
                    
                    if choice in ["1", "2", "3"]:
                        character_id = int(choice)
                        print(f"显示角色ID={character_id}的卡牌")
                        self.show_character_cards(character_id)
                    elif choice == "4":
                        print("显示角色信息")
                        self.show_character_info()
                    elif choice == "5":
                        print("返回主菜单")
                        return
                    else:
                        print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
                        try:
                            self.wait_for_key()
                        except EOFError:
                            # 如果在管道输入中，直接返回
                            return
                except EOFError:
                    # 如果在管道输入中，直接返回
                    return
        except Exception as e:
            print(f"卡牌图鉴出错: {str(e)}")
            import traceback
            traceback.print_exc()
            try:
                self.wait_for_key()
            except EOFError:
                # 如果在管道输入中，直接返回
                return

    def show_character_cards(self, character_id):
        """显示指定角色的所有卡牌"""
        import duckdb
        
        print(f"进入show_character_cards函数，角色ID={character_id}")
        
        try:
            # 连接数据库
            con = duckdb.connect(DB_PATH)
            print(f"已连接数据库: {DB_PATH}")
            
            # 获取角色信息
            character = con.execute(
                "SELECT name FROM characters WHERE id = ?",
                [character_id]
            ).fetchone()
            
            if not character:
                print(Fore.RED + "找不到该角色" + Style.RESET_ALL)
                self.wait_for_key()
                return
            
            character_name = character[0]
            print(f"找到角色: {character_name}")
            
            # 获取该角色的所有卡牌
            print("查询该角色的所有卡牌...")
            cards = con.execute(
                """
                SELECT id, name, type, rarity, energy_cost, description 
                FROM cards 
                WHERE character_id = ? OR character_id IS NULL
                ORDER BY rarity, type, energy_cost, name
                """,
                [character_id]
            ).fetchall()
            
            con.close()
            print(f"找到 {len(cards)} 张卡牌")
            
            # 按稀有度分类
            rarity_groups = {
                "Basic": [],
                "Common": [],
                "Uncommon": [],
                "Rare": []
            }
            
            for card in cards:
                card_id, name, card_type, rarity, energy_cost, description = card
                rarity_groups[rarity].append({
                    "id": card_id,
                    "name": name,
                    "type": card_type,
                    "energy_cost": energy_cost,
                    "description": description
                })
            
            while True:
                self.clear_screen()
                
                print(Fore.YELLOW + f"{character_name}的卡牌图鉴" + Style.RESET_ALL)
                self.print_separator()
                
                # 创建卡牌列表，包含索引
                all_cards = []
                card_index = 1
                
                for rarity, cards in rarity_groups.items():
                    if cards:
                        print(Fore.CYAN + f"\n{rarity}卡牌:" + Style.RESET_ALL)
                        for card in cards:
                            emoji = EMOJI.get(card["type"], "❓")
                            cost = card["energy_cost"]
                            name = card["name"]
                            desc = card["description"]
                            print(f"{card_index}. {emoji} [{cost}] {name}")
                            all_cards.append(card)
                            card_index += 1
                
                self.print_separator()
                print("输入卡牌编号查看详情，按 'q' 返回")
                
                try:
                    choice = input("> ")
                    
                    if choice.lower() == 'q':
                        break
                    
                    # 尝试查看卡牌详情
                    try:
                        card_idx = int(choice) - 1
                        if 0 <= card_idx < len(all_cards):
                            self.show_card_details(all_cards[card_idx])
                        else:
                            print(Fore.RED + "无效的卡牌编号" + Style.RESET_ALL)
                    self.wait_for_key()
                except ValueError:
                        print(Fore.RED + "请输入有效的数字" + Style.RESET_ALL)
                        self.wait_for_key()
                except EOFError:
                    # 如果在管道输入中，直接返回
                    break
        except Exception as e:
            print(f"显示角色卡牌出错: {str(e)}")
            import traceback
            traceback.print_exc()
                    self.wait_for_key()
            
    def show_card_details(self, card):
        """显示卡牌详细信息，包括升级后的效果"""
        self.clear_screen()
        
        print(f"显示卡牌详情: {card['name']}")
        
        # 获取卡牌基本信息
        card_id = card["id"]
        name = card["name"]
        card_type = card["type"]
        energy_cost = card["energy_cost"]
        description = card["description"]
        
        # 卡牌类型对应的颜色
        type_colors = {
            "Attack": Fore.RED,
            "Skill": Fore.BLUE,
            "Power": Fore.YELLOW
        }
        
        # 获取卡牌类型的颜色
        type_color = type_colors.get(card_type, Fore.WHITE)
        
        # 获取卡牌类型的emoji
        emoji = EMOJI.get(card_type, "❓")
        
        # 打印卡牌框
        width = 40
        print("┌" + "─" * width + "┐")
        print(f"│ {type_color}{name}{Style.RESET_ALL}" + " " * (width - len(name) - 1) + "│")
        print(f"│ {emoji} [{energy_cost}]" + " " * (width - 6) + "│")
        print("│" + "─" * width + "│")
        print(f"│ {description}" + " " * (width - len(description) - 1) + "│")
        print("└" + "─" * width + "┘")
        
        # 显示升级后的效果
        print("\n" + Fore.YELLOW + "升级后效果:" + Style.RESET_ALL)
        
        # 根据不同卡牌类型显示升级后的效果
        if "打击" in name:
            print("伤害从6点提升到9点")
        elif "防御" in name:
            print("格挡从5点提升到8点")
        elif name == "愤怒":
            print("获得的力量从3点提升到5点")
        elif name == "重击":
            print("伤害从14点提升到18点")
        elif name == "铁斩波":
            print("伤害从8点提升到12点")
        elif name == "顺势斩":
            print("伤害从12/16点提升到16/20点")
        elif name == "毒刃":
            print("伤害从5点提升到7点，中毒层数从2层提升到3层")
        elif name == "闪避":
            print("格挡从8点提升到11点")
        elif name == "致命毒素":
            print("中毒层数从5层提升到7层")
        elif name == "刀刃之舞":
            print("伤害从4点提升到6点")
        elif name == "闪电球" or name == "冰霜球":
            print("生成的充能球数量从1个提升到2个")
        elif name == "双重施法":
            print("可以使下两张技能牌打出两次，而不是一张")
        elif name == "自我修复":
            print("每回合回复的生命值从3点提升到5点")
        elif name == "火球术":
            print("伤害从10点提升到14点")
        elif name == "血肉奉献":
            print("获得的格挡从8点提升到10点")
        elif name == "狂暴打击":
            print("基础伤害从8点提升到10点")
        elif name == "战斗呐喊":
            print("每打出攻击牌获得的力量从1点提升到2点")
        elif name == "暗影步伐":
            print("获得的格挡从6点提升到8点")
        elif name == "毒雾弹":
            print("给予的中毒层数从4/3层提升到5/4层")
        elif name == "伏击":
            print("伤害从4点提升到6点")
        elif name == "能量涌动":
            print("获得的能量从2点提升到3点")
        elif name == "核心过载":
            print("每回合获得的充能球数量从1个提升到2个")
        elif name == "数据分析":
            print("查看的卡牌数量从3张提升到4张")
        else:
            print("无升级效果或效果未知")
        
        print("\n按回车键返回...")
        try:
            input()
        except EOFError:
            # 如果在管道输入中，直接返回
            pass

    def show_save_list(self):
        """显示存档列表"""
        import duckdb
        
        try:
            self.clear_screen()
            self.print_title()
            
            print(Fore.CYAN + "存档列表:" + Style.RESET_ALL)
            
            # 连接数据库
            con = duckdb.connect(DB_PATH)
            
            # 获取所有存档
            saves = con.execute(
                """
                SELECT s.id, s.player_name, c.name, s.current_hp, s.max_hp, s.gold, s.floor, 
                       s.created_at, s.updated_at
                FROM saves s
                JOIN characters c ON s.character_id = c.id
                ORDER BY s.updated_at DESC
                """
            ).fetchall()
            
            con.close()
            
            if not saves:
                print(Fore.YELLOW + "没有存档记录" + Style.RESET_ALL)
                self.wait_for_key()
                return
            
            # 显示存档列表
            for i, save in enumerate(saves):
                save_id = save[0]
                player_name = save[1]
                character_name = save[2]
                current_hp = save[3]
                max_hp = save[4]
                gold = save[5]
                floor = save[6]
                created_at = save[7]
                updated_at = save[8]
                
                # 格式化日期时间
                created_date = created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(created_at, "strftime") else str(created_at)
                updated_date = updated_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(updated_at, "strftime") else str(updated_at)
                
                print(f"\n{i+1}. {player_name} - {character_name}")
                print(f"   楼层: {floor} | 生命: {current_hp}/{max_hp} | 金币: {gold}")
                print(f"   创建时间: {created_date} | 最后更新: {updated_date}")
            
            print("\n[b] 返回")
            print()
            
            try:
                choice = input("> ")
                
                if choice.lower() == 'b':
                    return
                
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(saves):
                        self.show_save_details(saves[index][0])
            else:
                        print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
                        self.wait_for_key()
                except ValueError:
                    print(Fore.RED + "无效的输入，请重试" + Style.RESET_ALL)
                    self.wait_for_key()
            except EOFError:
                # 如果在管道输入中，直接返回
                return
        except Exception as e:
            print(f"显示存档列表出错: {str(e)}")
            import traceback
            traceback.print_exc()
                self.wait_for_key()
    
    def show_save_details(self, save_id):
        """显示存档详细信息"""
        import duckdb
        
        try:
        self.clear_screen()
        
            # 连接数据库
            con = duckdb.connect(DB_PATH)
            
            # 获取存档详情
            save = con.execute(
                """
                SELECT s.id, s.player_name, c.name, s.current_hp, s.max_hp, s.gold, s.floor, 
                       s.created_at, s.updated_at, c.id
                FROM saves s
                JOIN characters c ON s.character_id = c.id
                WHERE s.id = ?
                """,
                [save_id]
            ).fetchone()
            
            if not save:
                print(Fore.RED + "存档不存在" + Style.RESET_ALL)
                self.wait_for_key()
                con.close()
                return
            
            # 获取卡牌信息
            cards = con.execute(
                """
                SELECT c.name, c.type, c.rarity, pc.upgraded
                FROM player_cards pc
                JOIN cards c ON pc.card_id = c.id
                WHERE pc.save_id = ?
                ORDER BY c.type, c.rarity, c.name
                """,
                [save_id]
            ).fetchall()
            
            # 获取遗物信息
            relics = con.execute(
                """
                SELECT r.name, r.rarity, r.description
                FROM player_relics pr
                JOIN relics r ON pr.relic_id = r.id
                WHERE pr.save_id = ?
                ORDER BY r.rarity, r.name
                """,
                [save_id]
            ).fetchall()
            
            con.close()
            
            # 格式化日期时间
            created_at = save[7]
            updated_at = save[8]
            created_date = created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(created_at, "strftime") else str(created_at)
            updated_date = updated_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(updated_at, "strftime") else str(updated_at)
            
            # 显示存档详情
            print(Fore.CYAN + "存档详情:" + Style.RESET_ALL)
            print(f"玩家名称: {save[1]}")
            print(f"角色: {save[2]}")
            print(f"生命: {save[3]}/{save[4]}")
            print(f"金币: {save[5]}")
            print(f"楼层: {save[6]}")
            print(f"创建时间: {created_date}")
            print(f"最后更新: {updated_date}")
            
            # 显示卡组
            print("\n" + Fore.CYAN + "卡组:" + Style.RESET_ALL)
            if not cards:
                print(Fore.YELLOW + "没有卡牌" + Style.RESET_ALL)
        else:
                # 按类型分类
                cards_by_type = {
                    "Attack": [],
                    "Skill": [],
                    "Power": [],
                    "Other": []
                }
                
                for card in cards:
                    card_type = card[1] if card[1] in cards_by_type else "Other"
                    cards_by_type[card_type].append(card)
                
                # 显示各类型卡牌
                for card_type, type_cards in cards_by_type.items():
                    if type_cards:
                        if card_type == "Attack":
                            print(Fore.RED + f"\n攻击牌 ({len(type_cards)}):" + Style.RESET_ALL)
                        elif card_type == "Skill":
                            print(Fore.GREEN + f"\n技能牌 ({len(type_cards)}):" + Style.RESET_ALL)
                        elif card_type == "Power":
                            print(Fore.BLUE + f"\n能力牌 ({len(type_cards)}):" + Style.RESET_ALL)
                        else:
                            print(Fore.WHITE + f"\n其他牌 ({len(type_cards)}):" + Style.RESET_ALL)
                        
                        for card in type_cards:
                            card_name = card[0]
                            if card[3]:  # upgraded
                                card_name += "+"
                            
                            rarity_color = Fore.WHITE
                            if card[2] == "Common":
                                rarity_color = Fore.GREEN
                            elif card[2] == "Uncommon":
                                rarity_color = Fore.BLUE
                            elif card[2] == "Rare":
                                rarity_color = Fore.MAGENTA
                            elif card[2] == "Basic":
                                rarity_color = Fore.YELLOW
                            
                            print(f"  {rarity_color}{card_name}{Style.RESET_ALL}")
            
            # 显示遗物
            print("\n" + Fore.CYAN + "遗物:" + Style.RESET_ALL)
            if not relics:
                print(Fore.YELLOW + "没有遗物" + Style.RESET_ALL)
            else:
                # 按稀有度分类
                relics_by_rarity = {}
                for relic in relics:
                    rarity = relic[1]
                    if rarity not in relics_by_rarity:
                        relics_by_rarity[rarity] = []
                    relics_by_rarity[rarity].append(relic)
                
                # 稀有度顺序
                rarity_order = ["Starter", "Common", "Uncommon", "Rare", "Boss"]
                
                # 显示各稀有度遗物
                for rarity in rarity_order:
                    if rarity in relics_by_rarity:
                        rarity_color = Fore.WHITE
                        if rarity == "Common":
                            rarity_color = Fore.GREEN
                        elif rarity == "Uncommon":
                            rarity_color = Fore.BLUE
                        elif rarity == "Rare":
                            rarity_color = Fore.MAGENTA
                        elif rarity == "Boss":
                            rarity_color = Fore.RED
                        elif rarity == "Starter":
                            rarity_color = Fore.YELLOW
                        
                        print(rarity_color + f"\n{rarity} 遗物:" + Style.RESET_ALL)
                        for relic in relics_by_rarity[rarity]:
                            print(rarity_color + f"  {relic[0]} - {relic[2]}" + Style.RESET_ALL)
            
            print("\n1. 加载此存档")
            print("2. 返回")
            print()
            
            try:
                choice = input("> ")
                
                if choice == "1":
                    # 加载存档
                    self.game_state = GameState.load_game(save[1])
                    self.player_name = save[1]
                    print(Fore.GREEN + "存档已加载!" + Style.RESET_ALL)
                    self.wait_for_key()
                    self.print_player_status()
                elif choice == "2":
                    return
                else:
                    print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
                    self.wait_for_key()
            except EOFError:
                # 如果在管道输入中，直接返回
                return
        except Exception as e:
            print(f"显示存档详情出错: {str(e)}")
            import traceback
            traceback.print_exc()
        self.wait_for_key()
    
    def print_player_status(self):
        """显示玩家状态信息"""
        if not self.game_state or not self.game_state.player:
            print(Fore.RED + "没有加载游戏!" + Style.RESET_ALL)
            return
        
        player = self.game_state.player
        
        self.clear_screen()
        self.print_title()
        
        print(Fore.CYAN + "玩家状态:" + Style.RESET_ALL)
        print(f"名称: {self.player_name}")
        print(f"角色: {player.name}")
        print(f"生命: {player.current_hp}/{player.max_hp}")
        print(f"金币: {player.gold}")
        print(f"楼层: {self.game_state.floor}")
        
        # 显示当前位置
        if self.current_node:
            print(f"当前位置: {self.current_node.node_type} {EMOJI.get(self.current_node.node_type, '')}")
        
        if player.strength > 0:
            print(f"力量: {player.strength}")
        if player.dexterity > 0:
            print(f"敏捷: {player.dexterity}")
        
        # 显示遗物
        if player.relics:
            print("\n" + Fore.CYAN + "遗物:" + Style.RESET_ALL)
            for relic in player.relics:
                rarity_color = Fore.WHITE
                if relic.rarity == "Common":
                    rarity_color = Fore.GREEN
                elif relic.rarity == "Uncommon":
                    rarity_color = Fore.BLUE
                elif relic.rarity == "Rare":
                    rarity_color = Fore.MAGENTA
                elif relic.rarity == "Boss":
                    rarity_color = Fore.RED
                elif relic.rarity == "Starter":
                    rarity_color = Fore.YELLOW
                
                print(f"  {rarity_color}{relic.name}{Style.RESET_ALL} - {relic.description}")
        
        # 显示卡组
        print("\n" + Fore.CYAN + "卡组:" + Style.RESET_ALL)
        if not player.cards:
            print(Fore.YELLOW + "没有卡牌" + Style.RESET_ALL)
        else:
            # 按类型分类
            cards_by_type = {
                "Attack": [],
                "Skill": [],
                "Power": [],
                "Other": []
            }
            
            for card in player.cards:
                card_type = card.type if card.type in cards_by_type else "Other"
                cards_by_type[card_type].append(card)
            
            # 显示各类型卡牌
            for card_type, type_cards in cards_by_type.items():
                if type_cards:
                    if card_type == "Attack":
                        print(Fore.RED + f"\n攻击牌 ({len(type_cards)}):" + Style.RESET_ALL)
                    elif card_type == "Skill":
                        print(Fore.GREEN + f"\n技能牌 ({len(type_cards)}):" + Style.RESET_ALL)
                    elif card_type == "Power":
                        print(Fore.BLUE + f"\n能力牌 ({len(type_cards)}):" + Style.RESET_ALL)
                    else:
                        print(Fore.WHITE + f"\n其他牌 ({len(type_cards)}):" + Style.RESET_ALL)
                    
                    for card in type_cards:
                        card_name = card.name
                        if card.upgraded:
                            card_name += "+"
                        
                        rarity_color = Fore.WHITE
                        if card.rarity == "Common":
                            rarity_color = Fore.GREEN
                        elif card.rarity == "Uncommon":
                            rarity_color = Fore.BLUE
                        elif card.rarity == "Rare":
                            rarity_color = Fore.MAGENTA
                        elif card.rarity == "Basic":
                            rarity_color = Fore.YELLOW
                        
                        print(f"  {rarity_color}{card_name}{Style.RESET_ALL}")
        
        print("\n1. 继续游戏")
        print("2. 保存游戏")
        print("3. 返回主菜单")
        print()
        
        while True:
            try:
                choice = input("> ")
                
                if choice == "1":
                    # 直接进入地图界面
                    self.map_screen()  # 立即进入地图界面
                    return True  # 返回True表示继续游戏
                elif choice == "2":
                    if self.game_state.save_game(self.player_name):
                        print(Fore.GREEN + "游戏已保存!" + Style.RESET_ALL)
                    else:
                        print(Fore.RED + "保存游戏失败!" + Style.RESET_ALL)
                    self.wait_for_key()
                    # 不递归调用，而是重新显示当前界面
                    self.clear_screen()
                    return self.print_player_status()
                elif choice == "3":
                    return False  # 返回False表示退出游戏
                else:
                    print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
                    continue
            except EOFError:
                # 如果在管道输入中，直接返回
                return False

    def combat_loop(self):
        """战斗循环"""
        self.clear_screen()
        self.print_title()
        
        # 获取当前战斗的敌人
        enemies = self.game_state.current_enemies
        if not enemies:
            print(Fore.RED + "错误：没有敌人！" + Style.RESET_ALL)
            self.wait_for_key()
            return False
        
        player = self.game_state.player
        
        print(Fore.RED + "战斗开始！" + Style.RESET_ALL)
        self.wait_for_key()
        
        # 战斗回合
        turn = 1
        while True:
            self.clear_screen()
            self.print_title()
            
            print(Fore.YELLOW + f"回合 {turn}" + Style.RESET_ALL)
            print(f"玩家生命: {player.current_hp}/{player.max_hp}")
            print(f"能量: {player.energy}/{player.max_energy}")
            
            if player.block > 0:
                print(f"格挡: {player.block}")
            
            if player.strength > 0:
                print(f"力量: {player.strength}")
            
            if player.dexterity > 0:
                print(f"敏捷: {player.dexterity}")
            
            # 显示敌人信息
            print("\n敌人:")
            for i, enemy in enumerate(enemies, 1):
                # 显示敌人生命
                health_bar = f"{enemy.current_hp}/{enemy.max_hp}"
                
                # 显示敌人属性
                attributes = []
                if enemy.strength > 0:
                    attributes.append(f"力量: {enemy.strength}")
                if enemy.block > 0:
                    attributes.append(f"格挡: {enemy.block}")
                if enemy.poison > 0:
                    attributes.append(f"中毒: {enemy.poison}")
                
                attributes_str = " | ".join(attributes)
                if attributes_str:
                    attributes_str = f" | {attributes_str}"
                
                # 显示敌人意图
                intent = ""
                if enemy.intent == "Attack":
                    intent = f"{Fore.RED}攻击 {enemy.intent_value}{Style.RESET_ALL}"
                elif enemy.intent == "Defend":
                    intent = f"{Fore.BLUE}防御 {enemy.intent_value}{Style.RESET_ALL}"
                elif enemy.intent == "Buff":
                    intent = f"{Fore.YELLOW}增益 {enemy.intent_value}{Style.RESET_ALL}"
                
                # 根据敌人类型设置颜色
                name_color = Fore.WHITE
                if enemy.is_boss:
                    name_color = Fore.RED
                elif enemy.is_elite:
                    name_color = Fore.MAGENTA
                
                print(f"{i}. {name_color}{enemy.name}{Style.RESET_ALL} - 生命: {health_bar}{attributes_str} - 意图: {intent}")
            
            print("\n你的手牌:")
            # 使用玩家实际的手牌
            if not player.hand:
                # 如果没有手牌，从牌组中抽取5张
                hand_cards = player.cards[:5] if len(player.cards) >= 5 else player.cards
                player.hand = hand_cards.copy()
            
            for i, card in enumerate(player.hand, 1):
                self.print_card_simple(card, i)
        
            print("\n行动选择:")
            print("1-9. 使用卡牌")
            print("E. 结束回合")
            print("V. 查看弃牌堆")
            print("D. 查看抽牌堆")
            print()
            
            choice = input("> ").upper()
            
            if choice.isdigit() and 1 <= int(choice) <= len(player.hand):
                # 使用卡牌
                card_index = int(choice) - 1
                card = player.hand[card_index]
                
                # 检查能量是否足够
                if player.energy < card.energy_cost:
                    print(Fore.RED + f"能量不足! 需要 {card.energy_cost} 点能量。" + Style.RESET_ALL)
        self.wait_for_key()
                    continue
                
                # 如果是攻击牌，需要选择目标
                if card.type == "Attack" and len(enemies) > 1:
                    print("\n选择目标:")
                    for i, enemy in enumerate(enemies, 1):
                        print(f"{i}. {enemy.name} - 生命: {enemy.current_hp}/{enemy.max_hp}")
                    
                    target_choice = input("\n选择目标 > ")
                    if not target_choice.isdigit() or not (1 <= int(target_choice) <= len(enemies)):
                        print(Fore.RED + "无效的目标选择!" + Style.RESET_ALL)
                        self.wait_for_key()
                        continue
                    
                    target = enemies[int(target_choice) - 1]
                else:
                    # 默认选择第一个敌人
                    target = enemies[0]
                
                # 消耗能量
                player.energy -= card.energy_cost
                
                # 应用卡牌效果
                if card.type == "Attack":
                    # 攻击牌
                    damage = 6  # 基础伤害
                    if "打击" in card.name:
                        damage = 6
                    elif "重击" in card.name:
                        damage = 14
                    elif "铁斩波" in card.name:
                        damage = 8
                    
                    # 应用升级加成
                    if card.upgraded:
                        damage += 3
                    
                    # 应用力量加成
                    damage += player.strength
                    
                    # 应用伤害
                    target.current_hp -= damage
                    print(Fore.RED + f"你对 {target.name} 造成了 {damage} 点伤害!" + Style.RESET_ALL)
                    
                    # 检查敌人是否死亡
                    if target.current_hp <= 0:
                        print(Fore.GREEN + f"{target.name} 被击败了!" + Style.RESET_ALL)
                        enemies.remove(target)
                    
                    # 检查是否击败所有敌人
                    if not enemies:
                        print(Fore.GREEN + "战斗胜利!" + Style.RESET_ALL)
                        self.wait_for_key()
                        break
                
                elif card.type == "Skill":
                    # 技能牌
                    if "防御" in card.name:
                        block = 5  # 基础格挡
                        if card.upgraded:
                            block += 3
                        
                        # 应用敏捷加成
                        block += player.dexterity
                        
                        player.block += block
                        print(Fore.BLUE + f"你获得了 {block} 点格挡!" + Style.RESET_ALL)
                
                # 从手牌中移除使用的卡牌
                player.hand.pop(card_index)
                
                self.wait_for_key()
            
            elif choice == "E":
                # 结束回合，敌人行动
                print(Fore.YELLOW + "回合结束，敌人行动..." + Style.RESET_ALL)
                
                for enemy in enemies:
                    # 敌人行动
                    if enemy.intent == "Attack":
                        # 计算实际伤害
                        damage = max(0, enemy.intent_value - player.block)
                        block_absorbed = min(player.block, enemy.intent_value)
                        
                        # 减少格挡
                        player.block -= block_absorbed
                        
                        if damage > 0:
                            player.current_hp -= damage
                            print(Fore.RED + f"{enemy.name} 对你造成了 {damage} 点伤害!" + Style.RESET_ALL)
                        else:
                            print(Fore.BLUE + f"你的格挡吸收了全部伤害!" + Style.RESET_ALL)
                        
                        # 检查玩家是否死亡
                        if player.current_hp <= 0:
                            print(Fore.RED + "你被击败了!" + Style.RESET_ALL)
                            self.game_state.game_over = True
                            self.wait_for_key()
                            return False
                    
                    elif enemy.intent == "Defend":
                        # 敌人获得格挡
                        enemy.block += enemy.intent_value
                        print(f"{enemy.name} 获得了 {enemy.intent_value} 点格挡.")
                    
                    elif enemy.intent == "Buff":
                        # 敌人获得增益
                        print(f"{enemy.name} 获得了增益效果.")
                
                # 重新设置敌人意图
                for enemy in enemies:
                    self.game_state._set_enemy_intent(enemy)
                
                # 回合结束时，玩家格挡清零，能量重置
                player.block = 0
                player.energy = player.max_energy
                
                # 清空手牌，重新抽牌
                player.hand = []
                player.draw_cards(5)
                
                self.wait_for_key()
                turn += 1
            
            elif choice == "V":
                # 查看弃牌堆
        self.clear_screen()
                print(Fore.CYAN + "弃牌堆:" + Style.RESET_ALL)
                if not player.discard_pile:
                    print("弃牌堆为空")
                else:
                    for i, card in enumerate(player.discard_pile, 1):
                        self.print_card_simple(card, i)
                self.wait_for_key()
            
            elif choice == "D":
                # 查看抽牌堆
                self.clear_screen()
                print(Fore.CYAN + "抽牌堆:" + Style.RESET_ALL)
                if not player.draw_pile:
                    print("抽牌堆为空")
                else:
                    for i, card in enumerate(player.draw_pile, 1):
                        self.print_card_simple(card, i)
                self.wait_for_key()
            
            else:
                print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
                self.wait_for_key()
        
        # 战斗结束
        self.game_state.in_combat = False
        
        # 战斗胜利奖励
        gold_reward = random.randint(10, 30)
        self.game_state.player.gold += gold_reward
        
        print(Fore.GREEN + f"战斗胜利！获得 {gold_reward} 金币" + Style.RESET_ALL)
        self.wait_for_key()
        
        # 提供卡牌奖励
        self.offer_card_reward()
        
        # 随机获得药水
        if random.random() < 0.3:  # 30%几率获得药水
            potion = self.get_random_potion()
            if potion and len(self.game_state.player.potions) < self.game_state.player.max_potions:
                self.add_potion_to_player(potion)
                print(Fore.CYAN + f"你获得了药水: {potion.name} - {potion.description}" + Style.RESET_ALL)
                self.wait_for_key()
        
        return True
    
    def rest(self):
        """休息"""
        self.clear_screen()
        self.print_title()
        
        print(Fore.CYAN + "休息处:" + Style.RESET_ALL)
        print("1. 休息 (回复30%最大生命值)")
        print("2. 升级一张卡牌")
        print("3. 返回")
        print()
        
        choice = input("> ")
        
        if choice == "1":
            # 回复生命值
            heal_amount = int(self.game_state.player.max_hp * 0.3)
            self.game_state.player.heal(heal_amount)
            print(Fore.GREEN + f"你休息了一下，回复了 {heal_amount} 点生命值!" + Style.RESET_ALL)
            self.wait_for_key()
        elif choice == "2":
            # 升级卡牌
            self.upgrade_card()
        elif choice == "3":
            return
        else:
            print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
            self.wait_for_key()
            self.rest()
    
    def upgrade_card(self):
        """升级卡牌"""
        self.clear_screen()
        self.print_title()
        
        print(Fore.CYAN + "选择要升级的卡牌:" + Style.RESET_ALL)
        
        # 显示可升级的卡牌
        upgradable_cards = [card for card in self.game_state.player.cards if not card.upgraded]
        
        if not upgradable_cards:
            print(Fore.YELLOW + "没有可升级的卡牌!" + Style.RESET_ALL)
            self.wait_for_key()
            return
        
        for i, card in enumerate(upgradable_cards, 1):
            print(f"{i}. {card.name} - {card.description}")
        
        print(f"{len(upgradable_cards) + 1}. 返回")
        print()
        
        try:
            choice = int(input("> "))
            
            if 1 <= choice <= len(upgradable_cards):
                # 升级卡牌
                card = upgradable_cards[choice - 1]
                card.upgrade()
                print(Fore.GREEN + f"你升级了 {card.name}!" + Style.RESET_ALL)
                self.wait_for_key()
            elif choice == len(upgradable_cards) + 1:
                self.rest()
            else:
                print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
                self.wait_for_key()
                self.upgrade_card()
        except (ValueError, IndexError):
            print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
            self.wait_for_key()
            self.upgrade_card()
    
    def shop(self):
        """商店"""
        self.clear_screen()
        self.print_title()
        
        print(Fore.CYAN + "商店:" + Style.RESET_ALL)
        print(f"你有 {self.game_state.player.gold} 金币")
        print()
        print("商店系统正在开发中...")
        print("1. 返回")
        print()
        
        choice = input("> ")
        
        if choice == "1":
            return
        else:
            print(Fore.RED + "无效的选择，请重试" + Style.RESET_ALL)
        self.wait_for_key()
            self.shop()
    
    def view_deck(self):
        """查看卡组"""
        self.clear_screen()
        self.print_title()
        
        print(Fore.CYAN + "你的卡组:" + Style.RESET_ALL)
        
        # 按类型分类
        cards_by_type = {
            "Attack": [],
            "Skill": [],
            "Power": [],
            "Other": []
        }
        
        for card in self.game_state.player.cards:
            card_type = card.type if card.type in cards_by_type else "Other"
            cards_by_type[card_type].append(card)
        
        # 显示各类型卡牌
        for card_type, type_cards in cards_by_type.items():
            if type_cards:
                if card_type == "Attack":
                    print(Fore.RED + f"\n攻击牌 ({len(type_cards)}):" + Style.RESET_ALL)
                elif card_type == "Skill":
                    print(Fore.GREEN + f"\n技能牌 ({len(type_cards)}):" + Style.RESET_ALL)
                elif card_type == "Power":
                    print(Fore.BLUE + f"\n能力牌 ({len(type_cards)}):" + Style.RESET_ALL)
            else:
                    print(Fore.WHITE + f"\n其他牌 ({len(type_cards)}):" + Style.RESET_ALL)
                
                for card in type_cards:
                    card_name = card.name
                    if card.upgraded:
                        card_name += "+"
                    
                    rarity_color = Fore.WHITE
                    if card.rarity == "Common":
                        rarity_color = Fore.GREEN
                    elif card.rarity == "Uncommon":
                        rarity_color = Fore.BLUE
                    elif card.rarity == "Rare":
                        rarity_color = Fore.MAGENTA
                    elif card.rarity == "Basic":
                        rarity_color = Fore.YELLOW
                    
                    print(f"  {rarity_color}{card_name}{Style.RESET_ALL} - {card.description}")
        
        print("\n按任意键返回...")
        self.wait_for_key()
    
    def view_relics(self):
        """查看遗物"""
        self.clear_screen()
        self.print_title()
        
        print(Fore.CYAN + "你的遗物:" + Style.RESET_ALL)
        
        if not self.game_state.player.relics:
            print(Fore.YELLOW + "你没有遗物!" + Style.RESET_ALL)
        else:
            for relic in self.game_state.player.relics:
                rarity_color = Fore.WHITE
                if relic.rarity == "Common":
                    rarity_color = Fore.GREEN
                elif relic.rarity == "Uncommon":
                    rarity_color = Fore.BLUE
                elif relic.rarity == "Rare":
                    rarity_color = Fore.MAGENTA
                elif relic.rarity == "Boss":
                    rarity_color = Fore.RED
                elif relic.rarity == "Starter":
                    rarity_color = Fore.YELLOW
                
                print(f"  {rarity_color}{relic.name}{Style.RESET_ALL} - {relic.description}")
        
        print("\n按任意键返回...")
        self.wait_for_key()

    def random_event(self):
        """随机事件"""
        self.clear_screen()
        self.print_title()
        
        print(Fore.CYAN + "未知事件:" + Style.RESET_ALL)
        
        # 随机选择一个事件
        events = [
            "宝箱", "商人", "休息处", "战斗", "升级", "治疗"
        ]
        
        event = random.choice(events)
        
        if event == "宝箱":
            print("你发现了一个宝箱!")
            self.open_chest()
        elif event == "商人":
            print("你遇到了一个流浪商人!")
            self.shop()
        elif event == "休息处":
            print("你找到了一个安全的休息处!")
            self.rest()
        elif event == "战斗":
            print("你被埋伏了!")
            self.game_state.start_combat(1, False, False)
            self.combat_loop()
        elif event == "升级":
            print("你找到了一个古老的祭坛，可以升级一张卡牌!")
            self.upgrade_card()
        elif event == "治疗":
            heal_amount = int(self.game_state.player.max_hp * 0.2)
            self.game_state.player.heal(heal_amount)
            print(f"你找到了一个治疗喷泉，回复了 {heal_amount} 点生命值!")
            self.wait_for_key()
    
    def show_help(self):
        """显示帮助信息"""
        self.clear_screen()
        self.print_title()
        
        print(Fore.CYAN + "游戏帮助:" + Style.RESET_ALL)
        print("《杀戮尖塔》是一款融合了卡牌构筑和Roguelike元素的游戏。")
        print("你需要通过战斗、事件和休息来逐步攀登尖塔。")
        print()
        print("游戏流程:")
        print("1. 选择一个角色开始游戏")
        print("2. 在地图上选择路径前进")
        print("3. 通过战斗获取奖励，增强你的卡组")
        print("4. 在商店购买卡牌和遗物")
        print("5. 在休息处回复生命或升级卡牌")
        print("6. 最终击败Boss，通关游戏")
        print()
        print("按任意键返回...")
        self.wait_for_key()
    
    def print_card_simple(self, card, index=None):
        """简单显示卡牌信息"""
        rarity_color = Fore.WHITE
        if card.rarity == "Common":
            rarity_color = Fore.GREEN
        elif card.rarity == "Uncommon":
            rarity_color = Fore.BLUE
        elif card.rarity == "Rare":
            rarity_color = Fore.MAGENTA
        elif card.rarity == "Basic":
            rarity_color = Fore.YELLOW
            
        card_name = card.name
        if card.upgraded:
            card_name += "+"
            
        if index is not None:
            print(f"{index}. {rarity_color}{card_name}{Style.RESET_ALL} [{card.energy_cost}] - {card.description}")
        else:
            print(f"{rarity_color}{card_name}{Style.RESET_ALL} [{card.energy_cost}] - {card.description}")