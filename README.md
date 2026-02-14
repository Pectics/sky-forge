# Sky-Forge

> Forge your own Sky livestream experience

光遇直播工具集，首个模块：**钢琴自动演奏**

## 功能

- Windows API 键盘模拟 (支持后台演奏)
- JSON 格式乐谱解析
- 播放控制 (开始/暂停/停止)
- 本地曲库管理

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
# 列出曲库
python -m src.main list

# 播放乐谱 (按序号)
python -m src.main play 1

# 播放乐谱 (按名称)
python -m src.main play 小星星
```

## 曲库

将 JSON 格式的乐谱文件放入 `./sheets/` 目录。

乐谱格式：
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

## 致谢

核心实现参考了 [SkyMusicPlay-for-Windows](https://github.com/windhide/SkyMusicPlay-for-Windows) 项目。
