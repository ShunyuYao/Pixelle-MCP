# Flask WebSocket 服务器

## Unicode编码问题解决方案

如果您遇到日志输出显示Unicode编码（如 `\u8fde\u63a5\u6210\u529f`）的问题，请使用以下方法之一启动服务器：

### 方法1：使用Python启动脚本（推荐）

```bash
cd mcp-client
uv run run_server.py
```

### 方法2：使用Shell启动脚本

```bash
cd mcp-client
./start_server.sh
```

### 方法3：手动设置环境变量

```bash
cd mcp-client
export PYTHONIOENCODING=utf-8
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
uv run flask_websocket_server.py
```

## 问题原因

日志输出Unicode编码的原因是：
1. Python的日志系统没有正确配置UTF-8编码
2. 环境变量没有设置正确的语言环境
3. stdout/stderr没有使用UTF-8编码

## 解决方案说明

我们通过以下方式解决了编码问题：

1. **设置环境变量**：
   - `PYTHONIOENCODING=utf-8`：确保Python使用UTF-8编码
   - `LANG=zh_CN.UTF-8`：设置语言环境
   - `LC_ALL=zh_CN.UTF-8`：设置本地化环境

2. **配置日志系统**：
   - 使用`logging.StreamHandler(sys.stdout)`确保日志输出到stdout
   - 设置正确的日志格式

3. **配置stdout/stderr**：
   - 使用`sys.stdout.reconfigure(encoding='utf-8')`确保输出流使用UTF-8编码

4. **解决SocketIO Unicode编码问题**：
   - 重写`json.dumps`函数，使用`ensure_ascii=False`确保中文字符不被转义
   - 关闭`engineio_logger`避免引擎日志中的Unicode编码问题
   - 在发送的消息中同时提供英文和中文版本，避免WebSocket传输中的编码问题

## 服务器信息

- **WebSocket地址**: ws://localhost:9004
- **HTTP地址**: http://localhost:9004
- **支持的事件**: connect, disconnect, message, chat_message, tool_call, ping, join_room, leave_room, broadcast, room_message

## 测试连接

您可以使用以下JavaScript代码测试WebSocket连接：

```javascript
const socket = io('http://localhost:9004');

socket.on('connect', () => {
    console.log('连接成功');
});

socket.on('connection_established', (data) => {
    console.log('连接确认:', data);
});

socket.on('disconnect', () => {
    console.log('连接断开');
});
```
