import argparse
from realtimeserverz import RealtimeServer

def main():
    """启动实时WebSocket服务器"""
    # 配置命令行参数
    parser = argparse.ArgumentParser(description="启动实时WebSocket服务器")
    parser.add_argument("--host", default="localhost", help="服务器主机名 (默认: localhost)")
    parser.add_argument("--port", type=int, default=8765, help="服务器端口 (默认: 8765)")
    parser.add_argument("--api-key", default="fake-api-key", help="API密钥 (默认: fake-api-key)")
    parser.add_argument("--debug", action="store_true", help="启用调试日志")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    print("启动realtimeserverz服务器...")
    server = RealtimeServer(host=args.host, port=args.port, api_key=args.api_key)
    server.run()


if __name__ == "__main__":
    main()
