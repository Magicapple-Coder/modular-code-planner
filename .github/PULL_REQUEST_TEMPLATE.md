## What this changes

<!-- One or two sentences. What problem, and what the fix is. -->

## Type

- [ ] Scanner (`scripts/check_file_sizes.py`)
- [ ] Skill rules (`SKILL.md` / `SKILL.en.md`)
- [ ] Reference documentation (`references/`)
- [ ] Tests
- [ ] README or other docs
- [ ] CI

## Checklist

- [ ] `python -m unittest discover -s tests -v` passes
- [ ] `python scripts/check_file_sizes.py . --lang en` exits `0`
- [ ] Both language editions updated together (`SKILL.md` ↔ `SKILL.en.md`, and the same for `references/` and `prompts/`)
- [ ] If a frontmatter field was added, `tests/test_skill_package.py` was updated too
- [ ] If a scanner flag was added, there is a test for it — **including its failure case**
- [ ] No new runtime dependency

## Notes for the reviewer

<!-- Anything you tried that did not work, anything you are unsure about, anything deliberately left out. -->
