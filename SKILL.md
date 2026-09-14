---
name: modular-code-planner
description: "Plan code modules before writing code and keep single files small. Use when starting a new project or feature module, designing directory structure or architecture layering, generating multiple code files at once, or when one file has grown too long (hundreds to thousands of lines), mixes too many responsibilities, or needs a safe split or refactor. Covers Python, JavaScript/TypeScript, Java, Go, C#, Rust and more: prevent oversized files, enforce line-count thresholds, and restructure crowded files without changing behavior. 代码模块化规划与单文件体积治理：从零创建项目或功能模块、设计目录结构、规划架构分层、生成多个代码文件，或发现单个代码文件过长（数百上千行）、职责过多、需要安全拆分重构时使用。"
license: MIT
compatibility: "Bundled scripts/check_file_sizes.py requires Python 3.9+ (standard library only). No third-party dependencies, no network access."
metadata:
  version: "1.2.0"
  author: "Magicapple-Coder"
  spec: "Agent Skills (agentskills.io)"
  languages: "en, zh"
---

# Modular Code Planner · 模块化代码规划

> **Language / 语言** — This file is bilingual. Every section gives English first, then Chinese. 本文件为双语：每节先英文，后中文。
> **Portability / 可移植性** — Follows the open Agent Skills specification (SKILL.md), assuming no particular agent, install path, or host tool names. 遵循开放的 Agent Skills 规范，不假设任何特定 agent、安装路径或宿主工具名。
> Overview / 概览: [README.md](README.md) · [README.zh-CN.md](README.zh-CN.md)

**English** — Goal: never let one file reach a thousand lines. Plan modules before writing code; split a file as it approaches the threshold; when restructuring an existing large file, keep behavior equivalent and verify at every step.

**中文** — 目标：杜绝「一个文件堆上千行」。写新代码前先规划模块；文件接近阈值时主动拆；重构已有大文件时行为不变、分步可验证。

## Hard rules · 硬性规则

**English**

1. **Plan first, code second.** For any coding task touching 3+ files or estimated at 200+ lines, produce a module plan and get it approved before implementing file by file. Small edits and single-file scripts are exempt.
2. **File-length thresholds.** The test is *above* the number, matching the scanner's `--soft` / `--hard` semantics:
   - ≤300 lines: healthy, the target state.
   - 301–500 lines: warning zone. Stop adding responsibilities; split now within the current task, or produce a split plan.
   - \>500 lines: red line. The task is not complete until it is split. If that is genuinely impractical, state the reason and the follow-up plan — never deliver it silently.
   - Entry files (main / index / app / `__main__`): target ≤100 lines, wiring only, no business logic.
   - Generated code, lock files and type declarations (`*.d.ts`, `*.pb.go`, `*_pb2.py`) are exempt, but the exemption must be stated in the report.
3. **Single responsibility.** One file, one kind of change. The filename must summarize everything inside it. No `utils` / `helpers` / `misc` / `common` files that grow without limit.
4. **Behavior invariance (refactoring).** Splitting moves code and fixes imports. It does not change business logic. Splitting and feature changes are never mixed into one execution.
5. **One-way dependencies.** Upper layers depend on lower layers; no cycles. When two modules genuinely need each other, extract the shared types or interfaces into a third module.
6. **Never fake a passing verification.** Violating this means the task failed:
   - Do not make verification pass by commenting out failing code, deleting or skipping tests, adding `skip` / `xfail` / `@Ignore`, or loosening type checking (`any`, `cast`, `# type: ignore`, `eslint-disable`, lowering `strict`).
   - Do not fix bugs or "optimize" along the way. Record findings in a problem list and report them.
   - When verification fails, fix it in place or roll back the step. Never continue past a failure.

**中文**

1. **先规划，后写码**：任何涉及 ≥3 个文件或预估总量 ≥200 行的编码任务，先输出模块规划方案，经用户确认后再逐文件实现。小改动、单文件脚本除外。
2. **文件行数阈值**，判据是「超过」该数字，与扫描脚本的 `--soft` / `--hard` 语义一致：
   - ≤300 行：健康区，目标状态。
   - 301–500 行：警告区。停止追加新职责，在当前任务内顺手拆分，或给出拆分计划。
   - >500 行：红线。必须拆分后才算完成；确有困难时明确说明原因和后续计划，不得静默交付。
   - 入口文件（main / index / app / `__main__`）：目标 ≤100 行，只做装配，不放业务逻辑。
   - 生成代码、lock 文件、类型声明（`*.d.ts`、`*.pb.go`、`*_pb2.py`）豁免，但必须在报告中说明。
