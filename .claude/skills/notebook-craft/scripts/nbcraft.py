"""nbcraft: build, execute and check Jupyter notebooks in the house format."""
import json
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook


class NB:
    """Collect cells in order, then save as a valid nbformat v4 notebook."""

    def __init__(self, title):
        self.nb = new_notebook()
        self.nb.metadata.update({
            "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
            "language_info": {"name": "python"},
            "title": title,
        })

    def md(self, text):
        self.nb.cells.append(new_markdown_cell(_dedent(text)))
        return self

    def code(self, src, tags=None):
        cell = new_code_cell(_dedent(src))
        if tags:
            cell.metadata["tags"] = list(tags)
        self.nb.cells.append(cell)
        return self

    def save(self, path):
        nbformat.validate(self.nb)
        nbformat.write(self.nb, str(path))
        return Path(path)


def _dedent(text):
    return textwrap.dedent(text).strip("\n")


def tidy(path):
    """Sort imports and format code cells in place with ruff (skipped if ruff is missing)."""
    ruff = shutil.which("ruff")
    if ruff:
        subprocess.run([ruff, "check", "--select", "I,F401", "--fix", "-q", str(path)], check=False)
        subprocess.run([ruff, "format", "-q", str(path)], check=False)
    return Path(path)


def execute(path, timeout=600, cwd=None):
    """Restart and Run All equivalent: fresh kernel, top to bottom, outputs saved in place."""
    path = Path(path)
    nb = nbformat.read(str(path), as_version=4)
    NotebookClient(nb, timeout=timeout, kernel_name="python3",
                   resources={"metadata": {"path": str(cwd or path.parent)}}).execute()
    nbformat.write(nb, str(path))
    return path


def check(path, max_lines=40):
    """Return a list of problems. Empty list means the notebook passes the quality gate."""
    nb = nbformat.read(str(path), as_version=4)
    cells = nb.cells
    problems = []
    if not cells or cells[0].cell_type != "markdown" or not cells[0].source.lstrip().startswith("# "):
        problems.append("first cell must be a markdown H1 title")
    headings = [c for c in cells if c.cell_type == "markdown" and re.search(r"^## ", c.source, re.M)]
    if len(headings) < 3:
        problems.append("fewer than 3 numbered H2 sections")
    if not any("parameters" in c.metadata.get("tags", []) for c in cells if c.cell_type == "code"):
        problems.append("no code cell tagged 'parameters'")
    counts, prev = [], None
    for i, c in enumerate(cells):
        if c.cell_type == "code":
            n = len(c.source.splitlines())
            if n > max_lines:
                problems.append(f"cell {i}: {n} lines (max {max_lines}); split it or use a function")
            if not c.source.strip():
                problems.append(f"cell {i}: empty code cell")
            if re.search(r"^\s*[!%]pip install", c.source, re.M):
                problems.append(f"cell {i}: pip install inside the notebook")
            for o in c.get("outputs", []):
                if o.get("output_type") == "error":
                    problems.append(f"cell {i}: error output {o.get('ename')}")
                if o.get("name") == "stderr" and "Warning" in o.get("text", ""):
                    problems.append(f"cell {i}: unhandled warning in output")
            counts.append(c.get("execution_count"))
            if prev is not None and prev.cell_type == "code" and "\n" not in c.source and "\n" not in prev.source:
                problems.append(f"cells {i-1},{i}: consecutive one line code cells; merge them")
        if c.cell_type == "markdown" and re.search(r"\s[–—]\s|\s--?\s", c.source):
            problems.append(f"cell {i}: dash used as punctuation in markdown")
        prev = c
    if counts and counts != list(range(1, len(counts) + 1)):
        problems.append("execution counts not 1..N in order; run it top to bottom in a fresh kernel")
    ruff = shutil.which("ruff")
    if ruff:
        lint = subprocess.run([ruff, "check", "--select", "E,F,I,B,UP", "--ignore", "E501",
                               "--output-format", "concise", str(path)], capture_output=True, text=True)
        problems += [f"ruff: {ln}" for ln in lint.stdout.splitlines() if ".ipynb:" in ln]
    else:
        problems.append("ruff not installed; run: pip install ruff")
    size_mb = Path(path).stat().st_size / 1e6
    if size_mb > 10:
        problems.append(f"file is {size_mb:.1f} MB; lower figure dpi or drop large outputs")
    return problems


if __name__ == "__main__":
    issues = check(sys.argv[1])
    print(json.dumps(issues, indent=2) if issues else "PASS")
