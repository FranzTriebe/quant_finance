---
name: "notebook-craft"
description: "Build consistent, well structured Jupyter notebooks (.ipynb) in Franz's house format. Use for any notebook request, a backtest or analysis in Jupyter, or cleaning up an existing notebook."
---

# Notebook Craft

Every notebook reads as a computational narrative: a question at the top, numbered steps in the middle, an interpreted answer at the end, and it runs top to bottom in a fresh kernel without touching anything by hand. The rules below combine the PLOS Computational Biology "Ten simple rules for writing and sharing computational analyses in Jupyter Notebooks" (Rule et al. 2019) with standard tooling practice (nbformat, nbclient, ruff, papermill, jupytext, nbstripout) and a few quant finance conventions.

## Workflow

1. **Plan the story first.** Write down the one question the notebook answers, the audience (default: Franz in three months, so err on overexplaining the why), and the section list. One goal per notebook. If there are two goals, make two notebooks named `01_...`, `02_...` and have the first save its intermediate output (parquet or csv in `data/interim/`) for the second.
2. **Write the helper.** Save the `nbcraft.py` helper below to the scratchpad. Build notebooks with it from a Python build script; never hand write notebook JSON.
3. **Build** the cells in the canonical structure (next section).
4. **Tidy, execute, check:** `tidy(path)` (ruff import sort and format), `execute(path)` (fresh kernel, top to bottom, the equivalent of Restart and Run All), then `check(path)`. Fix every reported problem in the build script and repeat until it prints `PASS`.
5. **Look at the outputs.** Extract every `image/png` output and view it; read every printed table. A notebook that runs but shows an ugly axis or a 3000 row dataframe is not done.
6. **Fill the key findings** in the title cell with the actual numbers from the run, rerun, check again.
7. **Deliver** the executed .ipynb (outputs included, so it renders on GitHub and nbviewer) with SendUserFile. Offer an HTML export (`jupyter nbconvert --to html`) only if he wants to share it with someone without Jupyter.

For an existing notebook Franz wants cleaned up: read it fully, keep his code and logic, restructure it into the canonical layout, run steps 4 to 7, and list in two or three lines what changed structurally.

## Canonical structure

Always this order. Section numbers are fixed in the H2 text.

| # | Cell(s) | Content |
|---|---|---|
| Title | markdown | `# Title`, then a line `**Author:** Franz Triebe · **Date:** YYYY-MM-DD · **Status:** draft / final`, then **Question** (one or two sentences), **Data** (source, frequency, period, retrieval date), and a `> **Key findings**` blockquote with two or three numbered results (filled after the run). |
| Contents | markdown | Numbered links to each H2 section: `[2. Data](#2.-Data)`. |
| `## 1. Setup` | code | (a) one imports cell: stdlib, third party, local, ruff sorted; (b) one parameters cell tagged `parameters`, UPPER_CASE constants only (paths, dates, tickers, seeds, windows, costs, annualisation factor), each with a short unit comment; (c) one style cell: matplotlib rcParams, pandas display options, `rng = np.random.default_rng(SEED)`. |
| `## 2. Data` | md + code | Where the data comes from and why. Load, then assert shape, dtypes, index type, date range and NaN counts. Show `.head()` or `.describe()`, never a whole frame. |
| `## 3. Method` (or `3. Cleaning` and `4. Method`) | md + code | Formulas in LaTeX, assumptions stated, helper functions defined here. |
| `## N. Results` | md + code | Subsections `### N.1`, `### N.2`. Each block is: markdown saying what is computed and why, code, output, then a short **Reading the chart / table** markdown cell with the interpretation. |
| `## N+1. Conclusions` | md (+ optional code) | Numbered answers to the question, caveats, next step. |
| `## N+2. Appendix: environment` | code | Python and key library versions printed (last cell). |

Add `## Robustness` or `## Dead ends` sections before the conclusions when exploration produced alternatives worth documenting (PLOS Rule 2: document the process, not just the results).

## Cell rules

* One meaningful step per code cell, like one paragraph. Target 5 to 25 lines; the checker flags anything over 40. Split, or move logic into a function.
* No runs of one line cells. Merge them into the step they belong to.
* Every new step gets a markdown cell above it saying what and why. Low level detail goes in code comments, the reasoning goes in markdown.
* Anything used twice becomes a function with a one line docstring. Reusable across notebooks: put it in `src/` or a `utils.py` and import it.
* No hidden state: never redefine a variable later with a different meaning, never depend on a cell that is not above, no `del` tricks. Name things for what they hold (`daily_ret`, `ewma_vol`), not `df2`, `temp`, `x`.
* Display a table with `display(...)` or as the last expression, not `print(df)`. Use `print` with f strings only for one line results.
* No `!pip install`, no hardcoded absolute paths, no credentials. Paths are built from a `DATA_DIR = Path("data")` parameter.
* Silence warnings only by fixing the cause; if a warning is genuinely harmless, filter that specific warning with a comment explaining why.
* Long runs (more than a minute): cache the result to disk and load it if present, with a `RECOMPUTE` flag in the parameters cell.

## Markdown style

