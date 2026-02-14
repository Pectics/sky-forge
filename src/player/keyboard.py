"""
键盘模拟模块 - 使用 Windows API SendMessage
支持后台按键，适用于游戏
需要以管理员权限运行
"""

import ctypes
import os
import time

import psutil
import win32con
import win32gui
import win32process

from typing import Optional

# 设置 CPU 亲和性（避开核心 0，避免与游戏冲突）
_process = psutil.Process(os.getpid())
_all_cores = list(range(psutil.cpu_count()))
_cores_to_use = [core for core in _all_cores if core != 0]
if _cores_to_use:
    _process.cpu_affinity(_cores_to_use)

# Windows API
_user32 = ctypes.windll.user32
SendMessageW = _user32.SendMessageW
MapVirtualKeyW = _user32.MapVirtualKeyW
VkKeyScanW = _user32.VkKeyScanW

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101

# 特殊按键映射 (vk_code, scan_code)
_SPECIAL_KEYS = {
    'semicolon': (0xBA, 0x27),
    'comma': (0xBC, 0x33),
    'period': (0xBE, 0x34),
    'slash': (0xBF, 0x35),
}

# 光遇钢琴按键映射 (15键 -> 键盘)
NOTE_TO_KEY = {
    # 第一排
    "1Key0": "y", "1Key1": "u", "1Key2": "i", "1Key3": "o", "1Key4": "p",
    # 第二排
    "1Key5": "h", "1Key6": "j", "1Key7": "k", "1Key8": "l", "1Key9": ";",
    # 第三排
    "1Key10": "n", "1Key11": "m", "1Key12": ",", "1Key13": ".", "1Key14": "/",
    # 兼容 2Key 格式 (同 1Key)
    "2Key0": "y", "2Key1": "u", "2Key2": "i", "2Key3": "o", "2Key4": "p",
    "2Key5": "h", "2Key6": "j", "2Key7": "k", "2Key8": "l", "2Key9": ";",
    "2Key10": "n", "2Key11": "m", "2Key12": ",", "2Key13": ".", "2Key14": "/",
}


def _set_us_keyboard_layout():
    """设置美式键盘布局"""
    _user32.LoadKeyboardLayoutW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint]
    _user32.LoadKeyboardLayoutW.restype = ctypes.c_void_p
    _user32.LoadKeyboardLayoutW("00000409", 1)


class KeyboardController:
    """键盘控制器 - 使用 SendMessage API 发送后台按键"""

    def __init__(self):
        self.hwnd: Optional[int] = None

    def find_game_window(self) -> Optional[int]:
        """查找光遇游戏窗口"""
        result = {}

        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                title = win32gui.GetWindowText(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    name = proc.name().lower()
                    # 匹配进程名或窗口标题
                    if 'sky' in name or ('光' in title and '遇' in title):
                        result['hwnd'] = hwnd
                except Exception:
                    if '光' in title and '遇' in title:
                        result['hwnd'] = hwnd
            return True

        win32gui.EnumWindows(enum_callback, None)
        self.hwnd = result.get('hwnd')
        return self.hwnd

    def set_window(self, hwnd: int):
        """手动设置目标窗口"""
        self.hwnd = hwnd

    def _get_key_codes(self, key: str) -> tuple[int, int]:
        """获取按键的 VK 码和扫描码"""
        key_lower = key.lower()

        if key_lower in _SPECIAL_KEYS:
            return _SPECIAL_KEYS[key_lower]

        vk_code = VkKeyScanW(ctypes.c_wchar(key)) & 0xFF
        scan_code = MapVirtualKeyW(vk_code, 0)
        return vk_code, scan_code

    def key_down(self, key: str):
        """按下按键"""
        if not self.hwnd:
            raise RuntimeError("未设置目标窗口")

        _set_us_keyboard_layout()
        vk_code, scan_code = self._get_key_codes(key)
        lparam = (scan_code << 16) | 1

        SendMessageW(self.hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
        SendMessageW(self.hwnd, WM_KEYDOWN, vk_code, lparam)

    def key_up(self, key: str):
        """释放按键"""
        if not self.hwnd:
            raise RuntimeError("未设置目标窗口")

        _set_us_keyboard_layout()
        vk_code, scan_code = self._get_key_codes(key)
        lparam = (scan_code << 16) | 0xC0000001

        SendMessageW(self.hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
        SendMessageW(self.hwnd, WM_KEYUP, vk_code, lparam)

    def key_press(self, key: str, duration: float = 0.05):
        """按下并释放按键"""
        self.key_down(key)
        time.sleep(duration)
        self.key_up(key)

    def press_notes(self, notes: list[str], duration: float = 0.05):
        """同时按下多个音符 (和弦)"""
        keys = [NOTE_TO_KEY.get(note) for note in notes if NOTE_TO_KEY.get(note)]
        if not keys:
            return

        # 按下所有键
        for key in keys:
            self.key_down(key)
        time.sleep(duration)
        # 释放所有键
        for key in keys:
            self.key_up(key)
