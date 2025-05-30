#!/usr/bin/env python3
"""
示例客户端 - 连接到realtimeserverz服务器

这个脚本演示了如何连接到realtimeserverz服务器，
发送消息并接收响应，包括文本和音频数据。
"""

import os
import json
import asyncio
import base64
import argparse
import websockets

async def connect_to_server(uri="ws://localhost:8765"):
    """连接到WebSocket服务器"""
    print(f"正在连接到服务器: {uri}")
    
    async with websockets.connect(uri) as websocket:
        print("已连接到服务器")
        
        # 接收消息的任务
        receive_task = asyncio.create_task(receive_messages(websocket))
        
        try:
            # 发送消息循环
            while True:
                print("\n可用命令:")
                print("1. 发送文本消息")
                print("2. 请求音频")
                print("3. 退出")
                
                choice = input("请选择 (1-3): ")
                
                if choice == "1":
                    message = input("请输入消息: ")
                    await send_text_message(websocket, message)
                elif choice == "2":
                    await request_audio(websocket)
                elif choice == "3":
                    print("正在退出...")
                    break
                else:
                    print("无效的选择，请重试")
        
        except KeyboardInterrupt:
            print("\n接收到中断信号，正在退出...")
        
        finally:
            # 取消接收任务
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass

async def send_text_message(websocket, content):
    """发送文本消息"""
    message = {
        "type": "message",
        "content": content
    }
    await websocket.send(json.dumps(message))
    print(f"已发送消息: {content}")

async def request_audio(websocket):
    """请求音频数据"""
    message = {
        "type": "audio_request"
    }
    await websocket.send(json.dumps(message))
    print("已发送音频请求")

async def receive_messages(websocket):
    """接收并处理来自服务器的消息"""
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get("type", "unknown")
                
                if message_type == "connected":
                    print(f"服务器连接成功: {data.get('message', '')}")
                
                elif message_type == "text":
                    print(f"\n收到文本: {data.get('content', '')}")
                
                elif message_type == "audio":
                    print("\n收到音频数据")
                    # 保存音频文件
                    audio_format = data.get("format", "mp3")
                    audio_data = base64.b64decode(data.get("data", ""))
                    
                    filename = f"received_audio.{audio_format}"
                    with open(filename, "wb") as f:
                        f.write(audio_data)
                    
                    print(f"音频已保存为: {filename}")
                
                elif message_type == "error":
                    print(f"\n错误: {data.get('message', '')}")
                
                elif message_type == "info":
                    print(f"\n信息: {data.get('message', '')}")
                
                elif message_type == "processing":
                    print(f"\n处理中: {data.get('message', '')}")
                
                else:
                    print(f"\n收到未知类型的消息: {data}")
            
            except json.JSONDecodeError:
                print(f"\n收到非JSON消息: {message}")
    
    except websockets.exceptions.ConnectionClosed:
        print("\n连接已关闭")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="连接到realtimeserverz服务器")
    parser.add_argument("--host", default="localhost", help="服务器主机名 (默认: localhost)")
    parser.add_argument("--port", type=int, default=8765, help="服务器端口 (默认: 8765)")
    
    args = parser.parse_args()
    uri = f"ws://{args.host}:{args.port}"
    
    try:
        asyncio.run(connect_to_server(uri))
    except KeyboardInterrupt:
        print("\n程序已终止")

if __name__ == "__main__":
    main()