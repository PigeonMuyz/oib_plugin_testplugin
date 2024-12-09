from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Optional, List
import asyncio
from plugin_base import PluginBase
from utils.logger import setup_logger

logger = setup_logger("TestPlugin")

class TestPlugin(PluginBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router = APIRouter(prefix="/api/test", tags=["test"])
        self.ws_router = APIRouter(prefix="/ws/test", tags=["test"])
        self.active_connections: List[WebSocket] = []
        self.broadcast_task: Optional[asyncio.Task] = None

    @property
    def name(self) -> str:
        return "TestPlugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_router(self) -> Optional[APIRouter]:
        # 注册HTTP路由
        self.router.add_api_route("/hello", self.hello, methods=["GET"])
        # 注册WebSocket路由
        self.ws_router.add_api_websocket_route("", self.websocket_endpoint)
        # 合并两个路由
        combined_router = APIRouter()
        combined_router.include_router(self.router)
        combined_router.include_router(self.ws_router)
        return combined_router

    async def on_load(self) -> bool:
        """插件加载时调用"""
        logger.info("TestPlugin loaded")
        return True

    async def on_enable(self) -> bool:
        """插件启用时调用"""
        logger.info("TestPlugin enabled")
        # 启动广播任务
        self.broadcast_task = asyncio.create_task(self.broadcast_messages())
        return True

    async def on_disable(self) -> bool:
        """插件禁用时调用"""
        logger.info("TestPlugin disabled")
        # 取消广播任务
        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass
        return True

    async def hello(self):
        """测试API端点"""
        return {
            "success": True,
            "message": self.config.get("message", "Hello!"),
            "plugin": self.name,
            "version": self.version
        }

    async def websocket_endpoint(self, websocket: WebSocket):
        """WebSocket处理"""
        await websocket.accept()
        self.active_connections.append(websocket)
        try:
            while True:
                # 接收消息
                data = await websocket.receive_text()
                # 发送响应
                await websocket.send_text(f"Echo: {data}")
        except WebSocketDisconnect:
            self.active_connections.remove(websocket)

    async def broadcast_messages(self):
        """定时广播消息"""
        while True:
            try:
                interval = self.config.get("interval", 60)
                await asyncio.sleep(interval)
                if not self.is_enabled:
                    break
                message = {
                    "type": "broadcast",
                    "plugin": self.name,
                    "message": "Periodic update"
                }
                await self.broadcast_to_all(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Broadcast error: {str(e)}")

    async def broadcast_to_all(self, message: Dict):
        """向所有连接的客户端广播消息"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {str(e)}")
                self.active_connections.remove(connection)

    async def handle_config_update(self):
        """配置更新处理"""
        logger.info("Configuration updated")
        # 重新启动广播任务
        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass
            self.broadcast_task = asyncio.create_task(self.broadcast_messages())
