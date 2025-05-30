#!/usr/bin/env python3
"""
OpenAI风格的客户端 - 连接到realtimeserverz服务器

这个脚本演示了如何使用类似OpenAI实时API的方式
连接到realtimeserverz服务器。
"""

import os
import json
import argparse
import websocket

def on_open(ws):
    """连接打开时的回调"""
    print("已连接到服务器")
    
    # 发送初始消息
    message = {
        "type": "message",
        "content": "你好，这是一条测试消息"
    }
    ws.send(json.dumps(message))
    print(f"已发送消息: {message['content']}")

def on_message(ws, message):
    """接收消息时的回调"""
    try:
        data = json.loads(message)
        print("收到事件:", json.dumps(data, indent=2))
        
        # 如果收到文本消息，可以发送音频请求
        if data.get("type") == "text":
            print("发送音频请求...")
            ws.send(json.dumps({"type": "audio_request"}))
    
    except json.JSONDecodeError:
        print(f"收到非JSON消息: {message}")

def on_error(ws, error):
    """发生错误时的回调"""
    print(f"错误: {error}")

def on_close(ws, close_status_code, close_msg):
    """连接关闭时的回调"""
    print(f"连接已关闭: {close_status_code} - {close_msg}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="OpenAI风格的客户端连接到realtimeserverz服务器")
    parser.add_argument("--host", default="localhost", help="服务器主机名 (默认: localhost)")
    parser.add_argument("--port", type=int, default=8765, help="服务器端口 (默认: 8765)")
    parser.add_argument("--api-key", default="fake-api-key", help="模拟的API密钥 (默认: fake-api-key)")
    
    args = parser.parse_args()
    
    # ws://localhost:8765?model=gpt-4o-realtime-preview
    # fake-api-key
    # 构建WebSocket URL和头部，类似于OpenAI的API
    url = f"ws://{args.host}:{args.port}?model=gpt-4o-realtime-preview"
    headers = [
        f"Authorization: Bearer {args.api_key}",
        "OpenAI-Beta: realtime=v1"
    ]
    
    # 创建WebSocket连接
    ws = websocket.WebSocketApp(
        url,
        header=headers,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # 运行WebSocket客户端
    print(f"正在连接到服务器: {url}")
    ws.run_forever()

if __name__ == "__main__":
    main()