#!/usr/bin/env python3
"""check_commit: lint a commit message against the house convention.

Usage:
  python check_commit.py MSGFILE        lint a message file (also works as a commit-msg hook)
  echo "feat: add x" | python check_commit.py -
  python check_commit.py --install      install as .git/hooks/commit-msg in the current repo
  python check_commit.py --range main..HEAD   lint every commit in a range
"""
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

TYPES = ("feat", "fix", "docs", "refactor", "perf", "test", "build", "ci", "chore", "style", "revert")
HEADER = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[a-z0-9][a-z0-9._/-]*)\))?(?P<bang>!)?: (?P<desc>\S.*)$")
NON_IMPERATIVE = re.compile(r"^(added|adds|adding|fixed|fixes|fixing|updated|updates|updating|changed|changes|"
                            r"changing|removed|removes|removing|created|creates|implemented|implements|"
                            r"refactored|refactors|improved|improves|renamed|renames|moved|moves|deleted|deletes)\b")
FOOTER = re.compile(r"^(BREAKING[ -]CHANGE|[A-Za-z][A-Za-z-]*)(: | #)\S")
AUTO = re.compile(r"^(Merge |Revert \"|fixup! |squash! |amend! )")


def lint(message):
    lines = [ln for ln in message.splitlines() if not ln.startswith("#")]
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines or not lines[0].strip():
        return ["empty commit message"]
    header = lines[0]
    if AUTO.match(header):
        return []
    problems = []
    m = HEADER.match(header)
    if not m:
        return [f"header must be 'type(scope): description' or 'type: description', got: {header!r}"]
    if m["type"] not in TYPES:
        problems.append(f"unknown type {m['type']!r}; use one of: {', '.join(TYPES)}")
    desc = m["desc"]
    if len(header) > 72:
        problems.append(f"header is {len(header)} chars; hard limit 72 (aim for 50)")
    elif len(header) > 50:
        problems.append(f"warning: header is {len(header)} chars; aim for 50 or fewer")
    if desc[0].isupper() and not re.match(r"^[A-Z0-9]{2,}\b", desc):
        problems.append("description should start lowercase after the colon (acronyms like API are fine)")
    if desc.endswith((".", "!", "?", ":", ";")):
        problems.append("no trailing punctuation on the header")
    if NON_IMPERATIVE.match(desc.lower()):
        problems.append(f"use the imperative mood ('add', 'fix', 'update'), not {desc.split()[0]!r}")
    if re.search(r"\s[–—-]\s|—|–", desc):
        problems.append("no dashes as punctuation in the description; use a comma or rephrase")
    if len(lines) > 1 and lines[1].strip():
        problems.append("second line must be blank (separates header from body)")
    in_code = False
    for i, ln in enumerate(lines[2:], start=3):
        if ln.startswith("```"):
            in_code = not in_code
        if in_code or ln.startswith("    ") or "http" in ln or FOOTER.match(ln):
            continue
        if len(ln) > 72:
            problems.append(f"line {i} is {len(ln)} chars; wrap the body at 72")
    if m["bang"] is None and any(ln.startswith("BREAKING") and not FOOTER.match(ln) for ln in lines):
        problems.append("breaking change footer must read 'BREAKING CHANGE: description'")
    return problems


def install():
    git_dir = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True)
    if git_dir.returncode:
        sys.exit("not inside a git repository")
    hook = Path(git_dir.stdout.strip()) / "hooks" / "commit-msg"
    hook.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(__file__).resolve(), hook)
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"installed {hook}")


def lint_range(rev_range):
    shas = subprocess.run(["git", "rev-list", "--no-merges", rev_range], capture_output=True, text=True,
                          check=True).stdout.split()
    failed = 0
    for sha in shas:
        msg = subprocess.run(["git", "log", "-1", "--format=%B", sha], capture_output=True, text=True).stdout
        errors = [p for p in lint(msg) if not p.startswith("warning")]
        if errors:
            failed += 1
            print(f"{sha[:8]} {msg.splitlines()[0]}\n  " + "\n  ".join(errors))
    print(f"{len(shas) - failed}/{len(shas)} commits pass")
    return 1 if failed else 0


def main(argv):
    if not argv:
        sys.exit(__doc__)
    if argv[0] == "--install":
        return install()
    if argv[0] == "--range":
        return lint_range(argv[1])
    message = sys.stdin.read() if argv[0] == "-" else Path(argv[0]).read_text()
    problems = lint(message)
    errors = [p for p in problems if not p.startswith("warning")]
    for p in problems:
        print(("  " if p.startswith("warning") else "  error: ") + p, file=sys.stderr)
    if errors:
        print("commit message rejected (edit and retry; see the git-commits skill)", file=sys.stderr)
        return 1
    if not problems:
        print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
