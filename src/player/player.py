"""
播放控制器
管理乐谱播放、暂停、停止
"""

import threading
import time
from collections import defaultdict
from typing import Callable, Optional

from src.player.keyboard import KeyboardController
from src.player.sheet import Sheet


class Player:
    """播放控制器"""

    def __init__(self, keyboard: Optional[KeyboardController] = None):
        self.keyboard = keyboard or KeyboardController()
        self.sheet: Optional[Sheet] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # 初始未暂停
        self._current_idx = 0
        self._is_playing = False
        self._on_progress: Optional[Callable[[int, int], None]] = None
        self._on_complete: Optional[Callable[[], None]] = None

    def load(self, sheet: Sheet):
        """加载乐谱"""
        self.sheet = sheet
        self._current_idx = 0

    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """设置进度回调 (current, total)"""
        self._on_progress = callback

    def set_complete_callback(self, callback: Callable[[], None]):
        """设置完成回调"""
        self._on_complete = callback

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    @property
    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def play(self):
        """开始/继续播放"""
        if not self.sheet:
            raise RuntimeError("未加载乐谱")

        if self._is_playing and not self.is_paused:
            return  # 已在播放

        if self.is_paused:
            # 恢复播放
            self._pause_event.set()
            return

        # 查找游戏窗口
        if not self.keyboard.hwnd:
            if not self.keyboard.find_game_window():
                raise RuntimeError("未找到光遇游戏窗口")

        # 开始新播放
        self._stop_event.clear()
        self._pause_event.set()
        self._is_playing = True
        self._thread = threading.Thread(target=self._play_loop, daemon=True)
        self._thread.start()

    def _play_loop(self):
        """播放循环"""
        # 按时间分组音符
        notes_by_time = defaultdict(list)
        for note in self.sheet.notes:
            notes_by_time[note.time].append(note.key)

        sorted_times = sorted(notes_by_time.keys())
        total = len(sorted_times)

        if total == 0:
            self._is_playing = False
            if self._on_complete:
                self._on_complete()
            return

        # BPM 调整系数
        bpm_factor = 120 / self.sheet.bpm if self.sheet.bpm else 1.0
        t0 = sorted_times[0]

        for idx in range(self._current_idx, total):
            if self._stop_event.is_set():
                break

            # 等待恢复
            while not self._pause_event.is_set():
                if self._stop_event.is_set():
                    break
                time.sleep(0.05)

            if self._stop_event.is_set():
                break

            t = sorted_times[idx]
            keys = notes_by_time[t]

            # 播放音符
            self.keyboard.press_notes(keys)

            # 进度回调
            if self._on_progress:
                self._on_progress(idx + 1, total)

            # 等待下一个音符
            if idx < total - 1:
                interval = (sorted_times[idx + 1] - t) / 1000.0 * bpm_factor
                if interval > 0:
                    time.sleep(interval)

            self._current_idx = idx + 1

        self._is_playing = False
        if self._on_complete:
            self._on_complete()

    def pause(self):
        """暂停"""
        self._pause_event.clear()

    def resume(self):
        """继续"""
        self._pause_event.set()

    def stop(self):
        """停止"""
        self._stop_event.set()
        self._pause_event.set()  # 确保不会卡在暂停
        self._current_idx = 0
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
