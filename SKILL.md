---
name: modular-code-planner
description: "Plan code modules before writing code and keep single files small. Use when starting a new project or feature module, designing directory structure or architecture layering, generating multiple code files at once, or when one file has grown too long (hundreds to thousands of lines), mixes too many responsibilities, or needs a safe split or refactor. Covers Python, JavaScript/TypeScript, Java, Go, C#, Rust and more: prevent oversized files, enforce line-count thresholds, and restructure crowded files without changing behavior. 代码模块化规划与单文件体积治理：从零创建项目或功能模块、设计目录结构、规划架构分层、生成多个代码文件，或发现单个代码文件过长（数百上千行）、职责过多、需要安全拆分重构时使用。"
license: MIT
compatibility: "Bundled scripts/check_file_sizes.py requires Python 3.8+ (standard library only). No third-party dependencies, no network access."
metadata:
  version: "1.1.0"
  author: "Magicapple-Coder"
  spec: "Agent Skills (agentskills.io)"
---

# Modular Code Planner

> **语言 / Language**：本文件为中文版。English edition: [SKILL.en.md](SKILL.en.md)（英文版参考文档见 [`references/*.en.md`](references/)）
> **Portability**：本包遵循开放的 Agent Skills 规范（SKILL.md），不假设任何特定 agent、安装路径或宿主工具名。
> 说明文档：[README.md](README.md)（英） · [README.zh-CN.md](README.zh-CN.md)（中）

目标：杜绝「一个文件堆上千行」。写新代码前先规划模块；文件接近阈值时主动拆；重构已有大文件时行为不变、分步可验证。

## 硬性规则

1. **先规划，后写码**：任何涉及 ≥3 个文件或预估总量 ≥200 行的编码任务，先输出模块规划方案，经用户确认后再逐文件实现。小改动、单文件脚本除外。
2. **文件行数阈值**（判据是「超过」，与扫描脚本 `--soft/--hard` 语义一致）：
   - ≤300 行：健康区，目标状态。
   - 301–500 行：警告区，停止追加新职责，在当前任务内顺手拆分或给出拆分计划。
   - >500 行：红线，必须拆分后才算完成；确有困难时明确说明原因和后续计划，不得静默交付。
   - 入口文件（main / index / app / `__main__`）目标 ≤100 行，只做装配，不放业务逻辑。
   - 生成代码、lock 文件、类型声明（`*.d.ts`、`*.pb.go`、`*_pb2.py` 等）豁免，需在报告中说明。
3. **单一职责**：一个文件一类变化；文件名能概括其全部内容，禁止 utils / helpers / misc / common 大杂烩式无限膨胀。
4. **行为不变原则（重构场景）**：拆分只做位置移动与 import 调整，不改业务逻辑；拆分与功能变更严格分离，不合并到同一次执行中。
5. **依赖单向**：上层依赖下层，禁止循环依赖；两模块互相需要时抽出共同依赖的第三方模块。
6. **不得作弊通过验证**（违反即视为任务失败）：
   - 禁止通过注释掉报错代码、删除/跳过测试、加 `skip`/`xfail`/`@Ignore`、放宽类型检查（`any`、`cast`、`# type: ignore`、`eslint-disable`、降低 `strict` 级别）来让验证通过。
   - 禁止顺便「修 bug」或「优化」；发现问题只记录到问题清单并汇报。
   - 验证失败时就地修复或回滚上一步，不得带着失败继续。

## 工作流 A：新项目 / 新功能（预防，默认走这条）

1. **先读技术栈惯例**：规划前先读取 [references/module-split-patterns.md](references/module-split-patterns.md) 中对应技术栈的小节（分层惯例、目录结构、提取手法、常见反模式）。
2. **明确边界**：确认功能范围、技术栈、入口形态（CLI / Web 服务 / 前端页面 / 库）、运行与验证命令。
3. **输出模块规划并暂停等确认**，内容包括：
   - 目录树（到文件级）；
   - 每个文件一句话职责 + 预估行数；
   - 模块依赖方向（谁 import 谁），并说明如何避免循环依赖；
   - 哪些是入口层、业务层、数据层、公共层；
   - 实现顺序（自底向上）；
   - 每阶段的验证命令。
4. 用户确认后按规划逐文件实现；每个文件写到预估职责边界即止，新需求属于别的职责就开新文件，不就地膨胀。
5. **交付前运行行数扫描**（见下方「工具」节），全部低于阈值才算完成；有超阈值文件必须说明处理方案。

## 工作流 B：编码过程中文件逼近阈值

1. 当前文件超过 300 行或出现「该拆的信号」（注释分区标题、多组互不调用的函数、多类内容混杂、文件名已无法概括内容）时，停止追加。
2. 识别文件内的职责块，选定要提取的内聚块，新建职责单一的文件，移动代码并修正 import。
3. 立即运行测试 / 类型检查 / 构建验证，通过后继续原任务；失败则修复或回退本步。
4. 若拆分牵涉跨文件公开接口、动态/字符串引用或隐藏耦合，升级为工作流 C，不要就地硬拆。

## 工作流 C：已爆满文件的拆分重构

当用户要求拆分一个已经很长的文件（或历史遗留的巨型项目）时，严格按
[references/refactoring-workflow.md](references/refactoring-workflow.md) 执行，**开始动手前完整读取该文件**。要点：

- 阶段 0 冻结行为：先确认版本已提交/可回滚；无测试则先补关键路径的特征测试；
- 阶段 1 只读盘点：职责、符号、依赖、对外契约、隐藏耦合（含动态/字符串引用）；
- 阶段 2 出拆分方案（目录树、符号迁移映射表、兼容策略、分步顺序、每步验证命令、行数预估），**用户确认前禁止创建/修改/删除任何代码文件**；
- 阶段 3 自底向上、一次迁移一个职责、每步验证并报告改动文件清单；
- 阶段 4 全量验证 + 行数扫描 + 交付说明（含「拆分前后对外行为等价」声明与遗留问题清单）。

跨文件公开接口兼容策略、re-export 过渡层写法、各语言重构手法见
[references/module-split-patterns.md](references/module-split-patterns.md)。

## 工具：文件行数扫描

脚本：[`scripts/check_file_sizes.py`](scripts/check_file_sizes.py)，与本 SKILL.md 位于同一目录。

执行前，先按本 SKILL.md 在本机的实际位置，把 `scripts/check_file_sizes.py` 解析成绝对路径，再运行：

```bash
# macOS / Linux
python3 "/absolute/path/to/modular-code-planner/scripts/check_file_sizes.py" <项目路径>

# Windows
python "X:\path\to\modular-code-planner\scripts\check_file_sizes.py" <项目路径>

# 可选参数：--soft 300 --hard 500 --entry-max 100 --top 10
#          --ext .py,.ts --ignore dir1,dir2 --exclude-glob "*.generated.*"
#          --json --lang en|zh|auto（默认 auto，跟随系统区域设置）
```

- 判据为「超过」：`>软阈值` 报警告，`>硬阈值` 报红线；入口文件超过 `--entry-max` 单独列出。
- 退出码：`0` 正常，`1` 存在超硬阈值文件，`2` 用法错误或路径不存在（**看到 2 不要当成通过**）。
- 输出语言默认跟随系统区域设置；给非中文用户汇报时可显式加 `--lang en`。
- 默认已排除依赖目录、构建产物、生成文件与 lock 文件；项目交付前、重构前后各跑一次并对比。
- 路径含空格时必须加引号。
- 本 skill 不假定固定安装位置，可放在任意 agent 的 skills 目录或项目内。
