#!/usr/bin/env python3
"""Scan a project for oversized code files and report those over the threshold.

Usage:
    python check_file_sizes.py <path> [options]

Options:
    --soft N            Warn above N lines (default 300)
    --hard N            Fail above N lines (default 500)
    --entry-max N       Entry-file target (default 100)
    --top N             Also list the N longest files (default 10)
    --ext a,b,c         Scan only these extensions (with or without dot)
    --ignore a,b        Extra directory names to skip
    --exclude-glob a,b  Extra filename globs to skip (e.g. "*.generated.*")
    --json              Emit JSON instead of text
    --lang {auto,en,zh} Output language (default: auto from system locale)

Exit codes:
    0 = scanned successfully, nothing over the hard threshold
    1 = at least one file over the hard threshold
    2 = bad usage / path missing / nothing to scan (never a silent pass)
"""
import argparse
import fnmatch
import json
import locale
import os
import sys

DEFAULT_EXT = {
    ".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte",
    ".java", ".kt", ".kts", ".go", ".rs", ".rb", ".php", ".cs", ".cpp",
    ".cc", ".c", ".h", ".hpp", ".swift", ".m", ".mm", ".scala", ".sh",
    ".sql", ".html", ".css", ".scss", ".less", ".dart", ".lua", ".r",
}

DEFAULT_IGNORE = {
    ".git", ".svn", ".hg", "node_modules", "dist", "build", "out",
    "venv", ".venv", "env", "__pycache__", ".next", ".nuxt", "coverage",
    "target", "vendor", ".idea", ".vscode", ".cache", "tmp", "temp",
    ".mypy_cache", ".pytest_cache", ".tox", "egg-info",
}

# Generated artifacts, lock files and declaration files: large, but not
# the kind of code this tool is meant to flag.
DEFAULT_EXCLUDE_GLOB = {
    "*.min.js", "*.min.css", "*.bundle.js", "*.chunk.js",
    "*.d.ts", "*.generated.*", "*.g.cs", "*.designer.cs", "*.pb.go",
    "*.pb.cc", "*.pb.h", "*_pb2.py", "*_pb2_grpc.py", "*.g.dart",
    "*lock.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "poetry.lock", "Pipfile.lock", "*.lock",
    "*.svg", "*.map", "*.snap",
}

# Entry-file name heuristics. Reported separately, never part of the hard verdict.
ENTRY_NAMES = {
    "main.py", "__main__.py", "app.py", "cli.py", "manage.py", "wsgi.py", "asgi.py",
    "main.ts", "main.tsx", "main.js", "main.jsx", "index.ts", "index.tsx",
    "index.js", "index.jsx", "app.ts", "app.tsx", "app.js", "app.jsx",
    "main.go", "main.rs", "main.c", "main.cpp", "main.java", "App.swift",
    "MainActivity.kt", "program.cs", "Program.cs",
}

MESSAGES = {
    "en": {
        "path_missing": "Error: path does not exist -> {path}",
        "soft_gt_hard": "Error: --soft ({soft}) must not exceed --hard ({hard})",
        "ext_empty": "Error: --ext did not yield any valid extension",
        "nothing": ("No scannable code files found (path: {path}).\n"
                    "Check the path, and whether this project needs --ext."),
        "header": "Scanned {n} code files{skipped} | soft >{soft} lines | hard >{hard} lines\n",
        "skipped": " ({k} unreadable, skipped)",
        "over_title": "== Files over threshold (split these) ==",
        "hard": "HARD",
        "warn": "warn",
        "clean": "OK - no file exceeds the soft threshold (>{soft} lines).",
        "entry_title": "== Entry files too long (target <={max} lines, wiring only) ==",
        "entry": "entry",
        "top_title": "== Longest {n} files ==",
        "summary": ("Summary: {n_warn} over soft (>{soft}), {n_hard} over hard (>{hard}), "
                    "{n_entry} long entry files (>{max})"),
    },
    "zh": {
        "path_missing": "错误: 路径不存在 -> {path}",
        "soft_gt_hard": "错误: --soft({soft}) 不应大于 --hard({hard})",
        "ext_empty": "错误: --ext 未解析出任何有效扩展名",
        "nothing": ("未发现可扫描的代码文件（路径: {path}）。\n"
                    "请确认路径是否正确、是否需要用 --ext 指定扩展名。"),
        "header": "扫描 {n} 个代码文件{skipped} | 软阈值 >{soft} 行 | 硬阈值 >{hard} 行\n",
        "skipped": "（{k} 个无法读取已跳过）",
        "over_title": "== 超阈值文件（需要拆分） ==",
        "hard": "硬超标",
        "warn": "警告",
        "clean": "没有文件超过软阈值（>{soft} 行）。",
        "entry_title": "== 入口文件偏长（目标 <={max} 行，应只做装配） ==",
        "entry": "入口",
        "top_title": "== 行数 Top {n} ==",
        "summary": ("汇总: 警告(>{soft}) {n_warn} 个, 硬超标(>{hard}) {n_hard} 个, "
                    "入口偏长(>{max}) {n_entry} 个"),
    },
}


