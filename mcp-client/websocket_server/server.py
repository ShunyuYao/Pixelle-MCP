#!/usr/bin/env python3
"""
独立的WebSocket服务器，用于第三方通讯和MCP交互
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Set, Optional, Any
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class WebSocketMessage:
    """WebSocket消息格式"""
    
    def __init__(self, msg_type: str, data: Any = None, message_id: str = None):
        self.type = msg_type
        self.data = data
        self.message_id = message_id or str(uuid.uuid4())
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "type": self.type,
            "data": self.data,
            "message_id": self.message_id,
            "timestamp": self.timestamp
        }
    
    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str):
        try:
            data = json.loads(json_str)
            return cls(
                msg_type=data.get("type"),
                data=data.get("data"),
                message_id=data.get("message_id")
            )
        except Exception as e:
            logger.error(f"解析WebSocket消息失败: {e}")
            return None


class ClientSession:
    """客户端会话管理"""
    
    def __init__(self, websocket: WebSocketServerProtocol, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.message_history = []
        
    def update_activity(self):
        self.last_activity = datetime.now()
    
    def add_message(self, message: WebSocketMessage):
        self.message_history.append(message)
        self.update_activity()
    
    async def send_message(self, message: WebSocketMessage):
        """发送消息给客户端"""
        try:
            await self.websocket.send(message.to_json())
            logger.debug(f"发送消息给客户端 {self.client_id}: {message.type}")
        except Exception as e:
            logger.error(f"发送消息给客户端 {self.client_id} 失败: {e}")
            # 不抛出异常，避免连接断开


class WebSocketServer:
    """WebSocket服务器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 9004):
        self.host = host
        self.port = port
        self.clients: Dict[str, ClientSession] = {}
        self.running = False
        
    async def handle_client(self, websocket: WebSocketServerProtocol):
        """处理客户端连接"""
        client_id = str(uuid.uuid4())
        session = ClientSession(websocket, client_id)
        self.clients[client_id] = session
        
        logger.info(f"客户端 {client_id} 已连接，当前连接数: {len(self.clients)}")
        
        try:
            # 发送连接确认消息
            welcome_msg = WebSocketMessage(
                msg_type="connection_established",
                data={"client_id": client_id, "server_time": datetime.now().isoformat()}
            )
            await session.send_message(welcome_msg)
            
            # 处理客户端消息
            async for message in websocket:
                await self.handle_message(session, message)
                
        except ConnectionClosed:
            logger.info(f"客户端 {client_id} 连接已关闭")
        except Exception as e:
            logger.error(f"处理客户端 {client_id} 消息时出错: {e}")
        finally:
            # 清理客户端连接
            if client_id in self.clients:
                del self.clients[client_id]
                logger.info(f"客户端 {client_id} 已断开，当前连接数: {len(self.clients)}")
    
    async def handle_message(self, session: ClientSession, message_str: str):
        """处理客户端消息"""
        try:
            message = WebSocketMessage.from_json(message_str)
            if not message:
                await session.send_message(WebSocketMessage(
                    msg_type="error",
                    data={"error": "无效的消息格式"}
                ))
                return
            
            session.add_message(message)
            logger.debug(f"收到客户端 {session.client_id} 消息: {message.type}")
            
            # 根据消息类型处理
            if message.type == "chat_message":
                await self.handle_chat_message(session, message)
            elif message.type == "tool_call":
                await self.handle_tool_call(session, message)
            elif message.type == "ping":
                await session.send_message(WebSocketMessage(
                    msg_type="pong",
                    data={"timestamp": datetime.now().isoformat()}
                ))
            else:
                await session.send_message(WebSocketMessage(
                    msg_type="error",
                    data={"error": f"不支持的消息类型: {message.type}"}
                ))
                
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
            try:
                await session.send_message(WebSocketMessage(
                    msg_type="error",
                    data={"error": str(e)}
                ))
            except Exception as send_error:
                logger.error(f"发送错误消息失败: {send_error}")
    
    async def handle_chat_message(self, session: ClientSession, message: WebSocketMessage):
        """处理聊天消息"""
        try:
            # 发送处理中消息
            processing_msg = WebSocketMessage(
                msg_type="processing",
                data={"status": "正在处理消息..."}
            )
            await session.send_message(processing_msg)
            
            # 简单的消息回显
            content = message.data.get('content', '')
            response_msg = WebSocketMessage(
                msg_type="chat_response",
                data={
                    "content": f"服务器收到消息: {content}",
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
            )
            await session.send_message(response_msg)
            
        except Exception as e:
            logger.error(f"处理聊天消息时出错: {e}")
            try:
                await session.send_message(WebSocketMessage(
                    msg_type="error",
                    data={"error": f"处理聊天消息失败: {str(e)}"}
                ))
            except Exception as send_error:
                logger.error(f"发送错误消息失败: {send_error}")
    
    async def handle_tool_call(self, session: ClientSession, message: WebSocketMessage):
        """处理工具调用"""
        try:
            tool_name = message.data.get("tool_name")
            tool_params = message.data.get("params", {})
            
            # 简单的工具调用模拟
            response_msg = WebSocketMessage(
                msg_type="tool_response",
                data={
                    "tool_name": tool_name,
                    "result": f"工具 {tool_name} 调用成功，参数: {tool_params}",
                    "params": tool_params,
                    "status": "completed"
                }
            )
            await session.send_message(response_msg)
            
        except Exception as e:
            logger.error(f"处理工具调用时出错: {e}")
            try:
                await session.send_message(WebSocketMessage(
                    msg_type="error",
                    data={"error": f"工具调用失败: {str(e)}"}
                ))
            except Exception as send_error:
                logger.error(f"发送错误消息失败: {send_error}")
    
    async def start(self):
        """启动WebSocket服务器"""
        self.running = True
        logger.info(f"启动WebSocket服务器 {self.host}:{self.port}")
        
        # 创建WebSocket服务器
        async with websockets.serve(
            self.handle_client, 
            self.host, 
            self.port
        ):
            logger.info(f"WebSocket服务器已启动，监听 {self.host}:{self.port}")
            logger.info("注意：WebSocket跨域问题通常需要在客户端处理")
            await asyncio.Future()  # 保持服务器运行
    
    def stop(self):
        """停止WebSocket服务器"""
        self.running = False
        logger.info("WebSocket服务器已停止")


# 全局WebSocket服务器实例
websocket_server = None


async def start_websocket_server(host: str = "0.0.0.0", port: int = 9004):
    """启动WebSocket服务器"""
    global websocket_server
    websocket_server = WebSocketServer(host, port)
    await websocket_server.start()


def get_websocket_server() -> Optional[WebSocketServer]:
    """获取WebSocket服务器实例"""
    return websocket_server
