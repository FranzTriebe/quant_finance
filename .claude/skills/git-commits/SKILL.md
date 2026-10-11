---
name: "git-commits"
description: "Write uniform, best practice git commits (Conventional Commits plus the seven rules) for Franz's repos. Use whenever committing, splitting changes, writing a commit or PR title, or cleaning up history."
---

# Git Commits

Every commit in Franz's repos follows one format so the history reads like a changelog: [Conventional Commits 1.0](https://www.conventionalcommits.org/en/v1.0.0/) for the header, and Chris Beams' [seven rules](https://cbea.ms/git-commit/) for length, mood and body. A linter (`scripts/check_commit.py`) enforces it.

## Format

```
<type>(<scope>): <description>

<body: what changed and why, wrapped at 72>

<footers>
```

* **Header:** aim for 50 characters, never more than 72 (GitHub truncates beyond that).
* **type:** one of the list below, lowercase.
* **scope:** optional, a lowercase noun naming the area touched: `backtest`, `data`, `signals`, `notebooks`, `readme`, `deps`, `ci`. Reuse scopes already in `git log`; do not invent a new one per commit.
* **description:** imperative mood, lowercase first letter (acronyms like `API` stay uppercase), no trailing period. Test: "If applied, this commit will *description*" must read as a sentence.
* **Blank line** between header and body, and between body and footers.
* **Body:** optional for trivial changes, expected otherwise. Explain the what and the why, not the how (the diff shows how). Wrap at 72. Short bullet lists with `*` are fine.
* **Footers:** `Refs #12`, `Closes #12`, `BREAKING CHANGE: description`, `Co-authored-by: Name <email>`. Keep any attribution trailer the environment adds (for example Claude Code's `Co-Authored-By`) as the last footer.
* **No dashes as punctuation** in header or body (Franz's writing rule); use a comma, colon or a new sentence.

## Types

| type | use for | release effect |
|---|---|---|
| `feat` | new capability for the user of the code (new signal, new CLI flag, new notebook analysis) | minor |
| `fix` | bug fix (wrong return calc, lookahead leak, crash) | patch |
| `docs` | README, docstrings, comments, methodology docs only | none |
| `refactor` | restructure without changing behaviour or results | none |
| `perf` | faster or leaner, same results | none |
| `test` | add or fix tests only | none |
| `build` | dependencies, packaging, `requirements.txt`, `pyproject.toml` | none |
| `ci` | GitHub Actions and other pipeline config | none |
| `chore` | maintenance that fits nowhere else (`.gitignore`, file moves, tooling config) | none |
| `style` | formatting only (ruff format), no logic change | none |
| `revert` | reverting an earlier commit; body says `This reverts commit <sha>` and why | none |

**Breaking change** (any type): add `!` before the colon, `feat(api)!: rename run_backtest to backtest`, and explain in a `BREAKING CHANGE:` footer. In a quant repo a change that alters published results or a function signature others call counts as breaking.

Choosing between close calls: a bug fix that also changes numbers is `fix`, and the body states the effect on results. A refactor that accidentally changes results is a `fix` you have not noticed yet; check before committing.

## Examples

Good:

```
feat(backtest): add volatility targeting overlay

Scale exposure to a 10% annualised target using an EWMA estimate
lagged by one day, so the position never uses same day volatility.
Leverage is capped at 2x via MAX_LEVERAGE.

Refs #12
```

```
fix(data): forward fill only within trading days

Holidays were forward filled from the previous Friday, which created
zero returns on non trading days and understated volatility by about
4%. Reindex to the exchange calendar before filling.
```

```
docs(readme): add quickstart and results table
build(deps): pin pandas 2.2 for parquet support
refactor(signals): extract momentum score function
chore: ignore data/raw and notebook checkpoints
```

Bad, and why:

| message | problem |
|---|---|
| `Added momentum stuff.` | no type, past tense, vague, trailing period |
| `fix: fixed bug` | past tense, says nothing about which bug |
| `update: notebooks` | `update` is not a type; what changed? |
| `feat: add momentum signal, fix data loader, update README` | three commits in one |
| `wip` / `asdf` / `final version 2` | never on a shared branch |

## Workflow (follow every time Claude commits)

1. `git status` and `git diff` (plus `git diff --staged`) to see everything that changed.
2. **Split into atomic commits.** One logical change per commit: the repo should work (tests pass, notebooks run) after each one. Separate a refactor from the feature that needed it, formatting from logic, dependency bumps from code. Stage selectively with `git add <paths>` or `git add -p`.
3. **Never commit:** secrets, `.env`, API keys, credentials; large or raw data files (`data/raw`, anything over a few MB, use `.gitignore` or Git LFS); `.ipynb_checkpoints`, `__pycache__`, `.DS_Store`; notebook outputs if the repo uses `nbstripout`. Check `git diff --staged --stat` before every commit.
4. **Look at the history** (`git log --oneline -15`) to reuse existing scopes and match tone.
5. **Write the message to a file** and commit with `git commit -F msg.txt` (avoids shell quoting problems with multi line messages); delete the file afterwards.
6. **Lint:** `python <skill dir>/scripts/check_commit.py msg.txt` must print `PASS` before committing. Warnings (header 51 to 72 chars) are allowed but worth shortening.
7. Never use `--no-verify` to get past a hook. Never amend, rebase or force push commits that are already pushed unless Franz asks. Do not push unless asked.
8. After committing, show the result with `git log --oneline -n <count>`.

## Branches and pull requests

* Branch names: `<type>/<short-kebab-description>`, for example `feat/vol-targeting`, `fix/holiday-fill`, `docs/readme-results`.
* PR title uses the same header format as a commit (it becomes the squash commit message). PR description: **What** (one paragraph), **Why**, **How to verify** (commands), **Results impact** (for quant code: do any published numbers change?), and linked issues.
* When squash merging, rewrite the squash message to one clean conventional header plus a body summarising the branch, not the list of WIP commits.

## Cleaning up local history before pushing

For unpushed commits only: `git commit --fixup <sha>` for small corrections, then `git rebase -i --autosquash <base>`. Reword messages that fail the linter with `git rebase -i` and `reword`. Check the whole branch with `python <skill dir>/scripts/check_commit.py --range main..HEAD`.

## Enforcing it in a repo

Offer once per repo, do not do it unasked:

* Local hook: `python <skill dir>/scripts/check_commit.py --install` writes `.git/hooks/commit-msg`, so every commit (by Franz or Claude) is linted.
* Team or CI alternative: `commitlint` with `@commitlint/config-conventional`, or the `pre-commit` framework with a commit-msg stage.