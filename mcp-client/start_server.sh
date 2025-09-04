#!/bin/bash

# 设置环境变量确保UTF-8编码
export PYTHONIOENCODING=utf-8
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 启动Flask WebSocket服务器
echo "启动Flask WebSocket服务器..."
echo "环境变量设置:"
echo "  PYTHONIOENCODING: $PYTHONIOENCODING"
echo "  LANG: $LANG"
echo "  LC_ALL: $LC_ALL"
echo ""

uv run flask_websocket_server.py
