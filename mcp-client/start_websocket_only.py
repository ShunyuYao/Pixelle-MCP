#!/usr/bin/env python3
"""
只启动WebSocket服务器（不包含API服务器）
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from websocket_server.server import start_websocket_server

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    try:
        # 获取配置
        host = os.getenv("WS_HOST", "0.0.0.0")
        ws_port = int(os.getenv("WS_PORT", "9004"))
        
        logger.info("=" * 50)
        logger.info("启动WebSocket服务器（仅WebSocket）")
        logger.info("=" * 50)
        logger.info(f"WebSocket服务器: {host}:{ws_port}")
        logger.info("支持跨域连接")
        logger.info("=" * 50)
        
        # 只启动WebSocket服务器
        await start_websocket_server(host, ws_port)
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"启动服务器时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
