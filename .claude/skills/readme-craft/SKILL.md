---
name: "readme-craft"
description: "Write or update clear, uniform, best practice README.md files for Franz's repos (quant projects, tools, research code). Use whenever a README is created, updated, reviewed, or a repo is prepared for GitHub."
---

# README Craft

A README answers five questions in this order, fast: **what is this, why should I care, how do I run it, how do I use it, what are the terms.** GitHub's own guidance says it should hold only what someone needs to start using and contributing, with longer documentation elsewhere. The structure below adapts the [standard-readme spec](https://github.com/RichardLitt/standard-readme/blob/main/spec.md) for research and quant repos, which double as portfolio pieces: a recruiter should grasp the project and its headline result in 30 seconds, an engineer should reproduce it in 5 minutes.

## Workflow

1. **Read the repo first.** Entry points, `pyproject.toml` / `requirements.txt`, Python version, notebooks, data sources, CLI, tests, existing README and `git log`. Never describe a feature, flag or file that does not exist.
2. **Pick the variant:** *research / quant project* (default: a question, a method, results) or *tool / library* (installable package, API). The template below covers both; drop sections marked optional when they would be empty. No empty headings, no "coming soon".
3. **Draft** from the template.
4. **Verify every command.** Run the install and usage commands in a fresh virtual environment where possible. Copy numbers in the Results section from actual output, never from memory, and say which command produced them.
5. **Lint:** `python <skill dir>/scripts/check_readme.py README.md` must report no errors. Fix warnings unless there is a reason not to.
6. **Commit** as `docs(readme): ...` (see the git-commits skill), in the same commit as the feature when documenting a new feature.

When updating an existing README: keep Franz's wording where it is accurate, fix what is stale, restructure only if the order is wrong, and say in two lines what changed.

## Template

````markdown
# project-name

One sentence on what it does and for whom, under 120 characters.

[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![Cumulative returns of the strategy versus the benchmark, 2010 to 2025](docs/figures/hero.png)

A short paragraph: the problem, the approach, and the headline result with a number
(for example: "Volatility targeting cut the maximum drawdown from 44% to 24% while
raising the Sharpe ratio from 0.41 to 0.58 on S&P 500 data, 2005 to 2025.").

## Contents
(only when the README exceeds about 100 lines)

## Background
(optional) Motivation, the research question, related work or papers it builds on.

## Installation

Requires Python 3.12.

```bash
git clone https://github.com/<user>/<repo>.git
cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python -m project.run --start 2005-01-01 --target-vol 0.10
```

```python
from project import backtest
result = backtest(prices, target_vol=0.10)
```

Main options as a short table: flag, default, meaning.

## Data
Source, frequency, period, how to obtain it (script or link), licence or terms of
the data. Raw data is not committed; `data/raw/` is created by `make data` or the
download script.

## Methodology
Key steps and assumptions, formulas only where they help (GitHub renders `$...$`).
Explicitly state: return convention, rebalancing, costs, lookahead handling,
in sample and out of sample split. Link to a full write up in `docs/` if one exists.

## Results
A compact table (strategy rows, metric columns) and one or two figures, each with
the command that reproduces it. Caveats in one or two sentences.

## Project structure

```text
├── data/            # raw (ignored) and interim data
├── notebooks/       # 01_..., 02_... analysis notebooks
├── src/project/     # reusable code
├── tests/
└── README.md
```

## Testing
(optional) `pytest` command and what it covers.

## Roadmap
(optional) Two to five concrete next steps.

## Contributing
Where to ask questions and whether issues and pull requests are welcome. Commits
follow Conventional Commits.

## Acknowledgements
(optional) Supervisors, data providers, papers.

## License
MIT © 2026 Franz Triebe. See [LICENSE](LICENSE).
````

## Section rules

* **Title:** the repo name, exactly. One H1 only.
* **Short description:** one line, under 120 characters, no heading, reused as the GitHub "About" text. Say what it is, not that it is "awesome" or "powerful".
* **Badges:** at most three or four that carry information (Python version, licence, CI status). No vanity badges.
* **Hero figure (research repos):** one image showing the key result, stored in the repo (`docs/figures/`), with descriptive alt text. Not an external hotlink.
* **Installation / Usage:** copy pastable code blocks with a language tag (`bash`, `python`, `text`), no `$ ` prompts, commands that actually work from a fresh clone. Name the Python version. Show the shortest path to a first result before options.
* **Results:** numbers with units and periods (`Sharpe 0.58, 2005 to 2025, net of 5 bps costs`), and the command that reproduces them. If results are preliminary, say so.
* **License:** last section, SPDX name and owner. If the repo has no LICENSE file, ask Franz which licence he wants (MIT is the usual default for portfolio code) rather than inventing one; for code he cannot open source (internship, thesis data under NDA) write "All rights reserved" and explain the data restriction in the Data section.
* **Contents:** only when over about 100 lines; GitHub also renders an outline menu automatically.

## Writing rules

* Lead with the outcome, then the details. Short paragraphs, plain words, active voice.
* Never use dashes (hyphens, en dashes or em dashes) as punctuation; use commas, colons, parentheses or full stops. Hyphens inside commands, file names and compound words are fine. The checker flags spaced dashes in prose.
* H2 for sections, H3 at most below that.
* Relative links for repo files (`[methodology](docs/methodology.md)`), so they work on every branch and in clones; no absolute `github.com/.../blob/...` links to the same repo.
* Every image has alt text that says what it shows.
* Keep it under about 300 lines; move long material (full methodology, API reference, data dictionary) into `docs/` and link it. GitHub truncates READMEs beyond 500 KiB.
* No secrets, internal paths (`/Users/franz/...`), personal emails beyond what Franz chooses, or confidential data from internships or the thesis.
* Language: English unless Franz asks otherwise.

## Checker

`scripts/check_readme.py` verifies: single H1 first, a short description under 120 characters, Installation, Usage and License sections with License last, Contents when over 100 lines, code blocks closed and tagged with a language, no `$ ` prompts, images with alt text, relative links and anchors that resolve, no absolute links to the repo's own files, no dash punctuation, no placeholders like TODO. It cannot judge whether the README is clear, so finish with the self review.

## Final self review

1. Could someone who has never seen the repo say what it does and what it found after reading the first screen?
2. Did every install and usage command run in a fresh environment?
3. Do the numbers in Results match the latest run, with units, period and source command?
4. Is everything that exists in the repo and matters (CLI, notebooks, data step) documented, and nothing that does not exist?
5. Does the checker report no errors?