import asyncio
import json
import logging
import os
import base64
import uuid
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Any
from websockets.server import serve, WebSocketServerProtocol

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Session:
    """会话类，用于存储会话配置和状态"""
    def __init__(self, session_id: str):
        self.id = session_id
        self.created_at = time.time()
        self.updated_at = time.time()
        self.config = {
            "modalities": ["text", "audio"],
            "instructions": "",
            "voice": "jingdiannvsheng",  # 默认音色
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "input_audio_transcription": None,
            "turn_detection": None,
            "tools": [],
            "tool_choice": "auto",
            "temperature": 0.8,
            "max_response_output_tokens": 4096,
        }
        self.conversation_items = []
        self.input_audio_buffer = bytearray()

    def update_config(self, config: Dict[str, Any]) -> None:
        """更新会话配置"""
        self.config.update(config)
        self.updated_at = time.time()


class Conversation:
    """对话管理类，用于管理对话历史记录"""
    def __init__(self):
        self.items = []
        
    def add_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """添加对话项"""
        # 为项目添加ID和格式化属性
        if "id" not in item:
            item["id"] = str(uuid.uuid4())
        
        # 添加格式化属性
        if "formatted" not in item:
            item["formatted"] = {}
            
            # 根据内容类型添加格式化属性
            if item.get("type") == "message":
                content = item.get("content", [])
                for c in content:
                    if c.get("type") == "input_text":
                        item["formatted"]["text"] = c.get("text", "")
                    elif c.get("type") == "input_audio":
                        item["formatted"]["audio"] = c.get("audio", "")
                        item["formatted"]["transcript"] = c.get("transcript", "")
                    elif c.get("type") == "text":
                        item["formatted"]["text"] = c.get("text", "")
                    elif c.get("type") == "audio":
                        item["formatted"]["audio"] = c.get("audio", "")
                        item["formatted"]["transcript"] = c.get("transcript", "")
        
        self.items.append(item)
        return item
    
    def get_items(self) -> List[Dict[str, Any]]:
        """获取所有对话项"""
        return self.items
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取对话项"""
        for item in self.items:
            if item.get("id") == item_id:
                return item
        return None
    
    def clear(self) -> None:
        """清空对话历史记录"""
        self.items = []


class RealtimeServer:
    def __init__(self, host="localhost", port=8765, api_key="fake-api-key"):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.audio_file = Path(__file__).parent.parent.parent / "22.mp3"
        self.sessions: Dict[str, Session] = {}  # 会话字典，键为会话ID
        self.client_sessions: Dict[str, str] = {}  # 客户端会话字典，键为客户端ID，值为会话ID
        
        # 检查音频文件是否存在
        if not self.audio_file.exists():
            logger.warning(f"音频文件 {self.audio_file} 不存在")
        else:
            logger.info(f"使用音频文件: {self.audio_file}")
    
    def parse_auth_header(self, auth_header):
        """解析授权头"""
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        return auth_header[7:]  # 移除 "Bearer " 前缀
    
    def validate_api_key(self, api_key):
        """验证API密钥"""
        # 在实际应用中，这里应该进行真正的API密钥验证
        # 现在我们只是简单地检查它是否存在
        return api_key is not None
    
    def parse_query_params(self, path):
        """解析URL查询参数"""
        if "?" not in path:
            return path, {}
        
        path_part, query_part = path.split("?", 1)
        params = {}
        
        for param in query_part.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = urllib.parse.unquote(value)
        
        return path_part, params
    
    def get_or_create_session(self, client_id: str) -> Session:
        """获取或创建会话"""
        if client_id in self.client_sessions:
            session_id = self.client_sessions[client_id]
            return self.sessions[session_id]
        
        # 创建新会话
        session_id = str(uuid.uuid4())
        session = Session(session_id)
        self.sessions[session_id] = session
        self.client_sessions[client_id] = session_id
        return session
    
    async def handle_connection(self, websocket: WebSocketServerProtocol):
        """处理WebSocket连接"""
        client_id = str(id(websocket))
        path = websocket.path
        headers = websocket.request_headers
        
        # 解析路径和查询参数
        path, params = self.parse_query_params(path)
        model = params.get("model", "gpt-4o-realtime-preview-2024-12-17")
        
        # 获取授权头
        auth_header = headers.get("Authorization")
        api_key = self.parse_auth_header(auth_header)
        
        # 检查OpenAI-Beta头
        openai_beta = headers.get("OpenAI-Beta")
        
        logger.info(f"客户端 {client_id} 已连接")
        logger.info(f"路径: {path}, 模型: {model}")
        logger.info(f"OpenAI-Beta: {openai_beta}")
        
        # 验证API密钥
        if not self.validate_api_key(api_key):
            logger.warning(f"客户端 {client_id} 提供了无效的API密钥")
            await websocket.send(json.dumps({
                "type": "error",
                "error": "invalid_api_key",
                "message": "无效的API密钥"
            }))
            return
        
        # 获取或创建会话
        session = self.get_or_create_session(client_id)
        # 创建对话管理器
        conversation = Conversation()
        
        try:
            # 发送会话创建事件
            await websocket.send(json.dumps({
                "type": "server.session.created",
                "session_id": session.id,
                "model": model
            }))
            
            # 处理来自客户端的消息
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"收到来自客户端 {client_id} 的消息: {data}")
                    
                    # 处理不同类型的消息
                    event_type = data.get("type", "")
                    
                    # 处理会话更新
                    if event_type == "session.update":
                        await self.handle_session_update(websocket, session, data)
                    
                    # 处理对话项创建
                    elif event_type == "conversation.item.create":
                        await self.handle_item_create(websocket, session, conversation, data)
                    
                    # 处理响应创建
                    elif event_type == "response.create":
                        await self.handle_response_create(websocket, session, conversation)
                    
                    # 处理响应取消
                    elif event_type == "response.cancel":
                        await self.handle_response_cancel(websocket, session, conversation)
                    
                    # 处理音频缓冲区追加
                    elif event_type == "input_audio_buffer.append":
                        await self.handle_audio_buffer_append(websocket, session, data)
                    
                    # 处理音频缓冲区提交
                    elif event_type == "input_audio_buffer.commit":
                        await self.handle_audio_buffer_commit(websocket, session, conversation)
                    
                    # 处理旧版消息格式
                    elif event_type == "message":
                        await self.handle_message(websocket, data)
                    elif event_type == "audio_request":
                        await self.send_audio(websocket)
                    else:
                        # 默认回复
                        logger.warning(f"未知消息类型: {event_type}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": "unknown_message_type",
                            "message": f"未知消息类型: {event_type}"
                        }))
                        
                except json.JSONDecodeError:
                    logger.error(f"无法解析JSON消息: {message}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "无效的JSON格式"
                    }))
        
        except Exception as e:
            logger.error(f"处理客户端 {client_id} 连接时出错: {str(e)}")
        
        finally:
            logger.info(f"客户端 {client_id} 已断开连接")
    
    async def handle_session_update(self, websocket: WebSocketServerProtocol, session: Session, data: Dict[str, Any]):
        """处理会话更新"""
        session_data = data.get("session", {})
        session.update_config(session_data)
        
        # 发送会话更新成功事件
        await websocket.send(json.dumps({
            "type": "server.session.updated",
            "session_id": session.id
        }))
    
    async def handle_item_create(self, websocket: WebSocketServerProtocol, session: Session, conversation: Conversation, data: Dict[str, Any]):
        """处理对话项创建"""
        item_data = data.get("item", {})
        item = conversation.add_item(item_data)
        
        # 发送对话项创建成功事件
        await websocket.send(json.dumps({
            "type": "server.conversation.item.created",
            "item": item
        }))
    
    async def handle_response_create(self, websocket: WebSocketServerProtocol, session: Session, conversation: Conversation):
        """处理响应创建"""
        # 创建响应项
        response_id = str(uuid.uuid4())
        
        # 发送响应创建事件
        await websocket.send(json.dumps({
            "type": "server.response.created",
            "response_id": response_id
        }))
        
        # 创建助手消息
        assistant_item = {
            "type": "message",
            "role": "assistant",
            "status": "in_progress",
            "content": []
        }
        assistant_item = conversation.add_item(assistant_item)
        
        # 发送输出项添加事件
        await websocket.send(json.dumps({
            "type": "server.response.output_item.added",
            "response_id": response_id,
            "item": assistant_item
        }))
        
        # 模拟处理延迟
        await asyncio.sleep(0.5)
        
        # 添加文本内容
        text_content = "您好，我是AI助手，很高兴为您服务。"
        
        # 发送文本增量事件
        await websocket.send(json.dumps({
            "type": "server.response.text.delta",
            "response_id": response_id,
            "item_id": assistant_item["id"],
            "content_index": 0,
            "delta": text_content
        }))
        
        # 更新助手消息内容
        assistant_item["content"].append({
            "type": "text",
            "text": text_content
        })
        assistant_item["formatted"]["text"] = text_content
        
        # 发送内容部分添加事件
        await websocket.send(json.dumps({
            "type": "server.response.content_part.added",
            "response_id": response_id,
            "item_id": assistant_item["id"],
            "content_index": 0,
            "content": {
                "type": "text",
                "text": text_content
            }
        }))
        
        # 发送音频
        await self.send_audio_response(websocket, response_id, assistant_item)
        
        # 更新助手消息状态
        assistant_item["status"] = "completed"
        
        # 发送输出项完成事件
        await websocket.send(json.dumps({
            "type": "server.response.output_item.done",
            "response_id": response_id,
            "item_id": assistant_item["id"]
        }))
        
        # 发送响应完成事件
        await websocket.send(json.dumps({
            "type": "server.response.done",
            "response_id": response_id
        }))
    
    async def handle_response_cancel(self, websocket: WebSocketServerProtocol, session: Session, conversation: Conversation):
        """处理响应取消"""
        # 发送响应取消事件
        await websocket.send(json.dumps({
            "type": "server.response.cancelled"
        }))
    
    async def handle_audio_buffer_append(self, websocket: WebSocketServerProtocol, session: Session, data: Dict[str, Any]):
        """处理音频缓冲区追加"""
        audio_base64 = data.get("audio", "")
        if audio_base64:
            audio_data = base64.b64decode(audio_base64)
            session.input_audio_buffer.extend(audio_data)
    
    async def handle_audio_buffer_commit(self, websocket: WebSocketServerProtocol, session: Session, conversation: Conversation):
        """处理音频缓冲区提交"""
        # 如果有音频数据，创建用户音频消息
        if session.input_audio_buffer:
            # 模拟语音识别
            transcript = "这是用户说的话的转写文本"
            
            # 创建用户消息
            user_item = {
                "type": "message",
                "role": "user",
                "status": "completed",
                "content": [
                    {
                        "type": "input_audio",
                        "transcript": transcript
                    }
                ]
            }
            user_item = conversation.add_item(user_item)
            user_item["formatted"]["transcript"] = transcript
            
            # 发送对话项创建成功事件
            await websocket.send(json.dumps({
                "type": "server.conversation.item.created",
                "item": user_item
            }))
            
            # 发送音频转写完成事件
            await websocket.send(json.dumps({
                "type": "server.conversation.item.input_audio_transcription.completed",
                "item_id": user_item["id"],
                "transcript": transcript
            }))
            
            # 清空音频缓冲区
            session.input_audio_buffer = bytearray()
    
    async def handle_message(self, websocket: WebSocketServerProtocol, data):
        """处理旧版文本消息"""
        # 模拟处理消息并返回响应
        content = data.get("content", "")
        
        # 发送处理中状态
        await websocket.send(json.dumps({
            "type": "processing",
            "message": "正在处理消息"
        }))
        
        # 模拟处理延迟
        await asyncio.sleep(1)
        
        # 发送文本响应
        await websocket.send(json.dumps({
            "type": "text",
            "content": f"您发送的消息是: {content}"
        }))
        
        # 提示可以请求音频
        await websocket.send(json.dumps({
            "type": "info",
            "message": "您可以发送 audio_request 类型的消息来获取音频响应"
        }))
    
    async def send_audio_response(self, websocket: WebSocketServerProtocol, response_id: str, item: Dict[str, Any]):
        """发送音频响应"""
        if not self.audio_file.exists():
            logger.warning(f"音频文件 {self.audio_file} 不存在")
            return
        
        try:
            # 读取音频文件
            with open(self.audio_file, "rb") as f:
                audio_data = f.read()
            
            # 将音频数据编码为base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 发送音频转写事件
            transcript = "这是AI说的话的转写文本"
            await websocket.send(json.dumps({
                "type": "server.response.audio_transcript.delta",
                "response_id": response_id,
                "item_id": item["id"],
                "content_index": 1,
                "delta": transcript
            }))
            
            # 发送音频增量事件
            await websocket.send(json.dumps({
                "type": "server.response.audio.delta",
                "response_id": response_id,
                "item_id": item["id"],
                "content_index": 1,
                "delta": audio_base64
            }))
            
            # 更新助手消息内容
            item["content"].append({
                "type": "audio",
                "audio": audio_base64,
                "transcript": transcript
            })
            item["formatted"]["audio"] = audio_base64
            item["formatted"]["transcript"] = transcript
            
            # 发送内容部分添加事件
            await websocket.send(json.dumps({
                "type": "server.response.content_part.added",
                "response_id": response_id,
                "item_id": item["id"],
                "content_index": 1,
                "content": {
                    "type": "audio",
                    "audio": audio_base64,
                    "transcript": transcript
                }
            }))
            
            # 发送音频完成事件
            await websocket.send(json.dumps({
                "type": "server.response.audio.done",
                "response_id": response_id,
                "item_id": item["id"],
                "content_index": 1
            }))
            
            logger.info(f"已发送音频文件 {self.audio_file}")
            
        except Exception as e:
            logger.error(f"发送音频文件时出错: {str(e)}")
    
    async def send_audio(self, websocket: WebSocketServerProtocol):
        """发送旧版音频文件"""
        if not self.audio_file.exists():
            await websocket.send(json.dumps({
                "type": "error",
                "error": "audio_file_not_found",
                "message": "音频文件不存在"
            }))
            return
        
        try:
            # 读取音频文件
            with open(self.audio_file, "rb") as f:
                audio_data = f.read()
            
            # 将音频数据编码为base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 发送音频数据
            await websocket.send(json.dumps({
                "type": "audio",
                "format": "mp3",
                "data": audio_base64
            }))
            
            logger.info(f"已发送音频文件 {self.audio_file}")
            
        except Exception as e:
            logger.error(f"发送音频文件时出错: {str(e)}")
            await websocket.send(json.dumps({
                "type": "error",
                "error": "audio_send_error",
                "message": f"发送音频文件时出错: {str(e)}"
            }))
    
    async def start(self):
        """启动WebSocket服务器"""
        # 增加最大消息大小限制到10MB
        async with serve(
            self.handle_connection,
            self.host,
            self.port,
            max_size=10 * 1024 * 1024,  # 10MB
            max_queue=None
        ):
            logger.info(f"服务器已启动，监听 {self.host}:{self.port}")
            await asyncio.Future()  # 运行直到被取消
    
    def run(self):
        """运行服务器（阻塞）"""
        asyncio.run(self.start())


# 如果直接运行此文件，则启动服务器
if __name__ == "__main__":
    server = RealtimeServer()
    server.run()