3. **单一职责**：一个文件一类变化；文件名能概括其全部内容，禁止 utils / helpers / misc / common 大杂烩式无限膨胀。
4. **行为不变原则（重构场景）**：拆分只做位置移动与 import 调整，不改业务逻辑；拆分与功能变更严格分离，不合并到同一次执行中。
5. **依赖单向**：上层依赖下层，禁止循环依赖；两模块互相需要时抽出共同依赖的第三方模块。
6. **不得作弊通过验证**，违反即视为任务失败：
   - 禁止通过注释掉报错代码、删除/跳过测试、加 `skip` / `xfail` / `@Ignore`、放宽类型检查（`any`、`cast`、`# type: ignore`、`eslint-disable`、降低 `strict` 级别）来让验证通过。
   - 禁止顺便「修 bug」或「优化」；发现问题只记录到问题清单并汇报。
   - 验证失败时就地修复或回滚上一步，不得带着失败继续。

## Workflow A · 工作流 A：新项目 / 新功能（预防，默认走这条）

**English**

1. **Read the stack conventions first.** Before planning, read the relevant section of [references/module-split-patterns.en.md](references/module-split-patterns.en.md) — layering conventions, directory layout, extraction techniques, common anti-patterns.
2. **Establish the boundaries.** Confirm scope, stack, entry shape (CLI / web service / front-end page / library), and the run and verification commands.
3. **Output the module plan and pause for approval.** It must include the directory tree to file level; a one-line responsibility and estimated line count per file; dependency direction and how cycles are avoided; which files belong to the entry, business, data and shared layers; the implementation order (bottom-up); and the verification command for each stage.
4. After approval, implement file by file. Stop each file at its planned responsibility boundary; a new requirement that belongs elsewhere gets a new file, not a bigger one.
5. **Run the line-count scan before delivery** (see Tools below). Everything must be under threshold; any file over it needs a stated plan.

**中文**

1. **先读技术栈惯例**：规划前先读取 [references/module-split-patterns.md](references/module-split-patterns.md) 中对应技术栈的小节——分层惯例、目录结构、提取手法、常见反模式。
2. **明确边界**：确认功能范围、技术栈、入口形态（CLI / Web 服务 / 前端页面 / 库）、运行与验证命令。
3. **输出模块规划并暂停等确认**，内容包括：目录树（到文件级）；每个文件一句话职责 + 预估行数；模块依赖方向（谁 import 谁）及如何避免循环依赖；哪些是入口层、业务层、数据层、公共层；实现顺序（自底向上）；每阶段的验证命令。
4. 用户确认后按规划逐文件实现；每个文件写到预估职责边界即止，新需求属于别的职责就开新文件，不就地膨胀。
5. **交付前运行行数扫描**（见下方「工具」节），全部低于阈值才算完成；有超阈值文件必须说明处理方案。

## Workflow B · 工作流 B：编码过程中文件逼近阈值

**English**

1. Stop appending when the current file passes 300 lines, or when you see a split signal: section-header comments, several groups of functions that never call each other, mixed unrelated content, or a filename that no longer describes the contents.
2. Identify the responsibility blocks inside the file, pick one cohesive block, create a single-responsibility file, move the code and fix the imports.
3. Immediately run tests / type check / build. On success, continue the original task; on failure, fix or roll back this step.
4. If the split touches a cross-file public interface, dynamic references, or hidden coupling, escalate to workflow C instead of forcing it.

**中文**

1. 当前文件超过 300 行，或出现「该拆的信号」——注释分区标题、多组互不调用的函数、多类内容混杂、文件名已无法概括内容——时，停止追加。
2. 识别文件内的职责块，选定要提取的内聚块，新建职责单一的文件，移动代码并修正 import。
3. 立即运行测试 / 类型检查 / 构建验证，通过后继续原任务；失败则修复或回退本步。
4. 若拆分牵涉跨文件公开接口、动态 / 字符串引用或隐藏耦合，升级为工作流 C，不要就地硬拆。

