# quant_finance

Quant research projects based on academic papers, built on a tested backtesting and validation engine.

The core is `quantlab`, a small Python package that runs backtests without look ahead bias and then acts as a referee: it asks how much of a backtest result survives once you account for how many variants were tried. Every project in this repo runs its results through that referee before calling anything a finding. The full build plan for the first project is in [PLAN.md](PLAN.md).

## Installation

Requires Python 3.11 or newer (developed on 3.12).

```bash
git clone https://github.com/FranzTriebe/quant_finance.git
cd quant_finance
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

This also installs `quantlab` in editable mode, so `import quantlab` works from any notebook or script.

## Usage

Run the tests:

```bash
pytest -q
```

Open a notebook in VS Code (select the `.venv` interpreter) or in Jupyter Lab:

```bash
jupyter lab
```

## Projects

| Project | Status | Question |
| --- | --- | --- |
| [P1: Backtest referee](PLAN.md) | in progress (Phase 1 of 6 done) | I tried N variants of a strategy and kept the best one. How much of its backtest should I believe? |
| P2: Regime switching with statistical jump models | planned | Does cutting exposure in detected bear regimes help on the S&P 500, DAX and SMI? |
| P3: Trend following and CTA replication | planned | How well do trend factors at different speeds explain a managed futures fund? |
| P4: Swiss franc hedging | planned | How much currency risk should a CHF investor hedge? |
| P5: Technology momentum from patent data | planned | Do technologically linked firms predict each other's returns? |

Earlier exercises, kept as standalone notebooks:

* [momentum_strategy](projects/momentum_strategy/): 9/21 day moving average crossover on gold (GLD) against buy and hold.
* [black_scholes](projects/black_scholes/): European option pricing with Black Scholes (unfinished).

## Project structure

```text
├── quantlab/          # the engine: data, risk, backtest, stats, validation, plotting
├── projects/          # one folder per project
├── tests/             # pytest suite, runs offline on simulated data
├── data/              # cached downloads (not committed)
├── output/            # figures, reports, trial ledger (not committed)
├── .claude/skills/    # house rules for commits, notebooks and READMEs
├── CLAUDE.md          # working rules for Claude Code in this repo
└── PLAN.md            # build plan for Project 1
```

## Contributing

This is a personal research repo. Commits follow Conventional Commits.
