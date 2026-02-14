"""
Sky-Forge CLI 入口
"""

import argparse
import asyncio
import sys
from pathlib import Path

from src.player import Player
from src.player.sheet import load_sheet, scan_sheets
from src.live import DanmakuClient, RequestHandler


def get_sheets_dir() -> Path:
    """获取曲库目录"""
    # 优先使用环境变量
    if 'SKY_FORGE_SHEETS' in __import__('os').environ:
        return Path(__import__('os').environ['SKY_FORGE_SHEETS'])
    # 默认使用项目根目录下的 sheets
    return Path(__file__).parent.parent / 'sheets'


def cmd_list(args):
    """列出曲库"""
    sheets_dir = get_sheets_dir()
    sheets = scan_sheets(sheets_dir)

    if not sheets:
        print(f"曲库为空，请将乐谱文件放入: {sheets_dir}")
        return

    print(f"曲库目录: {sheets_dir}")
    print(f"共 {len(sheets)} 首曲目:\n")

    for i, path in enumerate(sheets, 1):
        try:
            sheet = load_sheet(path)
            print(f"  {i:3d}. {sheet.name}")
            if sheet.author:
                print(f"       作者: {sheet.author}")
        except Exception as e:
            print(f"  {i:3d}. {path.name} (解析失败: {e})")


def cmd_play(args):
    """播放乐谱"""
    sheets_dir = get_sheets_dir()

    # 查找乐谱
    if args.file:
        sheet_path = Path(args.file)
    else:
        # 按名称或序号查找
        sheets = scan_sheets(sheets_dir)
        if not sheets:
            print("曲库为空")
            return

        try:
            idx = int(args.song) - 1
            if 0 <= idx < len(sheets):
                sheet_path = sheets[idx]
            else:
                print(f"序号超出范围 (1-{len(sheets)})")
                return
        except ValueError:
            # 按名称搜索
            matches = [s for s in sheets if args.song.lower() in s.stem.lower()]
            if not matches:
                print(f"未找到匹配的曲目: {args.song}")
                return
            if len(matches) > 1:
                print(f"找到多个匹配:")
                for m in matches:
                    print(f"  - {m.stem}")
                return
            sheet_path = matches[0]

    # 加载乐谱
    try:
        sheet = load_sheet(sheet_path)
    except Exception as e:
        print(f"加载乐谱失败: {e}")
        return

    print(f"曲目: {sheet.name}")
    if sheet.author:
        print(f"作者: {sheet.author}")
    print(f"BPM: {sheet.bpm}")
    print(f"音符数: {len(sheet.notes)}")
    print()

    # 创建播放器
    player = Player()

    def on_progress(current, total):
        print(f"\r播放进度: {current}/{total}", end='', flush=True)

    def on_complete():
        print("\n演奏完成!")

    player.set_progress_callback(on_progress)
    player.set_complete_callback(on_complete)
    player.load(sheet)

    print("按 Ctrl+C 停止播放")
    print("-" * 40)

    try:
        player.play()
        # 等待播放完成
        while player.is_playing:
            __import__('time').sleep(0.1)
    except KeyboardInterrupt:
        print("\n已停止")
        player.stop()


def cmd_live(args):
    """启动直播间点播模式"""
    room_id = args.room_id
    sessdata = args.sessdata or ""
    sheets_dir = get_sheets_dir()

    print(f"直播间: {room_id}")
    print(f"曲库目录: {sheets_dir}")
    print()

    # 创建播放器和点播处理器
    player = Player()
    handler = RequestHandler(player, sheets_dir)

    # 创建弹幕客户端
    client = DanmakuClient(room_id, sessdata)
    client.set_danmaku_handler(handler.handle_danmaku)

    async def run():
        try:
            await client.start()
            print("按 Ctrl+C 退出")
            print("-" * 40)
            await client.join()
        except asyncio.CancelledError:
            pass
        finally:
            await client.stop()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n正在退出...")


def main():
    parser = argparse.ArgumentParser(
        prog='sky-forge',
        description='光遇钢琴演奏工具'
    )
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # list 命令
    subparsers.add_parser('list', aliases=['ls'], help='列出曲库')

    # play 命令
    play_parser = subparsers.add_parser('play', help='播放乐谱')
    play_parser.add_argument('song', nargs='?', help='曲目名称或序号')
    play_parser.add_argument('-f', '--file', help='直接指定乐谱文件')

    # live 命令
    live_parser = subparsers.add_parser('live', help='启动直播间点播模式')
    live_parser.add_argument('room_id', type=int, help='直播间ID')
    live_parser.add_argument('--sessdata', '-s', default='', help='B站登录cookie (SESSDATA)')

    args = parser.parse_args()

    if args.command in ('list', 'ls'):
        cmd_list(args)
    elif args.command == 'play':
        cmd_play(args)
    elif args.command == 'live':
        cmd_live(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
