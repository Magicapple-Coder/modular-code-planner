#!/usr/bin/env python3
"""Validate the Agent Skills package: frontmatter, naming, and link integrity.

No third-party dependencies, so this runs anywhere.

Run:  python -m unittest discover -s tests -v
"""
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.basename(REPO)

# Fields defined by the Agent Skills specification, plus its experimental one.
SPEC_FIELDS = {"name", "description", "license", "compatibility", "metadata",
               "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
DOCS = ["SKILL.md", "SKILL.en.md", "README.md", "README.zh-CN.md",
        "CONTRIBUTING.md"]


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def frontmatter(text):
    """Parse the leading YAML frontmatter into {key: raw_string} without PyYAML."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    block = text[4:end]
    out, key, buf = {}, None, []
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z][\w-]*):\s?(.*)$", line)
        if m and not line.startswith((" ", "\t")):
            if key:
                out[key] = "\n".join(buf).strip()
            key, buf = m.group(1), [m.group(2)]
        elif key:
            buf.append(line)
    if key:
        out[key] = "\n".join(buf).strip()
    return out


def strip_quotes(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


class FrontmatterTest(unittest.TestCase):
    def test_skill_md_has_frontmatter(self):
        fm = frontmatter(read(os.path.join(REPO, "SKILL.md")))
        self.assertIsNotNone(fm, "SKILL.md must start with a --- frontmatter block")

    def test_required_fields_present(self):
        fm = frontmatter(read(os.path.join(REPO, "SKILL.md")))
        for field in ("name", "description"):
            self.assertIn(field, fm, "frontmatter is missing the required field: " + field)

    def test_only_spec_fields(self):
        """Host-specific fields break portability across agents."""
        fm = frontmatter(read(os.path.join(REPO, "SKILL.md")))
        extra = set(fm) - SPEC_FIELDS
        self.assertEqual(extra, set(),
                         "non-spec frontmatter fields found: " + ", ".join(sorted(extra)))

    def test_name_matches_directory_and_spec(self):
        fm = frontmatter(read(os.path.join(REPO, "SKILL.md")))
        name = strip_quotes(fm["name"])
        self.assertEqual(name, PKG,
                         "frontmatter name must match the package directory name")
        self.assertLessEqual(len(name), 64)
        self.assertRegex(name, NAME_RE)

    def test_description_length(self):
        fm = frontmatter(read(os.path.join(REPO, "SKILL.md")))
        desc = strip_quotes(fm["description"])
        self.assertGreater(len(desc), 0)
        self.assertLessEqual(len(desc), 1024, "description exceeds the 1024 char limit")

    def test_description_triggers_in_both_languages(self):
        """Cross-agent discovery relies on the description; keep both languages in it."""
        fm = frontmatter(read(os.path.join(REPO, "SKILL.md")))
        desc = strip_quotes(fm["description"])
        latin = sum(1 for c in desc if c.isascii() and c.isalpha())
        han = len(re.findall(r"[\u4e00-\u9fff]", desc))
        self.assertGreater(latin, 100, "not enough English trigger text")
        self.assertGreater(han, 20, "not enough Chinese trigger text")

    def test_english_edition_has_parity(self):
        """The English edition must keep the same section structure as the original."""
        def sections(doc):
            return [l for l in read(os.path.join(REPO, doc)).splitlines()
                    if l.startswith("## ")]
        self.assertEqual(len(sections("SKILL.md")), len(sections("SKILL.en.md")),
                         "SKILL.en.md has drifted from SKILL.md")

    def test_license_declared_and_shipped(self):
        fm = frontmatter(read(os.path.join(REPO, "SKILL.md")))
        self.assertIn("license", fm)
        self.assertTrue(os.path.exists(os.path.join(REPO, "LICENSE")))


class LinkIntegrityTest(unittest.TestCase):
    def test_relative_links_resolve(self):
        broken = []
        for doc in DOCS:
            path = os.path.join(REPO, doc)
            if not os.path.exists(path):
                continue
            for target in LINK_RE.findall(read(path)):
                if "://" in target or target.startswith("#"):
                    continue
                target = target.split("#")[0]
                if not os.path.exists(os.path.join(REPO, target)):
                    broken.append(f"{doc} -> {target}")
        self.assertEqual(broken, [], "broken relative links:\n" + "\n".join(broken))

    def test_every_chinese_reference_has_english_twin(self):
        missing = []
        for rel in ["references/module-split-patterns.md",
                    "references/refactoring-workflow.md"]:
            twin = rel[:-3] + ".en.md"
            if not os.path.exists(os.path.join(REPO, twin)):
                missing.append(twin)
        self.assertEqual(missing, [], "missing English editions: " + ", ".join(missing))

    def test_readmes_link_to_each_other(self):
        en = read(os.path.join(REPO, "README.md"))
        zh = read(os.path.join(REPO, "README.zh-CN.md"))
        self.assertIn("README.zh-CN.md", en)
        self.assertIn("README.md", zh)


class PackageTest(unittest.TestCase):
    def test_script_present_and_compiles(self):
        path = os.path.join(REPO, "scripts", "check_file_sizes.py")
        self.assertTrue(os.path.exists(path))
        compile(read(path), path, "exec")

    def test_entry_document_declares_its_dependencies(self):
        fm = frontmatter(read(os.path.join(REPO, "SKILL.md")))
        self.assertIn("compatibility", fm,
                      "declare runtime requirements so hosts can check them")


if __name__ == "__main__":
    unittest.main(verbosity=2)
