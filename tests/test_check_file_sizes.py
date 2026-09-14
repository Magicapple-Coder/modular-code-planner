#!/usr/bin/env python3
"""Self-tests for scripts/check_file_sizes.py. Standard library only.

Run:  python -m unittest discover -s tests -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCANNER = os.path.join(REPO, "scripts", "check_file_sizes.py")


def write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join("x" for _ in range(lines)) + "\n")


def run(*args):
    r = subprocess.run([sys.executable, SCANNER] + list(args),
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


class ScannerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="mcp-test-")
        cls.proj = os.path.join(cls.tmp, "proj")
        write(os.path.join(cls.proj, "src", "big.ts"), 600)
        write(os.path.join(cls.proj, "src", "warn.ts"), 350)
        write(os.path.join(cls.proj, "src", "main.ts"), 180)
        write(os.path.join(cls.proj, "src", "small.py"), 20)
        write(os.path.join(cls.proj, "src", "big.generated.ts"), 900)
        write(os.path.join(cls.proj, "src", "types.d.ts"), 900)
        write(os.path.join(cls.proj, "node_modules", "dep.js"), 900)
        write(os.path.join(cls.proj, ".venv", "lib.py"), 900)

    def test_exit_code_1_when_over_hard_threshold(self):
        code, out = run(self.proj, "--lang", "en")
        self.assertEqual(code, 1)
        self.assertIn("HARD", out)

    def test_exit_code_2_when_path_missing(self):
        """A typo in the path must never read as a clean bill of health."""
        code, out = run(os.path.join(self.tmp, "does-not-exist"), "--lang", "en")
        self.assertEqual(code, 2)
        self.assertIn("does not exist", out)

    def test_exit_code_2_on_empty_directory(self):
        empty = os.path.join(self.tmp, "empty")
        os.makedirs(empty, exist_ok=True)
        code, out = run(empty, "--lang", "en")
        self.assertEqual(code, 2)
        self.assertIn("No scannable code files", out)

    def test_exit_code_2_when_soft_exceeds_hard(self):
        code, _ = run(self.proj, "--soft", "600", "--hard", "500")
        self.assertEqual(code, 2)

    def test_default_exclusions(self):
        """Dependencies, virtualenvs, generated files and declarations are skipped."""
        _, out = run(self.proj, "--lang", "en")
        self.assertNotIn("node_modules", out)
        self.assertNotIn(".venv", out)
        self.assertNotIn("big.generated.ts", out)
        self.assertNotIn("types.d.ts", out)
        self.assertIn("Scanned 4 code files", out)

    def test_ext_with_spaces_is_tolerated(self):
        _, out = run(self.proj, "--ext", "py, ts", "--lang", "en")
        self.assertIn("big.ts", out)      # the space must not silently drop .ts

    def test_ext_without_dot_is_tolerated(self):
        _, out = run(self.proj, "--ext", "ts", "--lang", "en")
        self.assertIn("big.ts", out)
        self.assertNotIn("small.py", out)

    def test_exclude_glob(self):
        _, out = run(self.proj, "--ext", "ts", "--exclude-glob", "big.ts", "--lang", "en")
        self.assertNotIn("big.ts", out)

    def test_entry_file_reported_separately(self):
        _, out = run(self.proj, "--lang", "en")
        self.assertIn("Entry files too long", out)
        self.assertIn("main.ts", out)

    def test_entry_max_disables_entry_section(self):
        _, out = run(self.proj, "--lang", "en", "--entry-max", "500")
        self.assertNotIn("Entry files too long", out)

    def test_paths_use_forward_slashes(self):
        _, out = run(self.proj, "--lang", "en")
        self.assertIn("src/big.ts", out)
        self.assertNotIn("src\\big.ts", out)

    def test_single_file_mode(self):
        code, out = run(os.path.join(self.proj, "src", "big.ts"), "--lang", "en")
        self.assertEqual(code, 1)
        self.assertIn("Scanned 1 code files", out)

    def test_json_output(self):
        _, out = run(self.proj, "--lang", "en", "--json")
        data = json.loads(out)
        self.assertEqual(data["scanned"], 4)
        self.assertEqual(len(data["hard_over"]), 1)   # big.ts
        self.assertEqual(len(data["warn_over"]), 1)   # warn.ts
        self.assertEqual(data["hard"], 500)
        self.assertTrue(all("lines" in s and "path" in s for s in data["top"]))

    def test_language_switch(self):
        _, en = run(self.proj, "--lang", "en")
        _, zh = run(self.proj, "--lang", "zh")
        self.assertIn("Files over threshold", en)
        self.assertIn("超阈值文件", zh)

    def test_custom_thresholds(self):
        _, out = run(self.proj, "--soft", "200", "--hard", "400", "--lang", "en")
        self.assertIn(">200", out)
        self.assertIn(">400", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
