# Sky-Forge 项目开发规范

> 本文档定义了项目开发过程中的规范和习惯，供 Claude Code 和所有开发者参考。

---

## 1. Git 提交规范

### 1.1 提交时机

**核心原则：每次代码经过一轮修改、测试、检验通过之后，都要进行 commit，哪怕是再细小的一个功能。**

```
修改代码 → 测试验证 → 通过 → 立即 Commit
```

**具体场景**：
- ✅ 新增一个功能模块 → commit
- ✅ 修复一个 bug → commit
- ✅ 添加一个配置文件 → commit
- ✅ 更新文档 → commit
- ✅ 重构一小段代码 → commit
- ✅ 添加测试用例 → commit

### 1.2 Commit Message 格式

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>

[optional body]

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

#### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | feat(player): add keyboard controller |
| `fix` | Bug 修复 | fix: correct window title matching |
| `docs` | 文档更新 | docs: add development report |
| `chore` | 构建/工具/依赖 | chore: init project structure |
| `refactor` | 代码重构 | refactor: simplify player loop |
| `test` | 测试相关 | test: add keyboard module tests |
| `style` | 代码格式（不影响逻辑） | style: format code |

#### Scope 范围（可选）

根据模块划分：
- `player` - 播放器模块
- `sheet` - 乐谱模块
- `cli` - 命令行接口
- `docs` - 文档
- 无 - 跨模块或全局修改

#### 示例

```bash
# 好的 commit message
feat(player): add keyboard controller with Windows API
fix: correct scan code for semicolon key
docs: add piano player module development report

# 不好的 commit message
update code
fix bug
wip
```

### 1.3 Commit 粒度

**原则：一个 commit 只做一件事**

```
# ✅ 推荐：按功能分开提交
git commit -m "feat(player): add keyboard controller"
git commit -m "feat(player): add sheet parser"
git commit -m "feat: add CLI interface"

# ❌ 不推荐：一个 commit 包含多个功能
git commit -m "feat: add player, sheet parser and CLI"
```

---

## 2. 代码规范

### 2.1 Python 代码风格

- 使用 **4 空格缩进**
- 类名使用 **PascalCase**：`KeyboardController`
- 函数/变量名使用 **snake_case**：`find_game_window`
- 常量使用 **UPPER_CASE**：`WM_KEYDOWN`
- 私有变量/函数前缀 **下划线**：`_set_us_keyboard_layout`

### 2.2 注释规范

```python
def key_down(self, key: str):
    """按下按键

    Args:
        key: 按键字符（小写）

    Raises:
        RuntimeError: 未设置目标窗口
    """
    ...
```

### 2.3 类型注解

```python
from typing import Optional

def find_game_window(self) -> Optional[int]:
    """查找光遇游戏窗口"""
    ...

def press_notes(self, notes: list[str], duration: float = 0.05):
    """同时按下多个音符"""
    ...
```

### 2.4 模块文档字符串

每个模块文件顶部应有文档字符串：

```python
"""
模块名称 - 简短描述

详细说明模块的功能和使用方式。
"""
```

---

## 3. 项目结构规范

```
sky-forge/
├── CLAUDE.md              # 本文件：开发规范
├── README.md              # 项目说明
├── pyproject.toml         # 项目配置
├── requirements.txt       # 依赖列表
├── reports/               # 开发报告
│   └── DEV_REPORT_*.md
├── sheets/                # 乐谱库
│   └── *.json
└── src/                   # 源代码
    ├── __init__.py
    ├── main.py            # 入口
    └── player/            # 模块
        ├── __init__.py
        ├── keyboard.py
        ├── player.py
        └── sheet.py
```

---

## 4. 开发流程

### 4.1 功能开发流程

```
1. 理解需求 → 2. 调研方案 → 3. 设计实现 → 4. 编写代码 → 5. 修复 Lint → 6. 测试验证 → 7. 提交代码 → 8. 编写报告
```

### 4.2 Lint 修复规范 ⚠️ 强制

**每次编辑代码后，必须根据 VSCode 的 Lint 提示修复问题，直到无严重 Lint 错误。**

```
编辑代码 → 检查 VSCode Lint → 修复所有严重错误 → 继续下一步
```

**严重 Lint 错误包括**：
- ❌ 类型错误 (type error)
- ❌ 未定义变量 (undefined variable)
- ❌ 语法错误 (syntax error)
- ❌ 导入错误 (import error)

**可忽略的 Lint 警告**：
- ⚠️ 未使用变量 (unused variable) - 如 `_` 变量
- ⚠️ 文档字符串缺失 (missing docstring) - 非必须
- ⚠️ 行长度超限 (line too long) - 可接受

### 4.2 测试验证

- **必须**：每次功能开发完成后进行手动测试
- **记录**：测试过程中发现的问题记录到开发报告
- **验证**：确保功能在预期环境下正常工作

### 4.3 问题解决流程

```
遇到问题 → 搜索相关资料 → 尝试解决方案 → 测试验证 → 记录到开发报告 → Commit
```

---

## 5. 文档规范

### 5.1 开发报告 (reports/)

每个功能模块开发完成后，创建开发报告：

**命名格式**：`DEV_REPORT_[Module_Name].md`

**内容结构**：
1. 模块概述
2. 技术调研
3. 关键技术实现
4. 踩坑记录
5. 运行要求
6. 参考资料
7. 已知问题

### 5.2 README.md

保持简洁，包含：
- 项目介绍
- 安装方式
- 使用方法
- 致谢

---

## 6. 依赖管理

### 6.1 添加新依赖

1. 更新 `requirements.txt`
2. 更新 `pyproject.toml`
3. Commit 时说明添加依赖的原因

### 6.2 依赖版本

- 使用 `>=` 指定最低版本
- 不指定具体版本号（除非有兼容性问题）

---

## 7. Windows 平台特定规范

### 7.1 管理员权限

涉及 Windows API 的操作需要管理员权限，在文档中明确说明。

### 7.2 路径处理

```python
# ✅ 使用 Path 对象
from pathlib import Path
path = Path("sheets/example.json")

# ✅ 或使用 os.path
import os
path = os.path.join("sheets", "example.json")
```

### 7.3 换行符

Git 配置 `core.autocrlf=true`，允许 Windows 换行符转换。

---

## 8. 调试技巧

### 8.1 日志输出

```python
# 开发调试时使用 print
print(f"[DEBUG] 找到窗口: {hwnd}")

# 后续可替换为 logging
import logging
logging.debug(f"找到窗口: {hwnd}")
```

### 8.2 错误处理

```python
try:
    # 操作
except SpecificException as e:
    print(f"错误: {e}")
    # 适当的处理
```

---

## 9. 参考资源

### 9.1 代码参考

- [SkyMusicPlay-for-Windows](https://github.com/windhide/SkyMusicPlay-for-Windows) - 核心实现参考

### 9.2 规范参考

- [Conventional Commits](https://www.conventionalcommits.org/)
- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

---

## 10. 检查清单

### 功能开发完成前

- [ ] 代码符合 PEP 8 规范
- [ ] 添加了必要的注释和文档字符串
- [ ] 功能已手动测试验证
- [ ] 更新了相关文档
- [ ] Commit message 符合规范
- [ ] 大型功能已编写开发报告

### Commit 前

- [ ] 确认修改已测试通过
- [ ] Commit message 描述清晰
- [ ] 一个 commit 只包含一个逻辑变更

---

*最后更新：2025-02-15*
