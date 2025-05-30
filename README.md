# RealtimeServerZ

一个模拟OpenAI实时API的WebSocket服务器，用于开发和测试需要实时API的应用程序。特别适配了Step-Realtime-Console项目，可以作为爱化身实时语音API的替代服务。

## 功能特点

- 提供与OpenAI/爱化身实时API类似的WebSocket接口
- 支持文本消息的发送和接收
- 支持音频数据的请求和发送，使用本地的11.mp3文件作为模拟的语音回复
- 支持API密钥验证
- 支持会话管理和配置更新
- 支持对话历史记录
- 支持VAD（语音活动检测）模式

## 安装

确保你已经安装了Python 3.13或更高版本，然后安装依赖项：

```bash
# 使用uv安装依赖项
uv add websockets pydub
```

## 使用方法

### 启动服务器

```bash
# 使用默认配置启动服务器
python main.py

# 指定主机和端口
python main.py --host 0.0.0.0 --port 8765

# 指定API密钥
python main.py --api-key your-api-key

# 启用调试日志
python main.py --debug
```

### 测试服务器

项目提供了一个测试脚本，用于测试服务器是否正常工作：

```bash
# 运行测试脚本
python tests/test_server.py

# 指定服务器主机和端口
python tests/test_server.py --host localhost --port 8765
```

### 与Step-Realtime-Console项目集成

要将RealtimeServerZ与Step-Realtime-Console项目集成，请按照以下步骤操作：

1. 启动RealtimeServerZ服务器：

```bash
python main.py --host 0.0.0.0 --port 8765
```

2. 在Step-Realtime-Console项目的设置中，将服务器地址设置为：

```
ws://localhost:8765
```

3. API Key可以设置为任意值，因为RealtimeServerZ默认接受任何API Key

4. 点击"连接"按钮，开始使用

## API参考

### WebSocket连接

连接URL格式：`ws://localhost:8765?model=<model_name>`

请求头：
- `Authorization: Bearer <api_key>` - API密钥
- `OpenAI-Beta: realtime=v1` - 指定API版本

### 会话管理

更新会话配置：

```json
{
  "type": "session.update",
  "session": {
    "voice": "jingdiannvsheng",
    "temperature": 0.7,
    "instructions": "你是一个AI助手",
    "modalities": ["text", "audio"],
    "input_audio_format": "pcm16",
    "output_audio_format": "pcm16",
    "turn_detection": { "type": "server_vad" }
  }
}
```

### 对话管理

创建用户消息：

```json
{
  "type": "conversation.item.create",
  "item": {
    "type": "message",
    "role": "user",
    "content": [
      {
        "type": "input_text",
        "text": "你好，这是一条测试消息"
      }
    ]
  }
}
```

创建响应：

```json
{
  "type": "response.create"
}
```

取消响应：

```json
{
  "type": "response.cancel"
}
```

### 音频处理

追加音频缓冲区：

```json
{
  "type": "input_audio_buffer.append",
  "audio": "<base64_encoded_audio>"
}
```

提交音频缓冲区：

```json
{
  "type": "input_audio_buffer.commit"
}
```

## 开发

### 项目结构

```
realtimeserverz/
├── examples/               # 示例客户端
│   ├── client.py           # 交互式客户端
│   └── openai_style_client.py  # OpenAI风格的客户端
├── src/
│   └── realtimeserverz/    # 主要代码
│       ├── __init__.py     # 包初始化
│       ├── __main__.py     # 命令行入口点
│       └── server.py       # WebSocket服务器实现
├── tests/                  # 测试代码
│   └── test_server.py      # 服务器测试脚本
├── 11.mp3                  # 示例音频文件
├── main.py                 # 主入口点
├── pyproject.toml          # 项目配置
└── README.md               # 项目说明
```

### 自定义服务器

你可以通过继承`RealtimeServer`类来自定义服务器的行为：

```python
from realtimeserverz import RealtimeServer

class MyCustomServer(RealtimeServer):
    async def handle_response_create(self, websocket, session, conversation):
        # 自定义响应创建逻辑
        # ...
```

## 许可证

MIT