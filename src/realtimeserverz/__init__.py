"""
realtimeserverz - 提供类似OpenAI实时API的WebSocket服务器

这个包提供了一个WebSocket服务器，它模拟了OpenAI的实时API接口，
可以用于开发和测试需要实时API的应用程序。
"""

from .server import RealtimeServer

__all__ = ["RealtimeServer"]