## Workflow C · 工作流 C：已爆满文件的拆分重构

**English**

When the user asks to split a long file, or a legacy project full of them, follow [references/refactoring-workflow.en.md](references/refactoring-workflow.en.md) exactly. **Read that file in full before touching anything.** The shape:

- Phase 0 freezes behavior: confirm the code is committed or backed up; with no tests, add characterization tests for the critical paths first.
- Phase 1 is a read-only inventory: responsibilities, symbols, dependencies, external contract, hidden coupling including dynamic and string references.
- Phase 2 produces the split plan — directory tree, symbol migration map, compatibility strategy, step order, per-step verification command, line-count estimate. **No file may be created, modified or deleted before the user approves it.**
- Phase 3 migrates bottom-up, one responsibility at a time, verifying and reporting each step, including the list of changed files.
- Phase 4 is full verification, a line-count scan, and a delivery report including a "behavior is equivalent before and after" statement and a list of open issues.

Interface compatibility strategies, re-export transition layers and per-language refactoring techniques are in [references/module-split-patterns.en.md](references/module-split-patterns.en.md).

**中文**

当用户要求拆分一个已经很长的文件（或历史遗留的巨型项目）时，严格按 [references/refactoring-workflow.md](references/refactoring-workflow.md) 执行，**开始动手前完整读取该文件**。要点：

- 阶段 0 冻结行为：先确认版本已提交 / 可回滚；无测试则先补关键路径的特征测试。
- 阶段 1 只读盘点：职责、符号、依赖、对外契约、隐藏耦合（含动态 / 字符串引用）。
- 阶段 2 出拆分方案——目录树、符号迁移映射表、兼容策略、分步顺序、每步验证命令、行数预估。**用户确认前禁止创建 / 修改 / 删除任何代码文件。**
- 阶段 3 自底向上、一次迁移一个职责、每步验证并报告改动文件清单。
- 阶段 4 全量验证 + 行数扫描 + 交付说明（含「拆分前后对外行为等价」声明与遗留问题清单）。

跨文件公开接口兼容策略、re-export 过渡层写法、各语言重构手法见 [references/module-split-patterns.md](references/module-split-patterns.md)。

## Tools · 工具：文件行数扫描

**English** — Script: [`scripts/check_file_sizes.py`](scripts/check_file_sizes.py), in the same directory as this SKILL.md. Resolve it against wherever SKILL.md actually lives on this machine, then run:

**中文** — 脚本：[`scripts/check_file_sizes.py`](scripts/check_file_sizes.py)，与本 SKILL.md 位于同一目录。先按本 SKILL.md 在本机的实际位置把它解析成绝对路径，再运行：

```bash
# macOS / Linux
python3 "/abs/path/to/modular-code-planner/scripts/check_file_sizes.py" <project-path>

# Windows
python "X:\path\to\modular-code-planner\scripts\check_file_sizes.py" <project-path>

# flags / 参数: --soft 300 --hard 500 --entry-max 100 --top 10
#               --ext .py,.ts --ignore dir1,dir2 --exclude-glob "*.generated.*"
#               --json --lang en|zh|auto   (auto follows the system locale / 跟随系统区域设置)
```

**English**

- The test is *above* the number: `>soft` warns, `>hard` fails. Entry files over `--entry-max` are listed separately.
- Exit codes: `0` clean, `1` at least one file over the hard threshold, `2` bad usage or path missing. **Never read exit code 2 as a pass.**
- Dependencies, build output, generated files, declarations and lock files are excluded by default. Run it before delivery and before and after any refactor, then compare.
- Quote the path when it contains spaces.
- This skill assumes no fixed install location; it can live in any agent's skills directory or inside a project.

**中文**

- 判据为「超过」该数字：`>软阈值` 报警告，`>硬阈值` 报红线；入口文件超过 `--entry-max` 单独列出。
- 退出码：`0` 正常，`1` 存在超硬阈值文件，`2` 用法错误或路径不存在。**看到 2 不要当成通过。**
- 默认已排除依赖目录、构建产物、生成文件、类型声明与 lock 文件。项目交付前、重构前后各跑一次并对比。
- 路径含空格时必须加引号。
- 本 skill 不假定固定安装位置，可放在任意 agent 的 skills 目录或项目内。
