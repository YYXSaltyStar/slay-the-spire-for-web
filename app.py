#!/usr/bin/env python3
import os
import sys
import json
import time
from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit
from io import StringIO
import threading
import logging
import traceback
import argparse
import random

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 导入游戏模块
from src.game import SlayTheSpireGame, EMOJI
from src.models import GameState, Character, Enemy, DB_PATH

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'slay-the-spire-secret')
socketio = SocketIO(app, 
                   cors_allowed_origins="*", 
                   ping_timeout=60,
                   ping_interval=25,
                   async_mode='eventlet',
                   logger=True,
                   engineio_logger=True)

# 存储用户会话
game_sessions = {}

@app.route('/')
def index():
    """主页"""
    logger.info(f"访问主页: {request.remote_addr}")
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    sid = request.sid
    logger.info(f"客户端连接: {sid} ({request.remote_addr})")
    # 可以在这里创建一个新的空游戏对象，或者等待玩家操作
    # 为了简单起见，我们等待'new_game'或'load_game'事件
    socketio.emit('connected', {'sid': sid}, room=sid)

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接"""
    sid = request.sid
    if sid in game_sessions:
        del game_sessions[sid]
    logger.info(f"客户端断开连接: {sid}")

@socketio.on_error_default
def default_error_handler(e):
    """默认错误处理器"""
    logger.error(f"WebSocket错误: {str(e)}")
    if request.sid and request.sid in game_sessions:
        socketio.emit('game_error', {'error': str(e)}, room=request.sid)

def get_game_state_json(game: SlayTheSpireGame):
    """将游戏状态序列化为JSON"""
    if not game or not game.game_state:
        return None

    state = game.game_state
    player = state.player

    # 序列化卡牌
    def serialize_card(card):
        return card.to_dict() if card else None

    # 序列化敌人
    def serialize_enemy(enemy):
        return enemy.to_dict() if enemy else None

    # 序列化遗物
    def serialize_relic(relic):
        return relic.to_dict() if relic else None

    # 序列化药水
    def serialize_potion(potion):
        return potion.to_dict() if potion else None
        
    # 序列化地图节点
    def serialize_node(node):
        return node.to_dict() if node else None

    # 构建JSON对象
    game_state_json = {
        "playerName": game.player_name,
        "floor": state.floor,
        "gameOver": state.game_over,
        "inCombat": state.in_combat,
        "shopPrices": state.shop_prices,
        "player": {
            "name": player.name,
            "characterId": player.character_id,
            "health": player.health,
            "maxHealth": player.max_health,
            "energy": player.energy,
            "maxEnergy": player.max_energy,
            "block": player.block,
            "gold": player.gold,
            "strength": player.strength,
            "dexterity": player.dexterity,
            "focus": player.focus,
            "effects": player.effects,
            "deck": [serialize_card(c) for c in player.deck],
            "hand": [serialize_card(c) for c in player.hand],
            "drawPile": [serialize_card(c) for c in player.draw_pile],
            "discardPile": [serialize_card(c) for c in player.discard_pile],
            "exhaustPile": [serialize_card(c) for c in player.exhaust_pile],
            "relics": [serialize_relic(r) for r in player.relics],
            "potions": [serialize_potion(p) for p in player.potions],
        },
        "currentEnemies": [serialize_enemy(e) for e in state.current_enemies],
        "map": {
            "nodes": [[serialize_node(node) for node in row] for row in game.map_nodes],
            "currentNode": serialize_node(game.current_node)
        },
        "currentEvent": state.current_event.to_dict() if state.current_event else None,
        "rewards": state.rewards,
        "screen": state.screen # 新增：当前界面（map, combat, rewards, shop, rest, event）
    }
    
    return game_state_json

def emit_update(sid):
    """向客户端发送最新的游戏状态"""
    game = game_sessions.get(sid)
    if game:
        state_json = get_game_state_json(game)
        socketio.emit('update_state', state_json, room=sid)
        logger.info(f"Sent update_state to {sid}")
    else:
        # 如果没有游戏会话，可以发送一个空状态或错误
        socketio.emit('update_state', None, room=sid)
        logger.warning(f"No game session found for {sid}, sent null state.")

@socketio.on('new_game')
def handle_new_game(data):
    """开始一个新游戏"""
    sid = request.sid
    try:
        player_name = data.get('playerName', '无名英雄')
        character_id = int(data.get('characterId', 1))
        
        logger.info(f"New game started for SID {sid}: player={player_name}, charID={character_id}")
        
        game = SlayTheSpireGame()
        game.game_state.new_game(character_id, player_name)
        game.player_name = player_name
        game.generate_map()
        
        # 设置初始节点
        if game.map_nodes and game.map_nodes[0]:
            game.current_node = game.map_nodes[0][0]
            game.current_node.visited = True
        
        game_sessions[sid] = game
        emit_update(sid)
        
    except Exception as e:
        logger.error(f"Error starting new game for {sid}: {e}")
        logger.error(traceback.format_exc())
        socketio.emit('game_error', {'error': f'创建新游戏失败: {e}'}, room=sid)

@socketio.on('load_game')
def handle_load_game(data):
    """加载游戏"""
    sid = request.sid
    save_name = data.get('saveName')
    if not save_name:
        socketio.emit('game_error', {'error': '需要提供存档名'}, room=sid)
        return

    try:
        game_state = GameState.load_game(save_name)
        if game_state:
            game = SlayTheSpireGame()
            game.game_state = game_state
            game.player_name = save_name
            game.generate_map() # 地图也需要恢复
            
            # 恢复当前节点位置
            current_floor = game_state.floor
            if current_floor < len(game.map_nodes):
                # 找到当前楼层的已访问节点
                for node in game.map_nodes[current_floor]:
                    if node.visited:
                        game.current_node = node
                        break
                # 如果没有找到已访问节点，默认设置为第一个节点
                if not game.current_node:
                    game.current_node = game.map_nodes[current_floor][0]
                    game.current_node.visited = True
            
            # 设置游戏屏幕状态
            if game_state.in_combat:
                game_state.screen = 'combat'
            else:
                game_state.screen = 'map'
            
            game_sessions[sid] = game
            logger.info(f"Game loaded for {sid} from save '{save_name}'")
            emit_update(sid)
        else:
            socketio.emit('game_error', {'error': f"找不到存档 '{save_name}'"}, room=sid)

    except Exception as e:
        logger.error(f"Error loading game for {sid}: {e}")
        logger.error(traceback.format_exc())
        socketio.emit('game_error', {'error': f'加载游戏失败: {e}'}, room=sid)

@socketio.on('player_action')
def handle_player_action(data):
    """处理玩家的通用操作"""
    sid = request.sid
    game = game_sessions.get(sid)
    if not game:
        socketio.emit('game_error', {'error': '游戏会话不存在'}, room=sid)
        return

    action = data.get('action')
    payload = data.get('payload', {})
    
    try:
        logger.info(f"Received action '{action}' from {sid} with payload: {payload}")
        
        # 根据action调用对应的游戏逻辑
        if action == 'choose_path':
            # 假设 payload 是 {'row': y, 'col': x}
            row, col = payload['row'], payload['col']
            game.move_to_node(row, col)

        elif action == 'play_card':
            # 假设 payload 是 {'card_index': idx, 'target_index': tidx}
            card_idx = payload['card_index']
            target_idx = payload.get('target_index') # 可以是None
            game.play_card(card_idx, target_idx)
            
        elif action == 'end_turn':
            game.end_turn()

        elif action == 'choose_reward':
            # payload: {'type': 'card'/'relic'/'gold', 'index': 0}
            game.game_state.choose_reward(payload)

        elif action == 'shop_purchase':
            # payload: {'type': 'card'/'relic'/'potion', 'index': 0}
            game.shop_purchase(payload['type'], payload['index'])
        
        elif action == 'rest_site_choice':
            # payload: {'choice': 'rest'/'upgrade'}
            game.rest_site_action(payload['choice'])
            
        elif action == 'upgrade_card':
            # payload: {'card_uid': 'uuid_of_card_to_upgrade'}
            game.upgrade_card_at_rest_site(payload['card_uid'])

        elif action == 'handle_event':
            # payload: {'choice': 0}
            game.handle_event_choice(payload['choice'])
            
        else:
            logger.warning(f"Unknown action '{action}' from {sid}")
            return
            
        # 动作执行后，发送最新的游戏状态
        emit_update(sid)
        
    except Exception as e:
        logger.error(f"Error processing action '{action}' for {sid}: {e}")
        logger.error(traceback.format_exc())
        socketio.emit('game_error', {'error': f'处理操作失败: {e}'}, room=sid)

@app.route('/simple')
def simple_page():
    """简单测试页面"""
    import datetime
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"访问简单测试页面: {request.remote_addr}")
    return render_template('simple.html', current_time=current_time)

@app.route('/test')
def test_page():
    """测试页面"""
    logger.info(f"访问测试页面: {request.remote_addr}")
    return render_template('test.html')

@app.route('/api/test')
def test_api():
    """测试API是否正常工作"""
    return jsonify({
        "status": "success",
        "message": "API正常工作",
        "time": time.time()
    })

if __name__ == '__main__':
    # 创建templates和static目录（如果不存在）
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='杀戮尖塔命令行游戏Web服务器')
    parser.add_argument('--port', type=int, default=os.environ.get("PORT", 14514), help='服务器端口号')
    args = parser.parse_args()
    
    # 启动服务器
    port = args.port
    logger.info(f"启动服务器: 0.0.0.0:{port}")
    # 使用 gunicorn 时不需要 app.run()
    # 在 Dockerfile 中通过 gunicorn 启动
    # 为了本地开发方便，可以保留这个
    socketio.run(app, host='0.0.0.0', port=port, debug=True) 