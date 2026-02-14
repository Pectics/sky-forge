# 开发报告：钢琴演奏模块 (Piano Player)

> 模块开发时间：2025-02-15
> 开发者：Claude Code + User

---

## 1. 模块概述

实现光遇（Sky: Children of the Light）游戏内的自动钢琴演奏功能，支持后台按键，用于无人直播场景。

### 核心功能
- JSON 格式乐谱解析
- Windows API 后台键盘模拟
- 播放控制（开始/暂停/停止）
- CLI 命令行接口

---

## 2. 技术调研

### 2.1 开源项目调研

| 项目 | Stars | 技术栈 | 核心技术 | 许可证 |
|-----|-------|-------|---------|-------|
| [SkyMusicPlay-for-Windows](https://github.com/windhide/SkyMusicPlay-for-Windows) | 194 | Electron + Vue + Python | Windows API (SendMessageW) | CC BY-NC |
| [SkyAutoMusic](https://github.com/Tloml-Starry/SkyAutoMusic) | 24 | Python + tkinter | pyautogui + keyboard | 未声明 |
| [LightMeetsPiano](https://github.com/StillMisty/LightMeetsPiano) | 12 | Vue3 + Rust + Tauri2 | 未详细调研 | 未声明 |

### 2.2 技术方案对比

| 方案 | 原理 | 优点 | 缺点 | 结论 |
|-----|------|-----|------|-----|
| **SendMessageW** | 直接发送键盘消息到窗口句柄 | 支持后台、稳定、低延迟 | 仅 Windows、需管理员权限 | ✅ 采用 |
| PostMessageW | 异步发送消息到窗口 | 不阻塞 | 不稳定、可能丢失消息 | ❌ |
| SendInput | 模拟硬件输入 | 更底层 | 需窗口前台 | ❌ |
| pyautogui/keyboard | 模拟全局键盘输入 | 简单、跨平台 | 需窗口前台、易被干扰 | ❌ |

---

## 3. 关键技术实现

### 3.1 Windows API 键盘模拟

**最终采用方案**：`SendMessageW` (同步消息)

```python
# 核心代码结构
SendMessageW(hwnd, WM_KEYDOWN, vk_code, lparam)
SendMessageW(hwnd, WM_KEYUP, vk_code, lparam)
```

**关键参数**：
- `hwnd`: 目标窗口句柄
- `WM_KEYDOWN = 0x0100`: 按键按下消息
- `WM_KEYUP = 0x0101`: 按键释放消息
- `vk_code`: 虚拟键码
- `lparam`: 包含扫描码的参数，格式：`(scan_code << 16) | flags`

### 3.2 必须的初始化操作

#### 3.2.1 CPU 亲和性设置 ⚠️ 重要
```python
process = psutil.Process(os.getpid())
all_cores = list(range(psutil.cpu_count()))
cores_to_use = [core for core in all_cores if core != 0]
process.cpu_affinity(cores_to_use)
```
**原因**：避免与光遇游戏抢占 CPU 核心 0，防止按键丢失。

#### 3.2.2 美式键盘布局设置 ⚠️ 重要
```python
user32.LoadKeyboardLayoutW("00000409", 1)
```
**原因**：中文键盘布局下，部分按键（如 `;` `,` `.` `/`）的扫描码不同。

#### 3.2.3 窗口激活
```python
SendMessageW(hwnd, WM_ACTIVATE, WA_ACTIVE, 0)
```
**原因**：每次发送按键前需要激活窗口，否则按键可能不生效。

### 3.3 按键映射

光遇钢琴 15 键 → 键盘映射：

| 光遇音符 | 键盘按键 | 扫描码 |
|---------|---------|--------|
| Key0-Key4 | Y U I O P | 0x15-0x19 |
| Key5-Key9 | H J K L ; | 0x23-0x27 |
| Key10-Key14 | N M , . / | 0x31-0x35 |

### 3.4 窗口查找

```python
def find_game_window():
    # 方式1: 通过进程名
    if 'sky' in proc.name().lower():
        ...
    # 方式2: 通过窗口标题
    if '光' in title and '遇' in title:
        ...
```

**实际窗口标题**：`光·遇`（带中间点）

---

## 4. 踩坑记录

### 4.1 PostMessageW vs SendMessageW

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 按键无反应 | 使用 PostMessageW（异步） | 改用 SendMessageW（同步） |

### 4.2 键盘布局问题

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 部分按键不生效 | 中文键盘布局扫描码不同 | 每次按键前设置美式布局 |

### 4.3 CPU 核心冲突

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 按键随机丢失 | 与游戏抢占 CPU 核心 0 | 设置 CPU 亲和性避开核心 0 |

### 4.4 窗口标题匹配

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 找不到窗口 | 窗口标题是 `光·遇` 不是 `光遇` | 使用 `'光' in title and '遇' in title` |

### 4.5 管理员权限

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 按键完全无反应 | SendMessageW 需要管理员权限 | 以管理员身份运行 |

---

## 5. 运行要求

### 5.1 必须条件
- ✅ Windows 操作系统
- ✅ 以**管理员身份**运行
- ✅ 光遇游戏已打开
- ✅ 游戏内钢琴界面已打开

### 5.2 依赖
```
pywin32>=305    # Windows API
keyboard>=0.13.5  # 键盘扫描码获取
psutil          # 进程管理和 CPU 亲和性
```

---

## 6. 乐谱格式

### 6.1 JSON 结构
```json
{
  "songName": "歌曲名",
  "author": "作者",
  "bpm": 120,
  "transcribedBy": "制谱人",
  "songNotes": [
    {"time": 0, "key": "1Key0"},
    {"time": 500, "key": "1Key5"}
  ]
}
```

### 6.2 字段说明
| 字段 | 类型 | 说明 |
|-----|------|-----|
| `time` | int | 时间戳（毫秒） |
| `key` | string | 音符标识，格式：`{轨道}Key{编号}` |
| `bpm` | int | 节拍，默认 120 |

---

## 7. 参考资料

### 7.1 主要参考
- [SkyMusicPlay-for-Windows](https://github.com/windhide/SkyMusicPlay-for-Windows) - 核心实现参考
  - `sky-music-server/windhide/playRobot/intel_robot.py` - 键盘模拟
  - `sky-music-server/windhide/static/global_variable.py` - 全局配置
  - `sky-music-server/sky_music_apis.py` - CPU 亲和性设置

### 7.2 Windows API 文档
- [SendMessageW function](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendmessagew)
- [WM_KEYDOWN message](https://learn.microsoft.com/en-us/windows/win32/inputdev/wm-keydown)
- [Keyboard Input Scan Codes](https://learn.microsoft.com/en-us/windows/win32/inputdev/keyboard-input)

---

## 8. 后续优化方向

- [ ] 支持更多乐器（吉他、竖琴等）
- [ ] 乐谱转换（MIDI → JSON）
- [ ] GUI 界面
- [ ] 直播平台集成（B站弹幕点歌）
- [ ] 礼物/舰长权限控制

---

## 9. 已知问题

| 问题 | 状态 | 备注 |
|-----|------|-----|
| 需要管理员权限 | 无法解决 | Windows API 限制 |
| 仅支持 Windows | 待定 | 可用 SendInput 方案支持跨平台，但需前台 |
| 部分特殊按键需单独映射 | 已解决 | 通过 _SPECIAL_KEYS 字典 |

---

*报告生成时间：2025-02-15*
