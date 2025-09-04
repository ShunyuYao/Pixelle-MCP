#!/usr/bin/env python3
"""
WebSocket服务器的API接口模块
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .server import WebSocketMessage, get_websocket_server

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="WebSocket API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    """聊天消息模型"""
    content: str
    client_id: Optional[str] = None


class ToolCallRequest(BaseModel):
    """工具调用请求模型"""
    tool_name: str
    params: Dict[str, Any] = {}
    client_id: Optional[str] = None


class BroadcastMessage(BaseModel):
    """广播消息模型"""
    message_type: str
    data: Dict[str, Any] = {}


@app.get("/")
async def root():
    """根路径"""
    return {"message": "WebSocket API Server", "timestamp": datetime.now().isoformat()}


@app.get("/status")
async def get_status():
    """获取服务器状态"""
    server = get_websocket_server()
    if server:
        return {
            "status": "running",
            "connected_clients": len(server.clients),
            "server_time": datetime.now().isoformat()
        }
    else:
        return {"status": "stopped", "server_time": datetime.now().isoformat()}


@app.get("/clients")
async def get_clients():
    """获取连接的客户端列表"""
    server = get_websocket_server()
    if not server:
        raise HTTPException(status_code=503, detail="WebSocket服务器未运行")
    
    clients_info = []
    for client_id, session in server.clients.items():
        clients_info.append({
            "client_id": client_id,
            "connected_at": session.connected_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "message_count": len(session.message_history)
        })
    
    return {"clients": clients_info, "total": len(clients_info)}


@app.post("/send_message")
async def send_message(message: ChatMessage):
    """发送消息给指定客户端"""
    server = get_websocket_server()
    if not server:
        raise HTTPException(status_code=503, detail="WebSocket服务器未运行")
    
    if not message.client_id:
        raise HTTPException(status_code=400, detail="client_id是必需的")
    
    if message.client_id not in server.clients:
        raise HTTPException(status_code=404, detail="客户端未连接")
    
    try:
        ws_message = WebSocketMessage(
            msg_type="chat_message",
            data={"content": message.content, "from_api": True}
        )
        await server.clients[message.client_id].send_message(ws_message)
        
        return {
            "status": "success",
            "message": "消息发送成功",
            "message_id": ws_message.message_id
        }
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")


@app.post("/call_tool")
async def call_tool(request: ToolCallRequest):
    """调用工具"""
    server = get_websocket_server()
    if not server:
        raise HTTPException(status_code=503, detail="WebSocket服务器未运行")
    
    if not request.client_id:
        raise HTTPException(status_code=400, detail="client_id是必需的")
    
    if request.client_id not in server.clients:
        raise HTTPException(status_code=404, detail="客户端未连接")
    
    try:
        ws_message = WebSocketMessage(
            msg_type="tool_call",
            data={
                "tool_name": request.tool_name,
                "params": request.params,
                "from_api": True
            }
        )
        await server.clients[request.client_id].send_message(ws_message)
        
        return {
            "status": "success",
            "message": "工具调用请求已发送",
            "message_id": ws_message.message_id
        }
    except Exception as e:
        logger.error(f"工具调用失败: {e}")
        raise HTTPException(status_code=500, detail=f"工具调用失败: {str(e)}")


@app.post("/broadcast")
async def broadcast_message(message: BroadcastMessage):
    """广播消息给所有客户端"""
    server = get_websocket_server()
    if not server:
        raise HTTPException(status_code=503, detail="WebSocket服务器未运行")
    
    try:
        ws_message = WebSocketMessage(
            msg_type=message.message_type,
            data=message.data
        )
        
        # 发送给所有客户端
        for client_id, session in server.clients.items():
            try:
                await session.send_message(ws_message)
            except Exception as e:
                logger.error(f"广播消息给客户端 {client_id} 失败: {e}")
        
        return {
            "status": "success",
            "message": f"消息已广播给 {len(server.clients)} 个客户端",
            "message_id": ws_message.message_id
        }
    except Exception as e:
        logger.error(f"广播消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"广播消息失败: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    await websocket.accept()
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            # 解析消息
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "unknown")
                
                # 处理消息
                if message_type == "ping":
                    response = {"type": "pong", "timestamp": datetime.now().isoformat()}
                elif message_type == "chat_message":
                    response = {
                        "type": "chat_response",
                        "data": {"content": f"API收到消息: {message_data.get('data', {}).get('content', '')}"}
                    }
                else:
                    response = {"type": "error", "data": {"error": f"不支持的消息类型: {message_type}"}}
                
                # 发送响应
                await websocket.send_text(json.dumps(response, ensure_ascii=False))
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"error": "无效的JSON格式"}
                }, ensure_ascii=False))
                
    except WebSocketDisconnect:
        logger.info("WebSocket客户端断开连接")
    except Exception as e:
        logger.error(f"WebSocket处理错误: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "data": {"error": str(e)}
            }, ensure_ascii=False))
        except:
            pass


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
