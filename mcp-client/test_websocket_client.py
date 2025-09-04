#!/usr/bin/env python3
"""
WebSocket客户端测试脚本
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket客户端"""
    
    def __init__(self, uri: str = "ws://localhost:9004"):
        self.uri = uri
        self.websocket = None
        
    async def connect(self):
        """连接WebSocket服务器"""
        try:
            self.websocket = await websockets.connect(self.uri)
            logger.info(f"已连接到WebSocket服务器: {self.uri}")
            return True
        except Exception as e:
            logger.error(f"连接WebSocket服务器失败: {e}")
            return False
    
    async def send_message(self, message_type: str, data: dict = None):
        """发送消息"""
        if not self.websocket:
            logger.error("WebSocket未连接")
            return
        
        message = {
            "type": message_type,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await self.websocket.send(json.dumps(message, ensure_ascii=False))
            logger.info(f"发送消息: {message_type}")
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
    
    async def receive_messages(self):
        """接收消息"""
        if not self.websocket:
            logger.error("WebSocket未连接")
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"收到消息: {data.get('type')} - {data.get('data')}")
                except json.JSONDecodeError:
                    logger.error(f"解析消息失败: {message}")
        except Exception as e:
            logger.error(f"接收消息失败: {e}")
    
    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()
            logger.info("WebSocket连接已关闭")


async def test_websocket():
    """测试WebSocket功能"""
    client = WebSocketClient()
    
    # 连接服务器
    if not await client.connect():
        return
    
    # 创建接收消息的任务
    receive_task = asyncio.create_task(client.receive_messages())
    
    try:
        # 等待连接建立
        await asyncio.sleep(1)
        
        # 发送ping消息
        await client.send_message("ping")
        await asyncio.sleep(1)
        
        # 发送聊天消息
        await client.send_message("chat_message", {
            "content": "你好，这是一个测试消息",
            "role": "user"
        })
        await asyncio.sleep(2)
        
        # 发送工具调用
        await client.send_message("tool_call", {
            "tool_name": "test_tool",
            "params": {"param1": "value1"}
        })
        await asyncio.sleep(2)
        
        # 发送另一个聊天消息
        await client.send_message("chat_message", {
            "content": "请帮我处理一些数据",
            "role": "user"
        })
        await asyncio.sleep(3)
        
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    finally:
        # 取消接收任务
        receive_task.cancel()
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_websocket())
