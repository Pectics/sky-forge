# 开发报告：音乐播放时序处理 (Playback Timing)

> 模块开发时间：2025-02-15
> 开发者：Claude Code + Pectics

---

## 1. 问题背景

在钢琴演奏模块开发完成后，实际测试发现播放节奏存在严重问题：
- **整体偏快**：歌曲播放速度明显快于正常节奏
- **空拍抢拍**：音符密集区域节奏稳定，但长间隔的空拍后会出现抢拍

---

## 2. 问题分析

### 2.1 乐谱格式分析

根据 [genshin-music wiki](https://github.com/Specy/genshin-music/wiki/Exported-Music-sheet-format) 的说明：

```typescript
type RecordedNote = [index: number, time: number, layer: string]
```

- `time` 是音符的**绝对时间点**（相对于歌曲开始），单位是毫秒
- 不是音符之间的间隔时间

### 2.2 示例乐谱分析

以小星星为例：
```json
{
  "bpm": 100,
  "songNotes": [
    {"time": 0, "key": "1Key0"},
    {"time": 500, "key": "1Key0"},
    {"time": 1000, "key": "1Key7"},
    ...
  ]
}
```

- BPM 标记为 100（每分钟 100 拍）
- 实际音符间隔 500ms（对应 120 BPM）
- **结论**：乐谱的 BPM 标记可能不准确，不应依赖

---

## 3. 错误方案回顾

### 3.1 方案一：相对时间 + BPM 调整（最初版本）

```python
# 错误代码
bpm_factor = 120 / self.sheet.bpm  # 例如 120/100 = 1.2
interval = (sorted_times[idx + 1] - t) / 1000.0 * bpm_factor
time.sleep(interval)
```

**问题**：
1. 使用**相对时间**（上一个音符到这一个音符的间隔）
2. BPM 调整方向**错误**，让歌曲变快而不是变慢

### 3.2 方案二：相对时间 + 精确计时

```python
# 仍然错误
start_time = time.perf_counter()
self.keyboard.press_notes(keys)
elapsed = time.perf_counter() - start_time
remaining = target_interval - elapsed
time.sleep(remaining)
```

**问题**：
- 仍然使用相对时间
- 虽然用 `perf_counter()` 精确计时，但无法解决根本问题

### 3.3 方案三：绝对时间 + 错误的 BPM 调整

```python
# 还是错误
song_start_time = time.perf_counter()
target_time = song_start_time + note_time_ms / 1000.0 * bpm_factor  # bpm_factor 让时间缩短
```

**问题**：
- 虽然用了绝对时间，但 BPM 调整系数让时间缩短
- 结果：歌曲**飞快**

---

## 4. 根本原因

### 4.1 空拍抢拍问题

**场景**：
- 音符 A 在 0ms，持续 50ms
- 音符 B 在 500ms，持续 50ms
- 空拍：500ms - 50ms = 450ms

**相对时间的问题**：
```
按下 A (50ms) → 等待 450ms → 按下 B (50ms)
实际间隔 = 50 + 450 = 500ms ✅ 正确
```

但如果：
- 音符 A 在 0ms
- 音符 B 在 1000ms（间隔更大）
```
按下 A (50ms) → 等待 950ms → 按下 B (50ms)
实际间隔 = 50 + 950 = 1000ms ✅ 还是正确？
```

**问题在于累积误差**：
- `time.sleep()` 精度有限（Windows 上约 10-15ms）
- 每次按键操作本身也有开销
- 多次累积后误差越来越大

### 4.2 BPM 调整问题

**原意**：如果乐谱 BPM 是 100，希望用 120 BPM 的标准速度播放

**错误理解**：
```python
bpm_factor = 120 / 100 = 1.2
interval = original_interval * 1.2  # 间隔变长 → 变慢
```

**实际效果**：间隔变长应该让歌曲变慢，但用户反馈是"飞快"

**真正原因**：乐谱的时间戳已经是正确的，**根本不需要 BPM 调整**！

---

## 5. 最终解决方案

### 5.1 核心思路

**使用绝对时间，不做 BPM 调整**

每个音符都有一个绝对时间点（相对于歌曲开始），我们只需要：
1. 记录歌曲开始时间
2. 计算每个音符的目标时间 = 开始时间 + 音符时间
3. 等待到达目标时间后按下音符

### 5.2 正确代码

```python
def _play_loop(self):
    """播放循环 - 使用绝对时间计时"""

    # 记录歌曲开始时间（绝对时间）
    song_start_time = time.perf_counter()

    for idx in range(total):
        # 当前音符的绝对时间点 (毫秒转秒)
        note_time_ms = sorted_times[idx]
        target_time = song_start_time + note_time_ms / 1000.0

        # 等待到达目标时间点
        now = time.perf_counter()
        wait_time = target_time - now
        if wait_time > 0:
            time.sleep(wait_time)

        # 播放音符
        self.keyboard.press_notes(keys)
```

### 5.3 为什么这样正确？

**示例**：
```
歌曲开始时间: 0.000s

音符1: target = 0.000s → 在 0.000s 按下
音符2: target = 0.500s → 在 0.500s 按下
音符3: target = 1.000s → 在 1.000s 按下
...
音符N: target = 10.000s → 在 10.000s 按下
```

无论中间有多少空拍，每个音符都在其**绝对时间点**触发，自然就不会累积误差。

---

## 6. 关键要点总结

### 6.1 时间处理原则

| 原则 | 说明 |
|-----|------|
| ✅ 使用绝对时间 | 每个音符在固定时间点触发 |
| ❌ 不用相对时间 | 累积误差会越来越大 |
| ❌ 不做 BPM 调整 | 乐谱时间戳已经是正确的 |

### 6.2 精确计时

| 函数 | 精度 | 用途 |
|-----|------|------|
| `time.time()` | 毫秒级 | 一般计时 |
| `time.perf_counter()` | 微秒级 | 高精度计时 ✅ |
| `time.sleep()` | 10-15ms | 不够精确，但可用 |

### 6.3 按键持续时间

- 按键操作本身需要约 50ms（按下 → 等待 → 释放）
- 这个时间**包含在等待时间内**，不需要额外处理
- 因为我们在按下音符**之前**就已经等待到了目标时间

---

## 7. 代码变更记录

### 7.1 最终版本

**文件**: `src/player/controller.py`

```python
def _play_loop(self):
    """播放循环 - 使用绝对时间计时"""
    assert self.sheet is not None
    assert self.sheet.notes is not None

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

    # 记录歌曲开始时间（绝对时间）
    # 直接使用乐谱中的时间，不做 BPM 调整
    song_start_time = time.perf_counter()

    for idx in range(self._current_idx, total):
        # ... 暂停/停止检查 ...

        # 当前音符的绝对时间点 (毫秒转秒)
        note_time_ms = sorted_times[idx]
        target_time = song_start_time + note_time_ms / 1000.0

        # 等待到达目标时间点
        now = time.perf_counter()
        wait_time = target_time - now
        if wait_time > 0:
            time.sleep(wait_time)

        # 播放音符
        keys = notes_by_time[note_time_ms]
        self.keyboard.press_notes(keys)

        # 进度回调
        if self._on_progress:
            self._on_progress(idx + 1, total)

        self._current_idx = idx + 1

    self._is_playing = False
    if self._on_complete:
        self._on_complete()
```

---

## 8. 参考资料

### 8.1 乐谱格式
- [genshin-music Exported Music sheet format](https://github.com/Specy/genshin-music/wiki/Exported-Music-sheet-format)

### 8.2 Python 计时
- [time.perf_counter()](https://docs.python.org/3/library/time.html#time.perf_counter)
- [time.sleep() 精度问题](https://stackoverflow.com/questions/1133857/how-accurate-is-pythons-time-sleep)

---

## 9. 经验教训

1. **理解数据格式的含义**：`time` 是绝对时间点，不是间隔
2. **不要过度设计**：乐谱时间戳已经是正确的，不需要 BPM 调整
3. **绝对时间 vs 相对时间**：绝对时间避免累积误差
4. **测试要覆盖边界情况**：空拍是常见的边界情况
5. **用户反馈很重要**：理论分析可能出错，实际测试才能发现问题

---

*报告生成时间：2025-02-15*
