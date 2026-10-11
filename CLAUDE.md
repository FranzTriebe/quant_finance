# CLAUDE.md · quantlab

## Purpose

This is Franz's research repo for quant projects based on academic papers. The plan for the current project is in `PLAN.md`.

Learning matters as much as the code: Franz has to understand every result he gets.

## How to work here

1. Follow `PLAN.md` one phase at a time. Finish a phase, then stop at its checkpoint and wait for Franz to say go.
2. At each checkpoint:
   * show the results
   * explain each new concept in plain language and link it to his coursework (concept map in `PLAN.md`, section 9)
   * list any open decisions
3. Before saying a phase is done, `pytest -q` must pass and the phase's acceptance checks must hold. Never report done with failing tests.
4. Ask before changing an interface in `quantlab/` that `PLAN.md` defines, and before adding a dependency.
5. Commit at the end of each phase following the `git-commits` skill (Conventional Commits). Use scope `p01` for project work and name the phase in the body, for example `feat(p01): add referee validation module` with body `Phase 2 of PLAN.md.` No attribution trailers.
6. Push after every clear unit of work, so each push on GitHub has one explicit purpose (for example: one module with its tests).

## Skills

Franz's house rules live in `.claude/skills/` and apply to this whole repo:

* `git-commits`: every commit and PR title.
* `notebook-craft`: every Jupyter notebook. A notebook must run without other local files; installed packages, including `quantlab`, are fine.
* `readme-craft`: every README.
* `model-docs`: every report or model write-up, in LaTeX with the shared `modeldoc.sty` (full methodology or 1 to 2 page model brief).
* `academic-graphs`: every figure, in the boxed black and white academic style. The helper lives in the engine as `quantlab.acad`, so notebooks import it like any library.
* `natural-writing`: a final prose pass on every text meant for a reader (reports, READMEs, notebook markdown, commit messages).

Where a skill and this file disagree, the hard rules below and `PLAN.md` win. In particular: lags happen only in `backtest.run`.

## Hard rules (research integrity)

* **No look ahead.**
  * Strategies return target weights as of the close of day t.
  * The only place that lags is `backtest.run(lag=1)`. Never shift inside strategy code.
* **Every backtest variant is a trial** and goes into the trial ledger. Never delete or reset ledger rows.
* **Never tune after looking.** Do not change parameters, the sample or thresholds after seeing holdout or referee results. A bad result gets reported, not fixed.
* **Inside formulas:**
  * use per period (daily) Sharpe ratios and Pearson kurtosis (normal = 3)
  * annualize with √252 only for display
* **Same dates for all trials** in one comparison.
* **Fixed random seeds.** Tests never need the internet (use `data.simulate_returns`).

## Code style

* Python 3.11 or newer, with type hints.
* Short numpy style docstrings that explain the finance, not only the code.
* `quantlab/` holds pure functions. File I/O happens only in `data.py` and in the project notebooks.
* Project work lives in Jupyter notebooks that follow the `notebook-craft` skill. They import `quantlab` like any installed library and need no other local files. Code that tests must import belongs in `quantlab/`.
* Figures follow the `academic-graphs` skill through `quantlab.acad`:
  * black, grey and line styles only, boxed axes, one y axis per panel
  * descriptive panel titles such as `(a) Growth of $1, log scale`; the takeaway goes in the caption (the markdown cell below the figure), not in the figure
  * a note under the figure naming data, sample and definitions
  * saved to `output/<project>/` as vector PDF and 300 dpi PNG

## Writing for Franz (reports, README, comments, chat)

* Use plain, direct language. Give realistic assessments rather than reassurance.
* **Never use dashes as punctuation**: no em dash, no en dash, and no hyphen used as a dash. Rephrase, or use commas, colons or parentheses instead.
* Give numbers with units and sensible rounding. Put tables in markdown.

## Commands

* Setup: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
* Tests: `pytest -q`
* Project 1: open the notebooks in `projects/p01_referee/` in order and run all cells
