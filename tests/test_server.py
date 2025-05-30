#!/usr/bin/env python3
"""
测试脚本 - 测试realtimeserverz服务器

这个脚本测试我们的自定义服务器是否能够与Step-Realtime-Console项目兼容。
"""

import asyncio
import json
import base64
import websockets
import argparse

async def test_server(uri="ws://localhost:8765?model=gpt-4o-realtime-preview"):
    """测试服务器"""
    print(f"正在连接到服务器: {uri}")
    
    # 使用additional_headers而不是extra_headers
    headers = [
        ("Authorization", "Bearer fake-api-key"),
        ("OpenAI-Beta", "realtime=v1")
    ]
    
    async with websockets.connect(uri, additional_headers=headers) as websocket:
        print("已连接到服务器")
        
        # 等待会话创建事件
        response = await websocket.recv()
        data = json.loads(response)
        print(f"收到事件: {json.dumps(data, indent=2)}")
        
        if data.get("type") != "server.session.created":
            print("错误: 未收到会话创建事件")
            return
        
        # 更新会话配置
        await websocket.send(json.dumps({
            "type": "session.update",
            "session": {
                "voice": "jingdiannvsheng",
                "temperature": 0.7
            }
        }))
        
        # 等待会话更新事件
        response = await websocket.recv()
        data = json.loads(response)
        print(f"收到事件: {json.dumps(data, indent=2)}")
        
        # 创建用户消息
        await websocket.send(json.dumps({
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
        }))
        
        # 等待用户消息创建事件
        response = await websocket.recv()
        data = json.loads(response)
        print(f"收到事件: {json.dumps(data, indent=2)}")
        
        # 创建响应
        await websocket.send(json.dumps({
            "type": "response.create"
        }))
        
        # 接收所有响应事件
        try:
            while True:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                print(f"收到事件: {data.get('type')}")
                
                # 如果收到响应完成事件，退出循环
                if data.get("type") == "server.response.done":
                    break
        except asyncio.TimeoutError:
            print("超时: 未收到响应完成事件")
        
        # 测试音频缓冲区
        print("\n测试音频缓冲区...")
        
        # 创建一个简单的音频数据
        audio_data = b"test audio data"
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # 追加音频缓冲区
        await websocket.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": audio_base64
        }))
        
        # 提交音频缓冲区
        await websocket.send(json.dumps({
            "type": "input_audio_buffer.commit"
        }))
        
        # 接收音频转写事件
        try:
            while True:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                print(f"收到事件: {data.get('type')}")
                
                # 如果收到音频转写完成事件，退出循环
                if data.get("type") == "server.conversation.item.input_audio_transcription.completed":
                    break
        except asyncio.TimeoutError:
            print("超时: 未收到音频转写完成事件")
        
        print("\n测试完成")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试realtimeserverz服务器")
    parser.add_argument("--host", default="localhost", help="服务器主机名 (默认: localhost)")
    parser.add_argument("--port", type=int, default=8765, help="服务器端口 (默认: 8765)")
    
    args = parser.parse_args()
    uri = f"ws://{args.host}:{args.port}?model=gpt-4o-realtime-preview"
    
    try:
        asyncio.run(test_server(uri))
    except KeyboardInterrupt:
        print("\n程序已终止")
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    main()