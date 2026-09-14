# Modular Code Planner

> **Language**: this is the English edition. 中文版: [SKILL.md](SKILL.md)
> **Portability**: this package follows the open Agent Skills spec (SKILL.md). It assumes no particular agent, install path, or host tool names.
> **Note**: agents load `SKILL.md` (Chinese) automatically. This file is the English equivalent, for readers and for hosts configured to load it.

Goal: never let one file reach a thousand lines. Plan modules before writing code; split a file as it approaches the threshold; when restructuring an existing large file, keep behavior identical and verify at every step.

## Hard rules

1. **Plan first, code second.** For any coding task touching 3+ files or estimated at 200+ lines, produce a module plan and get it approved before implementing file by file. Small edits and single-file scripts are exempt.
2. **File-length thresholds** (the test is *above*, matching the scanner's `--soft/--hard` semantics):
   - ≤300 lines: healthy, the target state.
   - 301–500 lines: warning zone. Stop adding responsibilities; split now within the current task, or produce a split plan.
   - \>500 lines: red line. The task is not complete until it is split. If that is genuinely impractical, state the reason and the follow-up plan — never deliver it silently.
   - Entry files (main / index / app / `__main__`): target ≤100 lines, wiring only, no business logic.
   - Generated code, lock files and type declarations (`*.d.ts`, `*.pb.go`, `*_pb2.py`, …) are exempt, but the exemption must be stated in the report.
3. **Single responsibility.** One file, one kind of change. The filename must summarize everything inside it. No `utils` / `helpers` / `misc` / `common` files that grow without limit.
4. **Behavior invariance (refactoring).** Splitting moves code and fixes imports. It does not change business logic. Splitting and feature changes are never mixed into one execution.
5. **One-way dependencies.** Upper layers depend on lower layers; no cycles. When two modules genuinely need each other, extract the shared types or interfaces into a third module.
6. **Never fake a passing verification.** Violating this means the task failed:
   - Do not make verification pass by commenting out failing code, deleting or skipping tests, adding `skip`/`xfail`/`@Ignore`, or loosening type checking (`any`, `cast`, `# type: ignore`, `eslint-disable`, lowering `strict`).
   - Do not fix bugs or "optimize" along the way. Record findings in a problem list and report them.
   - When verification fails, fix it in place or roll back the step. Never continue past a failure.

## Workflow A: new project / new feature (preventive; the default path)

1. **Read the stack conventions first.** Before planning, read the relevant section of [references/module-split-patterns.en.md](references/module-split-patterns.en.md) (layering conventions, directory layout, extraction techniques, common anti-patterns).
2. **Establish the boundaries.** Confirm scope, language/framework, entry shape (CLI / web service / front-end page / library), and the run and verification commands.
3. **Output the module plan and pause for approval.** It must include:
   - the directory tree, down to file level;
   - a one-line responsibility and estimated line count per file;
   - dependency direction (who imports whom) and how cycles are avoided;
   - which files belong to the entry, business, data and shared layers;
   - an implementation order (bottom-up);
   - the verification command for each stage.
4. After approval, implement file by file. Stop each file at its planned responsibility boundary; a new requirement that belongs elsewhere gets a new file, not a bigger one.
5. **Run the line-count scan before delivery** (see the Tools section). Everything must be under threshold. Any file over it needs a stated plan.

## Workflow B: a file approaching the threshold while coding

1. Stop appending when the current file passes 300 lines, or when you see a split signal: section-header comments, several groups of functions that never call each other, mixed unrelated content, or a filename that no longer describes the contents.
2. Identify the responsibility blocks inside the file, pick one cohesive block, create a single-responsibility file, move the code and fix the imports.
3. Immediately run tests / type check / build. On success, continue the original task; on failure, fix or roll back this step.
4. If the split touches a cross-file public interface, dynamic references, or hidden coupling, escalate to workflow C instead of forcing it.

## Workflow C: restructuring a file that is already over the limit

When the user asks to split a long file, or a legacy project full of them, follow
[references/refactoring-workflow.en.md](references/refactoring-workflow.en.md) exactly. **Read that file in full before touching anything.** The shape:

- Phase 0 freezes behavior: confirm the code is committed or backed up; if there are no tests, add characterization tests for the critical paths first.
- Phase 1 is a read-only inventory: responsibilities, symbols, dependencies, external contract, hidden coupling including dynamic and string references.
- Phase 2 produces the split plan (directory tree, symbol migration map, compatibility strategy, step order, per-step verification command, line-count estimate). **No file may be created, modified or deleted before the user approves it.**
- Phase 3 migrates bottom-up, one responsibility at a time, verifying and reporting each step, including the list of changed files.
- Phase 4 is full verification, a line-count scan, and a delivery report including a "behavior is equivalent before and after" statement and a list of open issues.

Interface compatibility strategies, re-export transition layers, and per-language refactoring techniques are in
[references/module-split-patterns.en.md](references/module-split-patterns.en.md).

## Tools: file line-count scan

Script: [`scripts/check_file_sizes.py`](scripts/check_file_sizes.py), in the same directory as this SKILL.md.

Before running it, resolve `scripts/check_file_sizes.py` against wherever SKILL.md actually lives on this machine, then run:

```bash
# macOS / Linux
python3 "/absolute/path/to/modular-code-planner/scripts/check_file_sizes.py" <project-path>

# Windows
python "X:\path\to\modular-code-planner\scripts\check_file_sizes.py" <project-path>

# Optional: --soft 300 --hard 500 --entry-max 100 --top 10
#           --ext .py,.ts --ignore dir1,dir2 --exclude-glob "*.generated.*"
#           --json --lang en|zh|auto  (default auto, follows the system locale)
```

- The test is *above*: `>soft` warns, `>hard` fails. Entry files over `--entry-max` are listed separately.
- Exit codes: `0` clean, `1` at least one file over the hard threshold, `2` bad usage or path missing. **Never read exit code 2 as a pass.**
- Dependencies, build output, generated files and lock files are excluded by default. Run it before delivery and before and after any refactor, and compare.
- Quote the path when it contains spaces.
- This skill assumes no fixed install location; it can live in any agent's skills directory or inside a project.
