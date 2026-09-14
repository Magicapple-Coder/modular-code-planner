# Contributing

Thanks for taking the time. This is a small, dependency-free package, so contributing is mostly about keeping it that way.

Issues and pull requests in **English or Chinese** are both welcome.

## What is most useful

| Type | Examples |
|---|---|
| **Better thresholds or detection** | A project layout where the defaults produce noise, or a generated-file pattern the scanner misses |
| **New stack conventions** | `references/module-split-patterns.md` has no section for Rust, PHP, Ruby, Kotlin Multiplatform, … |
| **Real-world reports** | "The agent still did X under workflow C" — this is the highest-value feedback, because it tells us where the constraints are too weak |
| **Translation fixes** | The English editions are hand-written; if a term reads wrong, say so |

## What we will decline

- Runtime dependencies. The scanner uses the standard library only, on purpose. If a feature needs a library, it needs a stronger argument than convenience.
- A "just run the formatter / auto-fix everything" mode. The whole point of workflow C is that the agent stops and asks before changing code.
- Rewriting the Chinese `SKILL.md` into English in place. It is the file agents load, and changing its language costs every existing user. Add or extend the `.en.md` editions instead.

## Setting up

Nothing to install.

```bash
git clone https://github.com/Magicapple-Coder/modular-code-planner.git
cd modular-code-planner
python -m unittest discover -s tests -v
```

Requires Python 3.9+. There is no virtualenv, no `requirements.txt`, and no build step.

## Before you open a pull request

1. **Run the tests.** `python -m unittest discover -s tests -v` must be green.
2. **Scan this repository with its own scanner.** `python scripts/check_file_sizes.py . --lang en` must exit `0`. This repo holds itself to the rule it ships.
3. **Keep the two language editions in sync.** If you change `SKILL.md`, change `SKILL.en.md`. Same for anything in `references/` or `prompts/`. CI does not catch semantic drift — only you can.
4. **If you add a frontmatter field, add it to `tests/test_skill_package.py` too.** The package only uses fields from the [Agent Skills specification](https://agentskills.io); a host-specific field breaks portability and will fail CI.
5. **If you add a script flag, add a test for it.** Including the failure case — `--soft` greater than `--hard`, a missing path, an empty directory.

## Changing the SKILL.md rules

The instructions in `SKILL.md` are the actual product. Two things worth knowing before you edit them:

- **They are constraints on an agent, not advice.** Keep the imperative voice and the explicit "never" list. Softening a rule ("try to avoid…") measurably weakens compliance.
- **Every phase needs an exit condition.** If you add a phase or a step, say what must be true before the agent may move on. Rules without an exit condition get skipped.

## Reporting a problem with an agent's behavior

The most useful bug report looks like this:

```
Skill: modular-code-planner v1.1.0
Agent: <name and version>
Task: <what you asked for>
Expected: the agent stopped at phase 2 and waited for approval
Actual: it started creating files
Prompt / repo shape: <what you gave it>
```

With that, the fix is usually a sharper sentence in `SKILL.md`. Without it, there is nothing to act on.

## Licence

By contributing you agree that your contribution is licensed under the MIT licence that covers this project.
