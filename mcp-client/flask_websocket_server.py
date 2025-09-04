#!/usr/bin/env python3
"""
基于Flask-SocketIO的简单WebSocket服务器
"""

from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import logging
import json
from datetime import datetime

# 注释掉JSON重写，避免与Flask内部冲突
# 我们将通过其他方式解决Unicode编码问题

# 配置日志
import sys
import os

# 设置环境变量确保UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 配置日志格式和编码
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# 确保日志处理器使用UTF-8编码
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setStream(sys.stdout)

logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 配置Flask JSON编码，确保中文字符不被转义
app.json.ensure_ascii = False

# 配置CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# 创建SocketIO实例
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    logger=True, 
    engineio_logger=False,  # 关闭引擎日志避免Unicode编码问题
    async_mode='threading',
    json=json,  # 使用标准json模块
    ping_timeout=60,  # 增加ping超时时间
    ping_interval=25,  # 增加ping间隔
    max_http_buffer_size=1e8  # 增加缓冲区大小
)

# 存储连接的客户端
connected_clients = {}

@socketio.on_error()
def error_handler(e):
    """处理SocketIO错误"""
    logger.error(f'SocketIO错误: {str(e)}')
    # 清理可能已断开的客户端
    try:
        client_id = request.sid
        if client_id in connected_clients:
            del connected_clients[client_id]
            logger.info(f'清理错误客户端: {client_id}')
    except:
        pass

@app.route('/')
def index():
    """首页"""
    return {
        "message": "Flask-SocketIO WebSocket Server",
        "status": "running",
        "connected_clients": len(connected_clients),
        "timestamp": datetime.now().isoformat()
    }

@app.route('/status')
def status():
    """服务器状态"""
    return {
        "status": "running",
        "connected_clients": len(connected_clients),
        "clients": list(connected_clients.keys()),
        "timestamp": datetime.now().isoformat()
    }

