#!/usr/bin/env python3
"""check_readme: lint a README.md against the house structure.

Usage: python check_readme.py [path/to/README.md]   (default: ./README.md)
Prints PASS, or a list of problems (errors first, then warnings). Exit code 1 on errors.
"""
import re
import sys
from pathlib import Path

REQUIRED = {
    "install": r"^(installation|install|setup|getting started|quickstart|quick start)$",
    "usage": r"^(usage|how to use|quickstart|quick start|getting started|running|reproducing.*)$",
    "license": r"^licen[cs]e$",
}
BADGE = re.compile(r"^\s*(\[!\[|!\[)[^\]]*\]\(https?://(img\.shields\.io|github\.com/.+/badge|badge)")


def strip_code(lines):
    out, in_code = [], False
    for ln in lines:
        if ln.lstrip().startswith("```"):
            in_code = not in_code
            out.append("")
            continue
        out.append("" if in_code else ln)
    return out


def check(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    prose = strip_code(lines)
    errors, warnings = [], []

    # title and short description
    first = next((i for i, ln in enumerate(prose) if ln.strip()), None)
    if first is None or not re.match(r"^# \S", prose[first]):
        errors.append("first line must be a single H1 title ('# Project name')")
    if sum(1 for ln in prose if re.match(r"^# \S", ln)) > 1:
        errors.append("only one H1; use H2 for sections")
    desc = None
    for ln in prose[(first or 0) + 1:]:
        s = ln.strip()
        if not s or BADGE.match(s) or s.startswith(("<p", "</p", "<img", "![")):
            continue
        desc = s
        break
    if desc is None or desc.startswith("#"):
        errors.append("missing one line description directly under the title (and badges)")
    elif len(desc) > 120:
        warnings.append(f"short description is {len(desc)} chars; keep it under 120 (it doubles as the GitHub About text)")

    # sections
    h2 = [(i, ln[3:].strip()) for i, ln in enumerate(prose) if ln.startswith("## ")]
    names = [re.sub(r"^\d+[.)]?\s*", "", n).lower() for _, n in h2]
    for key, pattern in REQUIRED.items():
        if not any(re.match(pattern, n) for n in names):
            errors.append(f"missing a '{key}' section (H2)")
    if names and not re.match(REQUIRED["license"], names[-1]):
        warnings.append("License should be the last section")
    if len(lines) > 100 and not re.search(r"^#*\s*(table of )?contents\s*$", text, re.I | re.M):
        warnings.append(f"README is {len(lines)} lines; add a Contents list after the description")
    if len(lines) > 400:
        warnings.append("README over 400 lines; move detail into docs/ and link it")
    for i, ln in enumerate(prose):
        if re.match(r"^#{4,} ", ln):
            warnings.append(f"line {i+1}: heading deeper than H3; flatten the structure")

    # code blocks
    in_code = False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("```"):
            if not in_code and ln.strip() == "```":
                warnings.append(f"line {i+1}: code block without a language (```bash, ```python, ```text)")
            in_code = not in_code
    if in_code:
        errors.append("unclosed code block")
    if not re.search(r"^```", text, re.M):
        errors.append("no code blocks; install and usage need copy pastable commands")
    if re.search(r"^\s*\$ \S", text, re.M):
        warnings.append("drop the '$ ' prompt from commands so they copy paste cleanly")

    # links and images
    for i, ln in enumerate(prose):
        for alt, target in re.findall(r"!\[([^\]]*)\]\(([^)\s]+)", ln):
            if not alt.strip():
                errors.append(f"line {i+1}: image without alt text")
        for target in re.findall(r"\]\(([^)\s#]+)(?:#[^)]*)?\)", ln):
            if re.match(r"^(https?:|mailto:)", target):
                if "github.com" in target and "/blob/" in target:
                    warnings.append(f"line {i+1}: absolute GitHub blob link; use a relative path")
                continue
            local = (path.parent / target.lstrip("/")) if not target.startswith("/") else (path.parent / target[1:])
            if not local.exists():
                errors.append(f"line {i+1}: broken relative link {target}")
        for anchor in re.findall(r"\]\(#([^)]+)\)", ln):
            slugs = {re.sub(r"[^\w\- ]", "", n.lower()).strip().replace(" ", "-") for _, n in h2}
            slugs |= {re.sub(r"[^\w\- ]", "", ln2[4:].lower()).strip().replace(" ", "-")
                      for ln2 in prose if ln2.startswith("### ")}
            if anchor.lower() not in slugs:
                errors.append(f"line {i+1}: anchor #{anchor} matches no heading")

    # writing
    for i, ln in enumerate(prose):
        bare = re.sub(r"`[^`]*`", "", ln)
        if re.search(r"—|–|\s--\s|\w\s-\s\w", bare) and not re.match(r"^\s*[-*] ", ln):
            errors.append(f"line {i+1}: dash used as punctuation")
        if re.search(r"\b(TODO|TBD|lorem ipsum)\b", bare, re.I):
            warnings.append(f"line {i+1}: placeholder text left in")

    return errors, warnings


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    errs, warns = check(target)
    for e in errs:
        print("error:", e)
    for w in warns:
        print("warning:", w)
    if not errs and not warns:
        print("PASS")
    sys.exit(1 if errs else 0)
