#!/usr/bin/env python3
"""
WebSocket代理服务器，解决跨域问题
"""

import asyncio
import json
import logging
from aiohttp import web, WSMsgType
from aiohttp_cors import setup as cors_setup, ResourceOptions
import websockets

logger = logging.getLogger(__name__)


class WebSocketProxy:
    """WebSocket代理服务器"""
    
    def __init__(self, target_ws_url: str = "ws://localhost:9004"):
        self.target_ws_url = target_ws_url
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()
    
    def setup_routes(self):
        """设置路由"""
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_get('/', self.index_handler)
    
    def setup_cors(self):
        """设置CORS"""
        cors = cors_setup(self.app, defaults={
            "*": ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # 为所有路由添加CORS
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def index_handler(self, request):
        """首页处理器"""
        return web.Response(text="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>WebSocket代理测试</title>
        </head>
        <body>
            <h1>WebSocket代理服务器</h1>
            <p>WebSocket地址: <code id="ws-url"></code></p>
            <div>
                <input type="text" id="message" placeholder="输入消息">
                <button onclick="sendMessage()">发送</button>
            </div>
            <div id="messages"></div>
            
            <script>
                const wsUrl = window.location.protocol === 'https:' ? 'wss:' : 'ws:' + '//' + window.location.host + '/ws';
                document.getElementById('ws-url').textContent = wsUrl;
                
                let ws = null;
                
                function connect() {
                    ws = new WebSocket(wsUrl);
                    
                    ws.onopen = function() {
                        console.log('WebSocket连接已建立');
                        addMessage('系统', '连接已建立');
                    };
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        addMessage('服务器', data.data?.content || JSON.stringify(data));
                    };
                    
                    ws.onclose = function() {
                        console.log('WebSocket连接已关闭');
                        addMessage('系统', '连接已关闭');
                    };
                    
                    ws.onerror = function(error) {
                        console.error('WebSocket错误:', error);
                        addMessage('错误', error);
                    };
                }
                
                function sendMessage() {
                    const input = document.getElementById('message');
                    const content = input.value.trim();
                    
                    if (content && ws && ws.readyState === WebSocket.OPEN) {
                        const message = {
                            type: 'chat_message',
                            data: { content: content }
                        };
                        ws.send(JSON.stringify(message));
                        addMessage('客户端', content);
                        input.value = '';
                    }
                }
                
                function addMessage(sender, content) {
                    const messages = document.getElementById('messages');
                    const div = document.createElement('div');
                    div.innerHTML = `<strong>${sender}:</strong> ${content}`;
                    messages.appendChild(div);
                    messages.scrollTop = messages.scrollHeight;
                }
                
                // 页面加载时连接
                connect();
            </script>
        </body>
        </html>
        """, content_type='text/html')
    
    async def websocket_handler(self, request):
        """WebSocket处理器"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        logger.info(f"客户端连接: {request.remote}")
        
        try:
            # 连接到目标WebSocket服务器
            async with websockets.connect(self.target_ws_url) as target_ws:
                logger.info(f"已连接到目标服务器: {self.target_ws_url}")
                
                # 创建两个任务：转发客户端消息和转发服务器消息
                async def forward_to_target():
                    """转发客户端消息到目标服务器"""
                    try:
                        async for msg in ws:
                            if msg.type == WSMsgType.TEXT:
                                # 转发消息到目标服务器
                                await target_ws.send(msg.data)
                                logger.debug(f"转发到目标服务器: {msg.data}")
                            elif msg.type == WSMsgType.ERROR:
                                logger.error(f"WebSocket错误: {ws.exception()}")
                    except Exception as e:
                        logger.error(f"转发到目标服务器时出错: {e}")
                
                async def forward_to_client():
                    """转发目标服务器消息到客户端"""
                    try:
                        async for message in target_ws:
                            # 转发消息到客户端
                            await ws.send_str(message)
                            logger.debug(f"转发到客户端: {message}")
                    except Exception as e:
                        logger.error(f"转发到客户端时出错: {e}")
                
                # 同时运行两个转发任务
                forward_to_target_task = asyncio.create_task(forward_to_target())
                forward_to_client_task = asyncio.create_task(forward_to_client())
                
                # 等待任一任务完成
                done, pending = await asyncio.wait(
                    [forward_to_target_task, forward_to_client_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # 取消未完成的任务
                for task in pending:
                    task.cancel()
                
        except Exception as e:
            logger.error(f"WebSocket处理错误: {e}")
        finally:
            logger.info(f"客户端断开: {request.remote}")
        
        return ws


async def main():
    """主函数"""
    # 创建代理服务器
    proxy = WebSocketProxy()
    
    # 启动服务器
    runner = web.AppRunner(proxy.app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 9006)
    await site.start()
    
    logger.info("WebSocket代理服务器已启动: http://localhost:9006")
    logger.info("目标WebSocket服务器: ws://localhost:9004")
    
    # 保持服务器运行
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        logger.info("正在关闭服务器...")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
