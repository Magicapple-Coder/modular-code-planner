# modular-code-planner

**English → [README.md](README.md)**

[![CI](https://github.com/Magicapple-Coder/modular-code-planner/actions/workflows/ci.yml/badge.svg)](https://github.com/Magicapple-Coder/modular-code-planner/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Magicapple-Coder/modular-code-planner)](https://github.com/Magicapple-Coder/modular-code-planner/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](#环境要求)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-SKILL.md-6f42c1.svg)](https://agentskills.io)

> **别再让代码库退化成一坨巨型文件。**
>
> 一个遵循 [Agent Skills](https://agentskills.io) 开放规范的技能包：写码前先规划模块，给每个文件设体积预算，拆分存量巨型文件时保证行为不变。

![modular-code-planner 扫描项目](docs/demo.gif)

它做三件事：

1. **先规划再写码** —— 涉及 3 个以上文件、或预估 200 行以上的任务，先出模块规划方案，你确认后才动手。
2. **守住文件体积预算** —— 300 / 500 行软硬阈值，自带扫描脚本，可对任意项目体检。
3. **安全拆分臃肿文件** —— 一套五阶段重构流程，只搬位置不改行为。

只要 agent 能读 `SKILL.md` 就能用。除扫描脚本需要 Python 3.9+ 外，没有任何依赖。

---

## 要解决的问题

AI 写代码很快，但很少主动停下来拆分。一个工具文件从 80 行长到 1400 行，等到合并冲突频繁出现时已经太晚了。

这个技能把「文件体积」变成一条硬约束：开工前规划模块，编码中盯住行数，拆分存量巨型文件时保证行为不变。

---

## 环境要求

- **Python 3.9+**，仅供 `scripts/check_file_sizes.py` 使用。只用标准库——不需要 `pip install`、不需要虚拟环境、不联网。
- 任何能读 `SKILL.md` 的 agent。指令本身是纯 Markdown，什么依赖都不需要。

---

## 安装

本包就是普通目录。整包复制到你的 agent 所用的 skills 目录即可，无构建步骤、无依赖。

```bash
git clone https://github.com/Magicapple-Coder/modular-code-planner.git
```

常用安装位置：

| Agent | 用户级（对所有项目生效） | 项目级 |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `<项目>/.claude/skills/` |
| Codex CLI | `~/.agents/skills/` | `<项目>/.agents/skills/` |
| Gemini CLI | `~/.gemini/skills/` 或 `~/.agents/skills/` | `<项目>/.gemini/skills/` |
| GitHub Copilot | `~/.copilot/skills/` 或 `~/.agents/skills/` | `<项目>/.github/skills/` 或 `.agents/skills/` |
| Cursor | `~/.cursor/skills/` | `<项目>/.cursor/skills/` |
| OpenCode | `~/.config/opencode/skills/` | `<项目>/.agents/skills/` |
| Windsurf | `~/.codeium/windsurf/skills/` | `<项目>/.windsurf/skills/` |

示例（macOS / Linux）：

```bash
mkdir -p ~/.claude/skills
cp -r modular-code-planner ~/.claude/skills/
```

示例（Windows / PowerShell）：

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse modular-code-planner "$HOME\.claude\skills\"
```

较新的 agent 还会把 `~/.agents/skills/` 当作共享位置读取，所以放一份在那里可能同时服务好几个工具。**请以你所用 agent 的当前文档为准**——skill 的发现路径在不同版本之间会变。

**安装后的结构** —— 目录名必须与 `SKILL.md` 里的 `name` 字段一致：

```
<你的 skills 目录>/
└── modular-code-planner/
    ├── SKILL.md                 # agent 自动加载；双语（英文 + 中文）
    ├── references/
    │   ├── module-split-patterns.md   / .en.md
    │   └── refactoring-workflow.md    / .en.md
    ├── scripts/
    │   └── check_file_sizes.py
    └── tests/                   # 只有你想跑测试套件时才需要
```

整包复制即可。运行时只会读 `SKILL.md`、`references/` 和 `scripts/`，其余目录不参与。

---

## 使用方式

装好后直接用自然语言描述任务，agent 会自动选择对应的工作流。

### 规划新项目

> 帮我用 FastAPI 搭一个服务，要 JWT 认证、Postgres、还有后台任务队列。

agent 会先读 `references/module-split-patterns.md` 里对应技术栈的惯例，然后给出目录树、每个文件的职责、预估行数、依赖方向，**等你确认后才开始写**。

### 体检现有项目

```bash
python3 /path/to/modular-code-planner/scripts/check_file_sizes.py ./src --lang zh
```

```
扫描 412 个代码文件 | 软阈值 >300 行 | 硬阈值 >500 行

== 超阈值文件（需要拆分） ==
  [硬超标]   1842  services/order_service.py
  [硬超标]    734  api/routes.py
  [警告]      412  models/user.py

== 入口文件偏长（目标 <=100 行，应只做装配） ==
  [入口]      287  main.py

== 行数 Top 10 ==
    1842  services/order_service.py
     734  api/routes.py
     ...

汇总: 警告(>300) 1 个, 硬超标(>500) 2 个, 入口偏长(>100) 1 个
```

输出语言默认跟随系统区域设置，可用 `--lang en` / `--lang zh` 强制指定。

### 拆分巨型文件

> 帮我拆分 `services/order_service.py`。

agent 会走五阶段流程：冻结行为 → 只读盘点 → 出方案 → 分步迁移 → 验收交付。**你确认方案之前，它不会动任何文件。**

### 脚本参数

```
python3 scripts/check_file_sizes.py <路径> [选项]

  --soft N            超过 N 行报警告            （默认 300）
  --hard N            超过 N 行报红线            （默认 500）
  --entry-max N       入口文件目标行数           （默认 100）
  --top N             展示行数最多的 N 个文件    （默认 10）
  --ext a,b,c         只扫描这些扩展名
  --ignore a,b        额外忽略的目录名
  --exclude-glob a,b  额外排除的文件名通配       （如 "*.generated.*"）
  --json              输出 JSON
  --lang {auto,en,zh} 输出语言                   （默认 auto）
```

默认覆盖 35 种常见代码扩展名；依赖目录、构建产物、生成文件、类型声明与 lock 文件自动跳过。

输出使用控制台自身的编码；遇到无法渲染的字符会降级成 `?` 而不是直接崩溃。需要 UTF-8 输出时设置 `PYTHONIOENCODING=utf-8`——管道接入其他工具或写日志时很有用。

**退出码**

| 退出码 | 含义 |
|---|---|
| `0` | 没有文件超过硬阈值 |
| `1` | 存在超过硬阈值的文件 |
| `2` | 参数错误，或路径不存在 / 没有可扫描的文件 |

退出码 `2` 是刻意设计的：避免路径写错被当成「项目健康」汇报。

---

## 行数阈值

| 区间 | 状态 | 处理 |
|---|---|---|
| ≤ 300 行 | 健康区 | 目标状态 |
| 301–500 行 | 警告区 | 停止追加职责，立即拆或排期拆 |
| > 500 行 | 红线 | 必须拆分后任务才算完成 |
| 入口文件（`main` / `index` / `app` / `__main__`） | > 100 行 | 入口只应做装配 |

生成代码、lock 文件、类型声明可豁免，但豁免必须在交付报告里说明。

阈值可按项目调整：前端组件类可放宽到 400 / 600；强类型后端逻辑可收紧到 200 / 400。

---

## 包内容

| 路径 | 作用 |
|---|---|
| `SKILL.md` | **双语** —— 每节先英文、后中文。agent 自动加载的就是这个文件，包含全部三条工作流：规划新模块（A）、拆分正在膨胀的文件（B）、重构存量巨型文件（C） |
| `references/refactoring-workflow.md` · `.en.md` | 五阶段安全重构流程，含每阶段出口条件与失败处理表 |
| `references/module-split-patterns.md` · `.en.md` | 分层模型、6 种提取手法、Python / JS-TS / Java / Go / C# 惯例、6 类反模式、接口兼容策略，以及「不该拆」的信号 |
| `scripts/check_file_sizes.py` | 行数扫描脚本，仅用标准库 |
| `tests/` | 扫描脚本与包元信息的自测。`python -m unittest discover -s tests -v` |
| `prompts/giant-file-split-prompt.zh-CN.md` · `.en.md` | 独立提示词版本，覆盖同样内容，适用于不支持 skill 的普通对话模型 |
| `docs/demo.gif` | 上面那段终端演示 |

重构流程里重点处理了 AI 最容易翻车的地方：

- **阶段 0 先冻结行为** —— 没有安全网就不拆。
- **隐藏耦合清单**覆盖了符号搜索找不到的动态引用：`getattr`、`importlib`、依赖注入容器、组件扫描、路由字符串、配置里的类路径、装饰器注册表、`embed` 指令。
- **明确的反作弊规则** —— agent 不得通过删除/跳过测试、注释掉报错代码、放宽类型检查来让验证变绿。
- **每个阶段都有出口条件**，「完成」才有意义。

---

## 注意事项与局限

- **`SKILL.md` 是双语的**，每节先英文后中文。这样只有一份真相源：任何语言的宿主加载它都能拿到完整指令，也不存在第二个文件会漂移。`references/` 仍保留 `.md` 与 `.en.md` 两份，因为它们是按需读取、一次只读一种语言。如果你想要纯英文版，本地删掉 `**中文**` 段落即可——约束双语结构的测试在 `tests/test_skill_package.py`。
- **验证通过不等于行为等价。** 拆分可能保住了行为，却弄坏了测试没覆盖的地方。流程要求 agent 明确说明哪些部分没有测试覆盖。
- **这个技能是约束 agent，不是控制 agent。** 宿主可以忽略 `SKILL.md`；`allowed-tools` 在各 agent 的支持程度差异很大——所以本包刻意不声明这个字段。

---

## 常见问题

**怎么让 AI 不要写出一个巨型文件？**
装上这个 skill，任务开始时提一句。凡涉及 3 个以上文件或约 200 行以上的任务，它会强制 agent 先出模块规划方案、等你确认再写码；同时设死预算：软 300 行、硬 500 行。

**一个 2000 行的文件，怎么拆才不出事？**
让 agent 拆它。工作流 C 走五阶段流程：先跑一遍基线测试冻结行为 → 只读盘点 → 出方案 → 一次迁移一个职责、每步验证 → 输出交付报告。**你确认方案之前，它不能创建／修改／删除任何文件。**

**项目里没有测试，还能安全拆吗？**
可以，但有一个 skill 明确要求的前提：阶段 0 必须先为关键路径补特征测试——只锁定代码**现在**的行为，绝不写「应该是什么」。如果确实做不到，它会如实告诉你，而不是硬拆。

**怎么查出项目里哪些文件太长了？**
```bash
python3 scripts/check_file_sizes.py ./src
```
会列出所有超阈值文件，单独标出入口文件偏长的情况，并自动跳过依赖目录、构建产物、生成文件和 lock 文件。退出码 `1` 表示有文件超过硬阈值，`2` 表示路径写错了——**看到 2 不要当成通过**。

**支持 Claude Code / Codex CLI / Cursor / Copilot 吗？**
支持。本包遵循开放的 [Agent Skills](https://agentskills.io) 规范，任何能读 `SKILL.md` 的 agent 都能用。各工具读取的目录见[安装](#安装)一节。

**需要装依赖吗？**
不需要。扫描脚本只用 Python 标准库，不用 `pip install`、不用虚拟环境、不联网。

**SKILL.md 是英文还是中文的？**
都是。每节先英文后中文，任何语言的 agent 都能拿到完整指令，也不存在第二个文件会漂移失同步。

**它会删掉或重写我的代码吗？**
不会。拆分只做位置移动与 import 调整。skill 明确禁止在拆分过程中改业务逻辑、修 bug 或「顺手优化」——发现问题只会记录到清单里，由你决定怎么处理。

---

## 参与贡献

规则、各语言惯例、扫描脚本参数——都欢迎提。什么合适、什么不合适，以及「agent 行为异常」的报告模板，见 [CONTRIBUTING.md](CONTRIBUTING.md)。中英文 issue 都可以。

如果这东西帮你省了一次重构，点个 star 能让下一个人也找到它。

---

## 许可

MIT。见 [LICENSE](LICENSE)。
