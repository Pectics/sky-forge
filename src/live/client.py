"""
B站直播弹幕客户端
基于 blivedm 库实现
"""

import asyncio
import http.cookies
from dataclasses import dataclass
from typing import Callable, Optional

import aiohttp

import blivedm
import blivedm.models.web as web_models


@dataclass
class DanmakuMessage:
    """弹幕消息"""
    uname: str      # 用户名
    uid: int        # 用户ID
    msg: str        # 消息内容
    room_id: int    # 房间号


class DanmakuClient:
    """B站直播弹幕客户端"""

    def __init__(self, room_id: int, sessdata: str = ""):
        """初始化弹幕客户端

        Args:
            room_id: 直播间ID
            sessdata: B站登录cookie中的SESSDATA（可选，用于获取完整用户名）
        """
        self.room_id = room_id
        self.sessdata = sessdata
        self._session: Optional[aiohttp.ClientSession] = None
        self._client: Optional[blivedm.BLiveClient] = None
        self._on_danmaku: Optional[Callable[[DanmakuMessage], None]] = None
        self._running = False

    def set_danmaku_handler(self, handler: Callable[[DanmakuMessage], None]):
        """设置弹幕处理器

        Args:
            handler: 弹幕处理回调函数
        """
        self._on_danmaku = handler

    def _create_session(self) -> aiohttp.ClientSession:
        """创建带有cookie的session"""
        cookies = http.cookies.SimpleCookie()
        if self.sessdata:
            cookies['SESSDATA'] = self.sessdata
            cookies['SESSDATA']['domain'] = 'bilibili.com'

        session = aiohttp.ClientSession()
        session.cookie_jar.update_cookies(cookies)
        return session

    async def start(self):
        """启动弹幕客户端"""
        if self._running:
            return

        self._session = self._create_session()
        self._client = blivedm.BLiveClient(self.room_id, session=self._session)
        self._client.set_handler(_Handler(self._on_message))
        self._client.start()

        self._running = True
        print(f"[弹幕] 已连接直播间: {self.room_id}")

    async def stop(self):
        """停止弹幕客户端"""
        if not self._running:
            return

        if self._client:
            await self._client.stop_and_close()
            self._client = None

        if self._session:
            await self._session.close()
            self._session = None

        self._running = False
        print("[弹幕] 已断开连接")

    async def join(self):
        """等待客户端运行"""
        if self._client:
            await self._client.join()

    def _on_message(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        """处理弹幕消息"""
        if self._on_danmaku:
            msg = DanmakuMessage(
                uname=message.uname,
                uid=message.uid,
                msg=message.msg,
                room_id=client.room_id
            )
            self._on_danmaku(msg)


class _Handler(blivedm.BaseHandler):
    """blivedm 消息处理器"""

    def __init__(self, callback: Callable):
        self._callback = callback

    def _on_danmaku(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        """弹幕消息"""
        self._callback(client, message)
