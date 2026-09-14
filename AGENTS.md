# AGENTS.md

Instructions for AI coding agents working **in** this repository.
For the skill's own instructions (used by agents that install this package), see [`SKILL.md`](SKILL.md).

## What this project is

`modular-code-planner` is an [Agent Skills](https://agentskills.io) package that prevents oversized code files. It ships three workflows (plan modules before coding, split a file that is growing, restructure an existing monolith), a set of hard rules an agent must follow, and a dependency-free line-count scanner.

`SKILL.md` is the file an agent loads when this package is installed. Everything else supports it.

## Setup

There is nothing to install.

```bash
git clone https://github.com/Magicapple-Coder/modular-code-planner.git
cd modular-code-planner
python -m unittest discover -s tests -v
```

Python 3.9+. Standard library only. No `requirements.txt`, no virtualenv, no build step, no network access at runtime.

## Commands

| Purpose | Command |
|---|---|
| Run the tests | `python -m unittest discover -s tests -v` |
| Scan this repo with its own scanner | `python scripts/check_file_sizes.py . --lang en` |
| Run the scanner against another project | `python scripts/check_file_sizes.py <path> [flags]` |

The self-scan must exit `0`. This repository holds itself to the rule it ships.

## Rules for changes in this repository

1. **`SKILL.md` is bilingual and must stay that way.** Every `## ` section needs an `**English**` block followed by a `**中文**` block. `test_every_section_carries_both_languages` enforces the presence of both, but not that they still say the same thing — keep them semantically in sync yourself.
2. **Do not create a second `SKILL.*` file.** A `SKILL.en.md` used to exist and duplicated the English text; `test_no_second_english_entry_point` now fails if one reappears. `SKILL.md` is the single source of truth.
3. **No runtime dependencies.** If a change needs a third-party package, it needs a much stronger argument than convenience.
4. **Keep the frontmatter to the [Agent Skills specification](https://agentskills.io).** Only `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. A host-specific field breaks portability and fails CI.
5. **Add a test with every scanner flag**, including its failure case. The scanner must never report a clean result for a path that does not exist — that is a deliberate design decision, not an accident.
6. **`references/` and `prompts/` ship in both `.md` and `.en.md`.** Update both.

## Where things live

| Path | Contents |
|---|---|
| `SKILL.md` | The skill itself — bilingual, three workflows, hard rules, exit conditions |
| `references/refactoring-workflow.md` · `.en.md` | The 5-phase safe-refactoring procedure |
| `references/module-split-patterns.md` · `.en.md` | Layering model, extraction techniques, per-language conventions, anti-patterns |
| `scripts/check_file_sizes.py` | The scanner. Exit codes: `0` clean, `1` over the hard threshold, `2` bad usage or path missing |
| `tests/` | 31 tests over the scanner and the package metadata |
| `prompts/` | Standalone prompt versions for chat models without skill support |
| `docs/demo.gif` | Terminal recording used in the README |

## Conventions

- Comments and `SKILL.md` prose: imperative mood, no hedging. A rule an agent can argue with is a rule it will skip.
- Every workflow phase states its exit condition.
- The scanner's output language follows the system locale; `--lang en|zh` overrides it. Non-ASCII output degrades to `?` rather than crashing.
