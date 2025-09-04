# WebSocket服务器

这是一个独立的WebSocket服务器，用于第三方通讯。

## 功能特性

- **实时通讯**: 支持WebSocket实时双向通讯
- **消息处理**: 支持多种消息类型处理
- **API接口**: 提供HTTP API接口供第三方调用
- **会话管理**: 支持多客户端会话管理
- **工具调用**: 支持工具调用模拟
- **消息历史**: 维护客户端消息历史

## 架构设计

```
┌─────────────────┐    ┌─────────────────┐
│   第三方客户端   │    │  WebSocket服务器 │
│                 │◄──►│                 │
│  - WebSocket    │    │  - 消息处理      │
│  - HTTP API     │    │  - 会话管理      │
└─────────────────┘    └─────────────────┘
```

## 启动方式

### 1. 独立启动WebSocket服务器

```bash
cd mcp-client
uv run run_websocket_server.py
```

### 2. 环境变量配置

```bash
export WS_HOST="0.0.0.0"      # WebSocket服务器主机
export WS_PORT="9004"         # WebSocket服务器端口
export API_PORT="9005"        # API服务器端口
```

## 服务地址

- **WebSocket服务器**: `ws://localhost:9004`
- **API服务器**: `http://localhost:9005`
- **API文档**: `http://localhost:9005/docs`

## 消息格式

### 客户端发送消息格式

```json
{
    "type": "chat_message",
    "data": {
        "content": "消息内容",
        "role": "user"
    },
    "message_id": "uuid",
    "timestamp": "2024-01-01T00:00:00"
}
```

### 服务器响应消息格式

```json
{
    "type": "chat_response",
    "data": {
        "content": "AI回复内容",
        "status": "completed",
        "model": "gpt-4"
    },
    "message_id": "uuid",
    "timestamp": "2024-01-01T00:00:00"
}
```

## 支持的消息类型

### 客户端消息类型

- `chat_message`: 聊天消息
- `tool_call`: 工具调用
- `ping`: 心跳检测

### 服务器消息类型

- `connection_established`: 连接建立确认
- `chat_response`: 聊天回复
- `tool_response`: 工具调用响应
- `processing`: 处理中状态
- `error`: 错误消息
- `pong`: 心跳响应

## API接口

### 1. 获取服务器状态

```bash
GET /status
```

响应:
```json
{
    "status": "running",
    "connected_clients": 2,
    "server_time": "2024-01-01T00:00:00"
}
```

### 2. 获取客户端列表

```bash
GET /clients
```

响应:
```json
{
    "clients": [
        {
            "client_id": "uuid",
            "connected_at": "2024-01-01T00:00:00",
            "last_activity": "2024-01-01T00:00:00",
            "message_count": 5
        }
    ],
    "total": 1
}
```

### 3. 发送消息给客户端

```bash
POST /send_message
Content-Type: application/json

{
    "content": "消息内容",
    "client_id": "uuid"
}
```

### 4. 调用工具

```bash
POST /call_tool
Content-Type: application/json

{
    "tool_name": "tool_name",
    "params": {"param1": "value1"},
    "client_id": "uuid"
}
```

### 5. 广播消息

```bash
POST /broadcast
Content-Type: application/json

{
    "message_type": "notification",
    "data": {"message": "广播消息内容"}
}
```

## 测试

### 使用测试客户端

```bash
cd mcp-client
uv run test_websocket_client.py
```

### 使用curl测试API

```bash
# 获取状态
curl http://localhost:9005/status

# 获取客户端列表
curl http://localhost:9005/clients

# 发送消息
curl -X POST http://localhost:9005/send_message \
  -H "Content-Type: application/json" \
  -d '{"content": "测试消息", "client_id": "your_client_id"}'
```

## 消息处理

WebSocket服务器支持多种消息类型处理：

1. **聊天消息**: 简单的消息回显功能
2. **工具调用**: 模拟工具调用响应
3. **心跳检测**: 支持ping/pong心跳
4. **错误处理**: 完善的错误消息处理

## 配置说明

### WebSocket服务器配置

- `WS_HOST`: WebSocket服务器主机地址
- `WS_PORT`: WebSocket服务器端口
- `API_PORT`: API服务器端口

### 消息处理配置

在 `server.py` 中可以配置：
- 消息处理逻辑
- 响应格式
- 错误处理方式

## 扩展开发

### 添加新的消息类型

1. 在 `server.py` 的 `handle_message` 方法中添加新的消息类型处理
2. 在 `mcp_integration.py` 中添加相应的处理方法
3. 更新API接口以支持新的消息类型

### 添加新的API接口

1. 在 `api.py` 中添加新的路由
2. 定义相应的请求/响应模型
3. 实现业务逻辑

### 自定义消息处理

1. 修改 `server.py` 中的消息处理逻辑
2. 实现具体的业务处理方法
3. 添加错误处理和重试机制

## 故障排除

### 常见问题

1. **连接失败**: 检查端口是否被占用
2. **消息发送失败**: 检查客户端ID是否正确
3. **消息处理失败**: 检查消息格式是否正确

### 日志查看

服务器会输出详细的日志信息，包括：
- 连接/断开事件
- 消息处理过程
- 错误信息

### 性能监控

可以通过API接口监控：
- 连接客户端数量
- 消息处理状态
- 服务器运行状态
