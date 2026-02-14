"""
乐谱解析模块
支持 JSON 格式的光遇乐谱
"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class Note:
    """单个音符"""
    time: int      # 时间戳 (毫秒)
    key: str       # 按键标识 (如 "1Key0")


@dataclass
class Sheet:
    """乐谱"""
    name: str                    # 歌曲名
    author: str = ""             # 原曲作者
    transcribed_by: str = ""     # 制谱人
    bpm: int = 120               # 节拍
    notes: Optional[list[Note]] = None  # 音符列表
    duration: int = 0            # 总时长 (毫秒)

    def __post_init__(self):
        if self.notes is None:
            self.notes = []
        if self.notes:
            self.duration = max(n.time for n in self.notes)


def parse_sheet(data: dict) -> Sheet:
    """解析乐谱数据"""
    # 兼容多种 JSON 结构
    if isinstance(data, list) and len(data) > 0:
        data = data[0]

    name = data.get('songName') or data.get('name') or '未知曲目'
    author = data.get('author') or ''
    transcribed_by = data.get('transcribedBy') or data.get('transcriber') or ''
    bpm = data.get('bpm', 120)

    # 解析音符
    song_notes = data.get('songNotes', [])
    notes = [Note(time=n['time'], key=n['key']) for n in song_notes]

    return Sheet(
        name=name,
        author=author,
        transcribed_by=transcribed_by,
        bpm=bpm,
        notes=notes,
    )


def load_sheet(file_path: str | Path) -> Sheet:
    """从文件加载乐谱"""
    path = Path(file_path)

    # 尝试多种编码
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'utf-16']
    data = None

    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                data = json.load(f)
            break
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue

    if data is None:
        raise ValueError(f"无法解析乐谱文件: {path}")

    return parse_sheet(data)


def scan_sheets(directory: str | Path) -> list[Path]:
    """扫描目录及子目录下的所有乐谱文件 (.json)"""
    dir_path = Path(directory)
    if not dir_path.exists():
        return []
    # 递归扫描所有子目录
    return list(dir_path.rglob('*.json'))
