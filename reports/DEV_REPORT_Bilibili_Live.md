# 开发报告：B站直播弹幕模块 (Bilibili Live Danmaku)

> 模块开发时间：2025-02-15
> 开发者：Claude Code + Pectics

---

## 1. 模块概述

实现 B 站直播间弹幕接收与点播功能，观众可以通过弹幕点播曲目，实现无人直播互动。

### 核心功能
- B 站直播间 WebSocket 连接
- 实时弹幕接收与解析
- 点播指令识别与处理
- 播放队列管理

---

## 2. 技术调研

### 2.1 开源项目调研

| 项目 | 技术栈 | 特点 | 推荐度 |
|-----|-------|------|-------|
| [blivedm](https://github.com/xfgryujk/blivedm) | Python + WebSocket | 最成熟，支持 web 端和开放平台 | ⭐⭐⭐⭐⭐ |
| [bilibili-api](https://github.com/Nemo2011/bilibili-api) | Python | 全面的 B 站 API 库 | ⭐⭐⭐⭐ |
| [blivec](https://github.com/hyrious/blivec) | Node.js | 轻量 CLI 工具 | ⭐⭐⭐ |

### 2.2 最终选择

**blivedm** - 理由：
- Python 原生，与 sky-forge 技术栈一致
- 使用 WebSocket 协议，实时性好
- 支持多种消息类型（弹幕、礼物、上舰、醒目留言）
- 代码简洁，文档完善

---

## 3. 关键技术实现

### 3.1 项目结构

```
src/
├── main.py              # CLI 入口（添加 live 命令）
├── player/              # 乐谱播放系统
│   ├── controller.py    # 播放控制器
│   ├── keyboard.py      # 键盘控制
│   └── sheet.py         # 乐谱解析
└── live/                # 直播弹幕系统（新建）
    ├── __init__.py      # 模块导出
    ├── client.py        # 弹幕客户端
    └── handler.py       # 点播处理器
```

### 3.2 弹幕客户端 (client.py)

封装 blivedm 库，提供简洁的接口：

```python
class DanmakuClient:
    """B站直播弹幕客户端"""

    def __init__(self, room_id: int, sessdata: str = ""):
        self.room_id = room_id
        self.sessdata = sessdata

    def set_danmaku_handler(self, handler: Callable):
        """设置弹幕处理器"""

    async def start(self):
        """启动客户端"""

    async def stop(self):
        """停止客户端"""
```

### 3.3 点播处理器 (handler.py)

```python
class RequestHandler:
    """点播请求处理器"""

    REQUEST_PREFIXES = ["点播 ", "播放 ", "点歌 ", "来首 "]

    def handle_danmaku(self, msg: DanmakuMessage):
        """处理弹幕，解析点播指令"""

    def request_song(self, song_name: str, requester: str):
        """添加到播放队列"""
```

### 3.4 点播指令格式

| 指令 | 示例 | 说明 |
|-----|------|------|
| `点播 曲名` | `点播 小星星` | 添加到队列 |
| `播放 曲名` | `播放 小星星` | 同上 |
| `点歌 曲名` | `点歌 小星星` | 同上 |
| `队列` | `队列` | 查看当前队列 |
| `跳过` | `跳过` | 跳过当前曲目 |

---

## 4. 踩坑记录

### 4.1 blivedm 版本问题

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| pip 安装失败 | brotli 依赖需要编译 | 先安装 aiohttp，再用 `--no-deps` 安装 blivedm |
| API 不兼容 | PyPI 版本 (0.1.1) 太老 | 从 GitHub 安装最新版本 |

**解决方案**：
```bash
pip install aiohttp
pip install git+https://github.com/xfgryujk/blivedm.git --no-deps
pip install pure-protobuf brotli
```

### 4.2 API 变更

| 旧版本 (0.1.1) | 新版本 (1.1.5) |
|---------------|---------------|
| `blivedm.models` | `blivedm.models.web` |
| `add_handler()` | `set_handler()` |
| 无 pure_protobuf 依赖 | 需要 pure_protobuf |

### 4.3 SESSDATA 格式

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 用户名打码 | 未登录或 SESSDATA 无效 | 使用正确的 SESSDATA cookie |

**获取方式**：
1. 浏览器打开 bilibili.com 并登录
2. F12 → Application → Cookies → bilibili.com
3. 复制 SESSDATA 的值

### 4.4 直播间必须开播

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 连接后无弹幕 | 直播间未开播 | 必须开播才能接收弹幕 |

这是 blivedm 的正常行为，未开播的直播间没有 WebSocket 连接。

### 4.5 编码问题

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| conda run 输出乱码 | Windows GBK 编码 | 使用 `--no-capture-output` 参数 |
| Python 输出乱码 | 控制台编码 | 设置 `PYTHONIOENCODING=utf-8` |

---

## 5. 依赖管理

### 5.1 新增依赖

```
# requirements.txt
aiohttp>=3.7.4
blivedm>=1.1.5
pure-protobuf
brotli
```

### 5.2 安装注意事项

blivedm 1.1.5 需要以下依赖：
- `aiohttp>=3.7.4` - 异步 HTTP 客户端
- `pure-protobuf` - Protocol Buffers 解析
- `brotli` - 压缩解压

---

## 6. 使用方式

### 6.1 命令行

```bash
# 不带登录（用户名会打码）
python -m src.main live <房间号>

# 带登录（获取完整用户名）
python -m src.main live <房间号> --sessdata <你的SESSDATA>
```

### 6.2 示例

```bash
python -m src.main live 1817619678 --sessdata "your_sessdata_here"
```

---

## 7. 参考资料

### 7.1 主要参考
- [blivedm](https://github.com/xfgryujk/blivedm) - B 站直播弹幕库
- [blivedm sample.py](https://github.com/xfgryujk/blivedm/blob/master/sample.py) - 使用示例

### 7.2 相关文档
- [B站直播开放平台](https://open-live.bilibili.com/) - 官方文档
- [Bilibili Live API 协议解释](https://open-live.bilibili.com/document/657d8e34-f926-a133-16c0-300c1afc6e6b)

---

## 8. 后续优化方向

- [ ] 醒目留言 (SC) 优先播放
- [ ] 礼物触发特殊效果
- [ ] 舰长专属点播权限
- [ ] 点播冷却时间限制
- [ ] 正则表达式模糊匹配曲名

---

## 9. 已知问题

| 问题 | 状态 | 备注 |
|-----|------|------|
| 直播间必须开播 | 正常行为 | blivedm 限制 |
| 未登录用户名打码 | 正常行为 | 需要提供 SESSDATA |
| 曲名模糊匹配可能误匹配 | 待优化 | 可添加更智能的匹配 |

---

*报告生成时间：2025-02-15*
