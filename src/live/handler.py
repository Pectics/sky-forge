"""
点播请求处理器
解析弹幕中的点播指令，管理播放队列
"""

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.player import Player
from src.player.sheet import load_sheet, scan_sheets
from .client import DanmakuMessage


@dataclass
class SongRequest:
    """点播请求"""
    song_name: str      # 曲名
    requester: str      # 点播者
    file_path: Path     # 乐谱文件路径


class RequestHandler:
    """点播请求处理器"""

    # 点播指令前缀
    REQUEST_PREFIXES = ["点播 ", "播放 ", "点歌 ", "来首 "]

    def __init__(self, player: Player, sheets_dir: Path):
        """初始化处理器

        Args:
            player: 播放器实例
            sheets_dir: 曲库目录
        """
        self.player = player
        self.sheets_dir = sheets_dir
        self._queue: list[SongRequest] = []
        self._lock = threading.Lock()
        self._current_request: Optional[SongRequest] = None
        self._sheets_cache: Optional[list[Path]] = None

        # 设置播放完成回调
        self.player.set_complete_callback(self._on_play_complete)

    def handle_danmaku(self, msg: DanmakuMessage):
        """处理弹幕消息

        Args:
            msg: 弹幕消息
        """
        # 显示收到的弹幕
        print(f"[弹幕] {msg.uname}: {msg.msg}")

        # 检查是否是点播指令
        for prefix in self.REQUEST_PREFIXES:
            if msg.msg.startswith(prefix):
                song_name = msg.msg[len(prefix):].strip()
                if song_name:
                    self.request_song(song_name, msg.uname)
                return

        # 检查其他指令
        if msg.msg.strip() == "队列":
            self._show_queue(msg.uname)
        elif msg.msg.strip() == "跳过":
            self._skip_current(msg.uname)

    def request_song(self, song_name: str, requester: str = ""):
        """点播歌曲

        Args:
            song_name: 曲名（支持模糊匹配）
            requester: 点播者
        """
        # 查找乐谱
        sheet_path = self._find_sheet(song_name)
        if not sheet_path:
            print(f"[点播] 未找到曲目: {song_name}")
            return

        request = SongRequest(
            song_name=song_name,
            requester=requester,
            file_path=sheet_path
        )

        with self._lock:
            self._queue.append(request)
            queue_pos = len(self._queue)

        print(f"[点播] {requester} 点播了 {song_name} (队列位置: {queue_pos})")

        # 如果当前没有播放，立即开始
        if not self.player.is_playing:
            self._play_next()

    def _find_sheet(self, song_name: str) -> Optional[Path]:
        """查找乐谱文件

        Args:
            song_name: 曲名（支持模糊匹配）

        Returns:
            乐谱文件路径，未找到返回 None
        """
        # 缓存曲库列表
        if self._sheets_cache is None:
            self._sheets_cache = scan_sheets(self.sheets_dir)

        song_lower = song_name.lower()

        # 精确匹配文件名
        for path in self._sheets_cache:
            if path.stem.lower() == song_lower:
                return path

        # 模糊匹配
        matches = [p for p in self._sheets_cache if song_lower in p.stem.lower()]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            # 多个匹配，选择最短的（通常是最精确的）
            return min(matches, key=lambda p: len(p.stem))

        return None

    def _play_next(self):
        """播放队列中的下一首"""
        with self._lock:
            if not self._queue:
                self._current_request = None
                print("[播放] 队列为空，等待点播...")
                return

            request = self._queue.pop(0)
            self._current_request = request

        try:
            sheet = load_sheet(request.file_path)
            self.player.load(sheet)
            self.player.play()
            print(f"[播放] 开始演奏: {sheet.name} (点播者: {request.requester})")
        except Exception as e:
            print(f"[播放] 加载乐谱失败: {e}")
            self._play_next()  # 尝试下一首

    def _on_play_complete(self):
        """播放完成回调"""
        if self._current_request:
            print(f"[播放] 演奏完成: {self._current_request.song_name}")
        self._play_next()

    def _show_queue(self, requester: str):
        """显示当前队列"""
        with self._lock:
            if not self._queue:
                print("[队列] 当前队列为空")
            else:
                print(f"[队列] 共 {len(self._queue)} 首待播:")
                for i, req in enumerate(self._queue, 1):
                    print(f"  {i}. {req.song_name} (点播者: {req.requester})")

    def _skip_current(self, requester: str):
        """跳过当前曲目"""
        if self.player.is_playing:
            self.player.stop()
            print(f"[跳过] {requester} 跳过了当前曲目")

    @property
    def queue_length(self) -> int:
        """当前队列长度"""
        with self._lock:
            return len(self._queue)