@app.route('/send_update_graph_api', methods=['POST'])
def send_update_graph_api():
    """向所有连接的客户端发送getGraphApi回调消息"""
    try:
        message = {
            'type': 'execute_callback',
            'data': {
                'callback': 'getGraphApi'
            }
        }
        
        # 检查是否有连接的客户端
        if not connected_clients:
            logger.warning('没有连接的客户端，跳过消息发送')
            return {
                'status': 'warning',
                'message': '没有连接的客户端',
                'timestamp': datetime.now().isoformat()
            }
        
        # 向所有连接的客户端发送消息
        try:
            socketio.emit('message', message)
            logger.info(f'已向 {len(connected_clients)} 个客户端发送 getGraphApi 消息')
        except Exception as emit_error:
            logger.error(f'发送消息时出错: {str(emit_error)}')
        
        return {
            'status': 'success',
            'message': f'已向 {len(connected_clients)} 个客户端发送 getGraphApi 消息',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f'发送 getGraphApi 消息时出错: {str(e)}')
        return {
            'status': 'error',
            'message': f'发送消息失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }, 500

@app.route('/send_execute_callback', methods=['POST'])
def send_execute_callback():
    """向所有连接的客户端发送execute_callback消息"""
    try:
        message = {
            'type': 'execute_callback',
            'data': {
                'callback': 'textToImage',
                'params': None
            }
        }
        
        # 检查是否有连接的客户端
        if not connected_clients:
            logger.warning('没有连接的客户端，跳过消息发送')
            return {
                'status': 'warning',
                'message': '没有连接的客户端',
                'timestamp': datetime.now().isoformat()
            }
        
        # 向所有连接的客户端发送消息
        try:
            socketio.emit('message', message)
            logger.info(f'已向 {len(connected_clients)} 个客户端发送 execute_callback 消息')
        except Exception as emit_error:
            logger.error(f'发送消息时出错: {str(emit_error)}')
        
        return {
            'status': 'success',
            'message': f'已向 {len(connected_clients)} 个客户端发送 execute_callback 消息',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f'发送 execute_callback 消息时出错: {str(e)}')
        return {
            'status': 'error',
            'message': f'发送消息失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }, 500

@app.route('/send_send_result', methods=['POST'])
def send_send_result():
    """向所有连接的客户端发送sendResult回调消息"""
    try:
        message = {
            'type': 'execute_callback',
            'data': {
                'callback': 'sendResult',
                'params': {
                    'id': '2',
                    'properties': {
                        'imageURL': 'https://static.chuangyi-keji.com/generate_toolbox_images/69cc9a3269148463/fd08e59016b6f74a/de4a30f7172572ca4ed2a701e04aa327.png'
                    }
                }
            }
        }
        
        # 检查是否有连接的客户端
        if not connected_clients:
            logger.warning('没有连接的客户端，跳过消息发送')
            return {
                'status': 'warning',
                'message': '没有连接的客户端',
                'timestamp': datetime.now().isoformat()
            }
        
        # 向所有连接的客户端发送消息
        try:
            socketio.emit('message', message)
            logger.info(f'已向 {len(connected_clients)} 个客户端发送 sendResult 消息')
        except Exception as emit_error:
            logger.error(f'发送消息时出错: {str(emit_error)}')
        
        return {
            'status': 'success',
            'message': f'已向 {len(connected_clients)} 个客户端发送 sendResult 消息',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f'发送 sendResult 消息时出错: {str(e)}')
        return {
            'status': 'error',
            'message': f'发送消息失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }, 500

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    client_id = request.sid
    connected_clients[client_id] = {
        'connected_at': datetime.now().isoformat(),
        'last_activity': datetime.now().isoformat()
    }
    
    logger.info(f'客户端连接: {client_id}, 当前连接数: {len(connected_clients)}')
    
    # 发送连接确认消息 - 使用英文避免编码问题
    response_data = {
        'client_id': client_id,
        'message': 'Connection successful',
        'message_zh': '连接成功',  # 中文版本
        'timestamp': datetime.now().isoformat()
    }
    
    # 确保JSON编码正确
    logger.info(f'发送连接确认: {json.dumps(response_data, ensure_ascii=False)}')
    emit('connection_established', response_data)

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接"""
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
        logger.info(f'客户端断开: {client_id}, 当前连接数: {len(connected_clients)}')

@socketio.on('message')
def handle_message(data):
    """处理普通消息"""
    client_id = request.sid
    logger.info(f'收到消息 from {client_id}: {data}')
    
    # 更新最后活动时间
    if client_id in connected_clients:
        connected_clients[client_id]['last_activity'] = datetime.now().isoformat()
    
    # 发送响应（使用英文避免编码问题）
    try:
        emit('message_response', {
            'message': f'Server received: {data}',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f'向客户端 {client_id} 发送响应时出错: {str(e)}')
        # 如果发送失败，可能是客户端已断开，清理连接
        if client_id in connected_clients:
            del connected_clients[client_id]
            logger.info(f'清理已断开的客户端: {client_id}')

@socketio.on('chat_message')
def handle_chat_message(data):
    """处理聊天消息"""
    client_id = request.sid
    content = data.get('content', '')
    logger.info(f'收到聊天消息 from {client_id}: {content}')
    
    # 更新最后活动时间
    if client_id in connected_clients:
        connected_clients[client_id]['last_activity'] = datetime.now().isoformat()
    
    # 发送处理中消息
    emit('processing', {
        'status': 'Processing message...',
        'timestamp': datetime.now().isoformat()
    })
    
    # 发送聊天响应
    emit('chat_response', {
        'content': f'Server received chat message: {content}',
        'status': 'completed',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('tool_call')
def handle_tool_call(data):
    """处理工具调用"""
    client_id = request.sid
    tool_name = data.get('tool_name', '')
    params = data.get('params', {})
    
    logger.info(f'收到工具调用 from {client_id}: {tool_name}, params: {params}')
    
    # 更新最后活动时间
    if client_id in connected_clients:
        connected_clients[client_id]['last_activity'] = datetime.now().isoformat()
    
    # 发送工具调用响应
    emit('tool_response', {
        'tool_name': tool_name,
        'result': f'Tool {tool_name} called successfully',
        'result_zh': f'工具 {tool_name} 调用成功',  # 中文版本
        'params': params,
        'status': 'completed',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('ping')
def handle_ping(data):
    """处理ping消息"""
    client_id = request.sid
    logger.debug(f'收到ping from {client_id}')
    
    # 发送pong响应
    emit('pong', {
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('join_room')
def handle_join_room(data):
    """加入房间"""
    client_id = request.sid
    room = data.get('room', 'default')
    
    join_room(room)
    logger.info(f'客户端 {client_id} 加入房间: {room}')
    
    emit('room_joined', {
        'room': room,
        'message': f'Joined room: {room}',
        'message_zh': f'已加入房间: {room}',  # 中文版本
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('leave_room')
def handle_leave_room(data):
    """离开房间"""
    client_id = request.sid
    room = data.get('room', 'default')
    
    leave_room(room)
    logger.info(f'客户端 {client_id} 离开房间: {room}')
    
    emit('room_left', {
        'room': room,
        'message': f'Left room: {room}',
        'message_zh': f'已离开房间: {room}',  # 中文版本
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('broadcast')
def handle_broadcast(data):
    """广播消息"""
    client_id = request.sid
    message = data.get('message', '')
    
    logger.info(f'广播消息 from {client_id}: {message}')
    
    # 广播给所有客户端
    socketio.emit('broadcast_message', {
        'from': client_id,
        'message': message,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('room_message')
def handle_room_message(data):
    """房间消息"""
    client_id = request.sid
    room = data.get('room', 'default')
    message = data.get('message', '')
    
    logger.info(f'房间消息 from {client_id} in {room}: {message}')
    
    # 发送给房间内的所有客户端
    socketio.emit('room_message', {
        'from': client_id,
        'room': room,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }, room=room)

if __name__ == '__main__':
    logger.info("启动Flask-SocketIO WebSocket服务器...")
    logger.info("WebSocket地址: ws://localhost:9004")
    logger.info("HTTP地址: http://localhost:9004")
    
    # 启动服务器
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=9004, 
        debug=False,  # 关闭debug模式避免冲突
        allow_unsafe_werkzeug=True,
        use_reloader=False,  # 禁用重载器避免重复启动
        log_output=True
    )