def resolve_lang(requested):
    """Pick an output language; follow the system locale when not specified."""
    if requested in MESSAGES:
        return requested
    try:
        code = (locale.getlocale()[0] or "") + (os.environ.get("LANG") or "")
    except (ValueError, TypeError):
        code = ""
    return "zh" if "zh" in code.lower() or "chinese" in code.lower() else "en"


def count_lines(path):
    """Return the line count, or None when the file cannot be read."""
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return None


def parse_csv(value):
    return [t.strip() for t in value.split(",") if t.strip()]


def normalize_ext(token):
    token = token.strip().lower()
    if not token:
        return None
    return token if token.startswith(".") else "." + token


def main():
    ap = argparse.ArgumentParser(
        description="Scan code files for line counts and report oversized ones.")
    ap.add_argument("path", help="project root directory, or a single file")
    ap.add_argument("--soft", type=int, default=300,
                    help="warn above this many lines (default 300)")
    ap.add_argument("--hard", type=int, default=500,
                    help="fail above this many lines (default 500)")
    ap.add_argument("--entry-max", type=int, default=100, dest="entry_max",
                    help="entry-file target in lines (default 100)")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--ext", default="")
    ap.add_argument("--ignore", default="")
    ap.add_argument("--exclude-glob", default="", dest="exclude_glob")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--lang", default="auto", choices=["auto", "en", "zh"])
    args = ap.parse_args()

    m = MESSAGES[resolve_lang(args.lang)]
    root = os.path.abspath(args.path)

    # Validate hard: a bad path must never look like "everything is fine".
    if not os.path.exists(root):
        print(m["path_missing"].format(path=root), file=sys.stderr)
        return 2
    if args.soft > args.hard:
        print(m["soft_gt_hard"].format(soft=args.soft, hard=args.hard),
              file=sys.stderr)
        return 2

    if args.ext:
        exts = {e for e in (normalize_ext(t) for t in parse_csv(args.ext)) if e}
        if not exts:
            print(m["ext_empty"], file=sys.stderr)
            return 2
    else:
        exts = DEFAULT_EXT

    ignore = DEFAULT_IGNORE | set(parse_csv(args.ignore))
    exclude_globs = DEFAULT_EXCLUDE_GLOB | set(parse_csv(args.exclude_glob))

    files = []
    if os.path.isfile(root):
        files.append(root)
    else:
        for dirpath, dirs, names in os.walk(root, followlinks=False):
            dirs[:] = [d for d in dirs
                       if d not in ignore and not d.startswith(".")]
            for n in names:
                if os.path.splitext(n)[1].lower() not in exts:
                    continue
                if any(fnmatch.fnmatch(n, g) for g in exclude_globs):
                    continue
                files.append(os.path.join(dirpath, n))

    stats, skipped = [], []
    for fp in files:
        n = count_lines(fp)
        if n is None:
            skipped.append(fp)
            continue
        # Report POSIX-style separators on every platform: portable in reports,
        # and still valid input on Windows.
        if os.path.isdir(root):
            rel = os.path.relpath(fp, root).replace(os.sep, "/")
        else:
            rel = fp.replace(os.sep, "/")
        stats.append({"lines": n, "path": rel})

    if not stats:
        print(m["nothing"].format(path=root), file=sys.stderr)
        return 2

    stats.sort(key=lambda s: (-s["lines"], s["path"]))

    hard_over = [s for s in stats if s["lines"] > args.hard]
    warn_only = [s for s in stats if args.soft < s["lines"] <= args.hard]
    entries = [s for s in stats
               if os.path.basename(s["path"]) in ENTRY_NAMES
               and s["lines"] > args.entry_max]

    if args.as_json:
        print(json.dumps({
            "root": root,
            "scanned": len(stats),
            "unreadable": len(skipped),
            "soft": args.soft,
            "hard": args.hard,
            "entry_max": args.entry_max,
            "hard_over": hard_over,
            "warn_over": warn_only,
            "entry_over": entries,
            "top": stats[:args.top],
        }, ensure_ascii=False, indent=2))
        return 1 if hard_over else 0

    skipped_txt = m["skipped"].format(k=len(skipped)) if skipped else ""
    print(m["header"].format(n=len(stats), skipped=skipped_txt,
                             soft=args.soft, hard=args.hard))

    if warn_only or hard_over:
        print(m["over_title"])
        for s in hard_over + warn_only:
            level = m["hard"] if s["lines"] > args.hard else m["warn"]
            print(f"  [{level}] {s['lines']:>6}  {s['path']}")
    else:
        print(m["clean"].format(soft=args.soft))

    if entries:
        print("\n" + m["entry_title"].format(max=args.entry_max))
        for s in entries:
            print(f"  [{m['entry']}] {s['lines']:>6}  {s['path']}")

    print("\n" + m["top_title"].format(n=args.top))
    for s in stats[:args.top]:
        print(f"  {s['lines']:>6}  {s['path']}")

    print("\n" + m["summary"].format(soft=args.soft, hard=args.hard,
                                     max=args.entry_max,
                                     n_warn=len(warn_only),
                                     n_hard=len(hard_over),
                                     n_entry=len(entries)))
    return 1 if hard_over else 0


if __name__ == "__main__":
    sys.exit(main())
