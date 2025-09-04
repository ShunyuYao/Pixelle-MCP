#!/usr/bin/env python3
"""
支持CORS的WebSocket服务器示例
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


class CORSWebSocketServer:
    """支持CORS的WebSocket服务器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 9004):
        self.host = host
        self.port = port
        self.clients: Dict[str, WebSocketServerProtocol] = {}
        
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """处理客户端连接"""
        client_id = str(uuid.uuid4())
        self.clients[client_id] = websocket
        
        # 设置CORS相关的响应头
        if websocket.request_headers.get("Origin"):
            # 允许所有来源
            await websocket.send(json.dumps({
                "type": "connection_established",
                "data": {
                    "client_id": client_id,
                    "cors_enabled": True,
                    "allowed_origins": "*"
                }
            }))
        
        logger.info(f"客户端 {client_id} 已连接，当前连接数: {len(self.clients)}")
        
        try:
            async for message in websocket:
                await self.handle_message(client_id, message)
        except ConnectionClosed:
            logger.info(f"客户端 {client_id} 连接已关闭")
        except Exception as e:
            logger.error(f"处理客户端 {client_id} 消息时出错: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
                logger.info(f"客户端 {client_id} 已断开，当前连接数: {len(self.clients)}")
    
    async def handle_message(self, client_id: str, message: str):
        """处理消息"""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "unknown")
            
            if msg_type == "ping":
                response = {"type": "pong", "timestamp": datetime.now().isoformat()}
            elif msg_type == "chat_message":
                content = data.get("data", {}).get("content", "")
                response = {
                    "type": "chat_response",
                    "data": {"content": f"服务器收到: {content}"}
                }
            else:
                response = {"type": "error", "data": {"error": f"不支持的消息类型: {msg_type}"}}
            
            await self.clients[client_id].send(json.dumps(response))
            
        except json.JSONDecodeError:
            await self.clients[client_id].send(json.dumps({
                "type": "error",
                "data": {"error": "无效的JSON格式"}
            }))
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
    
    async def start(self):
        """启动服务器"""
        # 创建WebSocket服务器，支持CORS
        async with websockets.serve(
            self.handle_client, 
            self.host, 
            self.port,
            # CORS相关配置
            process_request=self.process_request
        ):
            logger.info(f"WebSocket服务器已启动，监听 {self.host}:{self.port}")
            await asyncio.Future()  # 保持服务器运行
    
    async def process_request(self, path, headers):
        """处理请求，设置CORS头"""
        # 检查Origin头
        origin = headers.get("Origin")
        if origin:
            # 允许所有来源
            return (200, [
                ("Access-Control-Allow-Origin", "*"),
                ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
                ("Access-Control-Allow-Headers", "*"),
                ("Access-Control-Allow-Credentials", "true"),
            ], b"")
        return None


async def main():
    """主函数"""
    server = CORSWebSocketServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
