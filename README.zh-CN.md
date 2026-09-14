# modular-code-planner

**English → [README.md](README.md)**

一个遵循 [Agent Skills](https://agentskills.io) 开放规范的技能包，用来阻止你的代码库退化成一坨巨型文件。

它做三件事：

1. **先规划再写码** —— 涉及 3 个以上文件、或预估 200 行以上的任务，先出模块规划方案，你确认后才动手。
2. **守住文件体积预算** —— 300 / 500 行软硬阈值，自带扫描脚本，可对任意项目体检。
3. **安全拆分臃肿文件** —— 一套五阶段重构流程，只搬位置不改行为。

只要 agent 能读 `SKILL.md` 就能用。除扫描脚本需要 Python 3.8+ 外，没有任何依赖。

---

## 要解决的问题

AI 写代码很快，但很少主动停下来拆分。一个工具文件从 80 行长到 1400 行，等到合并冲突频繁出现时已经太晚了。

这个技能把「文件体积」变成一条硬约束：开工前规划模块，编码中盯住行数，拆分存量巨型文件时保证行为不变。

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
    ├── SKILL.md
    ├── references/
    │   ├── module-split-patterns.md
    │   └── refactoring-workflow.md
    └── scripts/
        └── check_file_sizes.py
```

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
| `SKILL.md` | 三条工作流：规划新模块（A）、拆分正在膨胀的文件（B）、重构存量巨型文件（C） |
| `references/refactoring-workflow.md` | 五阶段安全重构流程，含每阶段出口条件与失败处理表 |
| `references/module-split-patterns.md` | 分层模型、6 种提取手法、Python / JS-TS / Java / Go / C# 惯例、6 类反模式、接口兼容策略，以及「不该拆」的信号 |
| `scripts/check_file_sizes.py` | 行数扫描脚本，仅用标准库 |
| `prompts/giant-file-split-prompt.zh-CN.md` | 独立提示词版本，覆盖同样内容，适用于不支持 skill 的普通对话模型 |

`references/refactoring-workflow.md` 里重点处理了 AI 重构最容易翻车的地方：

- **阶段 0 先冻结行为** —— 没有安全网就不拆。
- **隐藏耦合清单**覆盖了符号搜索找不到的动态引用：`getattr`、`importlib`、依赖注入容器、组件扫描、路由字符串、配置里的类路径、装饰器注册表、`embed` 指令。
- **明确的反作弊规则** —— agent 不得通过删除/跳过测试、注释掉报错代码、放宽类型检查来让验证变绿。
- **每个阶段都有出口条件**，「完成」才有意义。

---

## 注意事项与局限

- **`SKILL.md` 正文是中文的。** frontmatter 里的 `description` 是中英双语，所以中英文都能触发，但详细流程文字是中文。目前未提供英文版 `SKILL.md`。
- **验证通过不等于行为等价。** 拆分可能保住了行为，却弄坏了测试没覆盖的地方。流程要求 agent 明确说明哪些部分没有测试覆盖。
- **这个技能是约束 agent，不是控制 agent。** 宿主可以忽略 `SKILL.md`；`allowed-tools` 在各 agent 的支持程度差异很大——所以本包刻意不声明这个字段。

---

## 许可

MIT。见 [LICENSE](LICENSE)。