* H1 only in the title cell, numbered H2 for sections, H3 `N.1` for subsections. Nothing deeper.
* Math in LaTeX: inline `$\sigma_t$`, display `$$ ... $$`. Define every symbol once.
* Callouts as blockquotes: `> **Note:**`, `> **Assumption:**`, `> **Caveat:**`.
* Short sentences, no filler. Never use dashes (hyphens, en dashes or em dashes) as punctuation in prose; use commas, colons, parentheses or full stops. The checker flags spaced dashes.
* Units always stated: annualised or daily, percent or decimal, basis points.

## Figures

* Set style once in the setup cell, never per chart:

```python
plt.rcParams.update({
    "figure.figsize": (10, 4), "figure.dpi": 110,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.3,
    "axes.titleweight": "bold", "axes.titlesize": 12,
})
```

* Every chart has a title, axis labels with units, a legend when there is more than one series, and a small source note (`fig.text(0.01, 0, "Source: ...", fontsize=8, alpha=0.7)`).
* Percent axes use `PercentFormatter(1.0)`. Log axes get readable tick labels (`FormatStrFormatter("%.1f")` for major and minor), never `2 x 10^0`.
* Related panels go in one `plt.subplots` figure with `sharex=True`. Finish with `fig.tight_layout()` and `plt.show()`.
* Keep the default colour cycle consistent across the notebook; the same series always gets the same colour.
* Each figure is followed by a markdown cell that says what to see in it.

## Tables

* Format with `df.style.format({...})`: returns and vol as `{:.2%}`, Sharpe as `{:.2f}`, money with thousands separators, bps as `{:.0f}`.
* Show summaries, not raw data: `.head()`, `.describe()`, a stats frame with strategies as rows and metrics as columns.
* Set `pd.options.display.float_format = "{:,.4f}".format` in the setup cell.

## Quant finance conventions

* State the return convention (simple or log) in the Data or Method section and stick to it. Annualise with an `ANN_FACTOR` parameter (252 daily, 52 weekly, 12 monthly).
* No lookahead: signals and weights computed with data up to t are applied at t+1 (`.shift(1)`), and the markdown says so.
* Seed every random process from `SEED` and use `np.random.default_rng`.
* Out of sample splits, transaction costs and rebalancing frequency are parameters, not literals in the middle of the code.
* Dates are a proper `DatetimeIndex` with a name; state the timezone for intraday data.
* Assert after each transformation that matters (`assert not df.isna().any().any()`, `assert df.index.is_monotonic_increasing`).

## Naming and repository hygiene

* File names: `NN_short_snake_case_description.ipynb` (`01_data_download.ipynb`, `02_vol_targeting.ipynb`). If there are three or more notebooks, add `00_index.ipynb` linking them in order.
* Notebooks live in `notebooks/`, data in `data/raw` (never edited) and `data/interim`, reusable code in `src/`.
* When the project is under git, suggest once: `nbstripout --install` for output free commits, or `jupytext --set-formats ipynb,py:percent` to keep a reviewable `.py` twin, plus `nbdime` for notebook aware diffs. Dependencies go in `requirements.txt` or `environment.yml`.
* A notebook meant to rerun with different inputs keeps all inputs in the `parameters` cell so `papermill in.ipynb out.ipynb -p TICKER SPY` works.

## Quality gate

`check(path)` must print `PASS`. It verifies: H1 title first, at least three H2 sections, a `parameters` tagged cell, no code cell over 40 lines, no empty cells, no runs of one line cells, no `pip install`, no error outputs or unhandled warnings, execution counts exactly 1..N in order (proof of a clean top to bottom run), ruff clean (pyflakes, pycodestyle, isort, bugbear, pyupgrade), no spaced dashes in markdown, file under 10 MB. Then do the visual pass of step 5 yourself; the checker cannot judge whether a chart is good.

## The helper: nbcraft.py

Install once if missing: `pip install --break-system-packages nbformat nbclient ipykernel ruff` (plus the analysis libraries the notebook imports). Save this file to the scratchpad:

```python
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
```

A build script then looks like:

```python
import sys
sys.path.insert(0, "<scratchpad>")
from nbcraft import NB, check, execute, tidy

nb = NB("Volatility targeting on a simulated equity index")
nb.md("""
# Volatility targeting on a simulated equity index

**Author:** Franz Triebe · **Date:** 2026-10-11 · **Status:** draft

**Question.** Does scaling exposure to a constant volatility target improve the Sharpe ratio and drawdowns?

**Data.** Simulated daily log returns, GARCH(1,1), seeded.

> **Key findings**
> 1. ...
""")
nb.md("**Contents**\n1. [Setup](#1.-Setup)\n2. [Data](#2.-Data)\n...")
nb.md("## 1. Setup")
nb.code("import numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom IPython.display import display")
nb.code("SEED = 42\nTARGET_VOL = 0.10  # annualised\nANN_FACTOR = 252", tags=["parameters"])
# ... sections 2 to N ...
path = nb.save("02_vol_targeting.ipynb")
tidy(path); execute(path); print(check(path) or "PASS")
```

Write markdown with normal strings; inside Python triple quoted strings, double the backslashes in LaTeX (`\\sigma`) or use raw strings (`r"""..."""`).

## Final self review

Before delivering, answer yes to all:
1. Could someone read only the markdown cells and understand the question, the method and the answer?
2. Do the key findings at the top quote the actual numbers from this run?
3. Does every chart have title, labels with units, legend, source, and a reading note under it?
4. Are all tunable numbers in the parameters cell and nowhere else?
5. Does `check()` print `PASS` after the final execution?