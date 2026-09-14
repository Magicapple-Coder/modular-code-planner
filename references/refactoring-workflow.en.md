# Splitting a large file: the five-phase workflow

Used by workflow C of `modular-code-planner`. **Read this file in full before touching anything.**

Iron rule: **behavior must be exactly equivalent.** Splitting moves code and fixes imports, nothing else. Bugs and design problems you find are recorded, not fixed.

---

## Phase 0: freeze behavior (build the safety net)

1. Confirm version state: the code is committed or backed up, and the user can roll back at any time. If it is uncommitted, tell the user to commit first.
2. Confirm the verification commands: tests, type check, lint, build, start. **Run them once and record the baseline**, including any pre-existing failures, so a known failure is not later blamed on the split.
3. If there are no tests at all:
   - state the risk plainly: a split with no safety net cannot be verified;
   - add **minimal characterization tests** for the critical paths the target file covers: pin down current input/output behavior, never assert what it "should" be;
   - the tests must not modify the code under test. If the code cannot be tested as written, report that and let the user decide.

**Exit condition**: the baseline verification commands have run and their results are recorded. Do not enter phase 1 without this.

---

## Phase 1: read-only inventory (no write operations)

Read the target file and its immediate neighbors end to end. Allowed: reading files, global searches, running read-only commands. Forbidden: creating, modifying or deleting files, formatting, batch renaming.

Produce five lists:

1. **Responsibilities.** Which independent responsibilities the file actually carries, and which functions/classes and line ranges each one maps to.
2. **Symbols.** Every top-level function, class, constant and type, and who calls it (in-file / cross-file / public).
3. **Dependencies.** Which responsibility each import serves; module-level global state, singletons, and import-time side effects.
4. **External contract.** Which files in the project reference the target, and which symbols they use. This is the public surface that must keep working.
5. **Hidden coupling**, checked item by item:
   - execution-order dependencies, shared mutable variables, implicit data-format agreements;
   - **string and dynamic references**: `getattr`, `importlib`, reflection, DI containers and component scanning, route strings, template references, serialization paths, class paths in config, `entry_points`;
   - registries and decorator auto-collection (plugins, routes, ORM models, event subscribers);
   - monkey patching and runtime replacement;
   - relative paths, `__file__`-relative lookup, embedded assets such as Go's `embed`.

**Exit condition**: all five lists complete, and every hidden-coupling item either has a conclusion or is explicitly marked "not found, checked by X".

---

## Phase 2: the split plan (output, then pause for approval)

Must contain:

1. **Target directory tree**, down to file level; one-line responsibility and estimated line count per file.
2. **Symbol migration map**: where each function, class and constant goes.
3. **Public interface compatibility strategy**: update all imports / keep a re-export transition layer / compatibility wrapper. State the choice, the reason, and an explicit claim that external callers will not break under it, citing the external contract from phase 1.
4. **Module dependency graph or list**, explaining how cycles are avoided.
5. **A bottom-up migration sequence** where the project runs after every step, naming which file gets created first.
6. **Per-step verification**: exact commands, not "run the tests".
7. **Before/after line-count estimate.**
8. **What will not be split, and why** (if anything).
9. **Risk list**: which steps are most likely to fail, and where the rollback point is.

> **No code file may be created, modified or deleted before the user explicitly approves.** If the user asks for changes, update the plan and get approval again.

---

## Phase 3: incremental migration

1. **Bottom-up.** Build the leaf files that depend on no other new module first (types, pure utilities, constants), then work upward, and change the entry point last.
2. **One responsibility at a time.** Move the code, fix the references, delete the duplicated original, run this step's verification, report, then continue.
   - The report always contains: the list of files changed in this step, lines added and removed, the command that ran and its real output, and whether that matched expectations.
3. **Move, don't rewrite.** Keep function bodies as close to byte-identical as possible. Renames happen in their own step, never mixed with a move.
4. **Create a rollback point after each stage or step group.** One commit, with the step number in the message.
5. **On hidden coupling the plan did not anticipate**: stop immediately, explain the symptom and the impact, update the plan, and get approval again. Do not force it through and do not guess.
6. **Forbidden ways to make verification pass:**
   - commenting out failing code, or swallowing exceptions with `try/except: pass`;
   - deleting, skipping or weakening existing tests (`skip` / `xfail` / `@Ignore` / leaving only `.only` — also check that tests were not silently removed);
   - loosening type checking (`any`, `cast`, `# type: ignore`, `eslint-disable`, lowering tsconfig `strict`);
   - keeping two implementations so it "seems to work" instead of deleting the old code.

**Exit condition**: every step done, every verification passed, no leftover temporary or commented-out code.

---

## Phase 4: acceptance and delivery report

1. Run **all** verification: tests, type check, lint, build, and actually start or exercise the critical path — passing unit tests alone is not enough.
2. Run the line-count scan (`scripts/check_file_sizes.py`), confirm everything is under threshold, and list the final directory structure with per-file line counts.
3. Static checks: no dependency cycles (`madge --circular` / `jdeps` / the equivalent for the language), no duplicated definitions, no dead code, no unused imports, and no stale references to old paths anywhere — including docs, config, scripts and CI files.
4. Produce the **delivery report**:
   - description of the new structure;
   - the symbol migration map as actually executed, compared against the plan;
   - the verification command and result for each phase;
   - a **"behavior is equivalent before and after" statement**, explaining the basis (test coverage plus a symbol-by-symbol check) and honestly marking what is not covered by tests;
   - a list of open issues, including suspected bugs found along the way, explicitly marked "not modified";
   - a before/after line-count table.

---

## Handling failure

| Situation | Action |
|---|---|
| A step's verification fails | Debug and fix in place. If it is not located within a reasonable time, roll the step back to the previous commit, report to the user, and replan that step |
| The plan turns out to be wrong | Stop and return to phase 2 to update the plan and get approval again |
| The target file has a bug in it | **Do not fix it.** Record it in the open issues list and let the user decide whether to open a separate task |
| The user changes the target mid-way | Stop the current migration and return to phase 1 to re-inventory the affected part |
