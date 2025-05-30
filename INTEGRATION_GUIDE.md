# RealtimeServerZ 与 Step-Realtime-Console 集成指南

本指南将帮助您将RealtimeServerZ自定义服务器与Step-Realtime-Console项目集成，实现本地的实时语音交互体验。

## 集成概述

RealtimeServerZ现在完全兼容Step-Realtime-Console项目，可以作为爱化身实时语音API的本地替代方案。集成后您可以：

- 使用本地服务器进行实时语音交互测试
- 避免依赖外部API服务
- 使用自定义音频文件进行语音回复
- 完全控制服务器行为和响应

## 前置要求

1. Python 3.13或更高版本
2. Bun运行时（用于Step-Realtime-Console）
3. 已安装的依赖项

## 步骤一：启动RealtimeServerZ服务器

1. 在RealtimeServerZ项目目录中，启动服务器：

```bash
python main.py --host 0.0.0.0 --port 8765 --debug
```

服务器将在8765端口上启动，并输出以下信息：
```
2025-05-30 11:51:XX,XXX - realtimeserverz.server - INFO - 服务器已启动，监听 0.0.0.0:8765
2025-05-30 11:51:XX,XXX - realtimeserverz.server - INFO - 使用音频文件: /path/to/22.mp3
```

## 步骤二：配置Step-Realtime-Console

1. 进入Step-Realtime-Console项目目录：

```bash
cd Step-Realtime-Console
```

2. 安装依赖项：

```bash
bun install
```

3. 启动开发服务器：

```bash
bun dev
```

项目将在5173端口运行，WebSocket中转服务将在8081端口运行。

## 步骤三：连接配置

1. 在浏览器中访问：`http://localhost:5173`

2. 点击"服务器设置"按钮

3. 填写以下配置：
   - **服务器地址**：`ws://localhost:8765`
   - **模型**：任意值（如：`gpt-4o-realtime-preview`）
   - **API Key**：任意值（如：`test-api-key`）

4. 点击"确定"保存设置

5. 点击"点击连接"按钮开始连接

## 步骤四：测试功能

连接成功后，您可以测试以下功能：

### 文本对话
- 在手动对话模式下，按住麦克风按钮说话
- 服务器将返回文本响应和音频回复

### 实时对话
- 切换到"实时对话"模式
- 启用VAD（语音活动检测）
- 直接开始说话，无需按按钮

### 音频播放
- 服务器将播放预设的22.mp3音频文件作为AI语音回复
- 您可以在对话界面中看到音频波形并播放

## 技术细节

### 消息流程

1. **前端** ↔ **Step-Realtime-Console中转服务器(8081端口)**
2. **中转服务器** ↔ **RealtimeServerZ服务器(8765端口)**

### 支持的API事件

RealtimeServerZ支持以下OpenAI风格的实时API事件：

- `session.update` - 会话配置更新
- `conversation.item.create` - 创建对话项
- `response.create` - 创建响应
- `response.cancel` - 取消响应
- `input_audio_buffer.append` - 追加音频缓冲区
- `input_audio_buffer.commit` - 提交音频缓冲区

### 服务器响应事件

- `server.session.created` - 会话创建
- `server.session.updated` - 会话更新
- `server.conversation.item.created` - 对话项创建
- `server.response.created` - 响应创建
- `server.response.text.delta` - 文本增量
- `server.response.audio.delta` - 音频增量
- `server.response.done` - 响应完成

## 故障排除

### 连接问题

如果遇到连接问题，请检查：

1. RealtimeServerZ服务器是否正在运行（端口8765）
2. Step-Realtime-Console中转服务器是否正在运行（端口8081）
3. 防火墙设置是否允许这些端口的通信
4. 服务器地址是否正确配置为`ws://localhost:8765`

### 音频问题

如果音频播放有问题：

1. 确保22.mp3文件存在于项目根目录
2. 检查浏览器是否授予了麦克风权限
3. 确保音频设备正常工作

### 调试日志

启用调试模式来查看详细日志：

```bash
python main.py --host 0.0.0.0 --port 8765 --debug
```

在Step-Realtime-Console界面中，您可以在"调试日志"面板中查看所有WebSocket事件。

## 自定义配置

### 更换音频文件

要使用不同的音频文件作为AI回复：

1. 将您的音频文件放置在项目根目录
2. 修改`src/realtimeserverz/server.py`中的音频文件路径
3. 重启服务器

### 修改响应内容

要自定义AI的文本响应，编辑`src/realtimeserverz/server.py`中的`handle_response_create`方法。

### 调整服务器配置

您可以通过命令行参数调整服务器配置：

```bash
python main.py --host 0.0.0.0 --port 8765 --api-key your-key --debug
```

## 总结

通过以上步骤，您已经成功将RealtimeServerZ与Step-Realtime-Console项目集成。现在您可以：

- 在本地环境中测试实时语音交互
- 自定义AI响应和音频文件
- 完全控制服务器行为
- 避免依赖外部API服务

如果您遇到任何问题，请查看服务器和浏览器控制台的调试日志以获取更多信息。



```python
# example requires websocket-client library:
# pip install websocket-client

import os
import json
import websocket

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

url = "ws://localhost:8765?model=gpt-4o-realtime-preview-2024-12-17"
headers = [
    "Authorization: Bearer " + "test-api-key",
    "OpenAI-Beta: realtime=v1"
]

def on_open(ws):
    print("Connected to server.")

def on_message(ws, message):
    data = json.loads(message)
    print("Received event:", json.dumps(data, indent=2))

ws = websocket.WebSocketApp(
    url,
    header=headers,
    on_open=on_open,
    on_message=on_message,
)

ws.run_forever()
```