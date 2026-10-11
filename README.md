# Quant Finance

A collection of quantitative finance projects as Jupyter notebooks. Each project lives in its own folder, and every notebook is self-contained: no shared helper modules, so each one runs top to bottom on its own.

## Projects

| Project | Description |
| --- | --- |
| [momentum_strategy](momentum_strategy/) | Moving-average crossover (9/21-day) strategy on gold (GLD), compared against buy & hold |
| [black_scholes](black_scholes/) | European option pricing with the Black-Scholes model *(work in progress)* |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running a notebook

```bash
jupyter lab
```

Then open a project's `.ipynb` file and run all cells. You can also open the notebooks directly in PyCharm or VS Code using the `.venv` interpreter.

## Adding a new project

1. Create a folder with a `snake_case` name, e.g. `pairs_trading/`.
2. Add a notebook inside it, named after the folder (`pairs_trading/pairs_trading.ipynb`). Keep all code in the notebook itself; don't import from other projects.
3. Add a short `README.md` in the folder covering what it does.
4. Add any new dependencies to the root `requirements.txt`.
5. Add a row to the **Projects** table above.

## Repository structure

```
quant_finance/
├── README.md
├── requirements.txt              # shared dependencies for all projects
├── momentum_strategy/
│   ├── README.md
│   └── momentum_strategy.ipynb
└── black_scholes/
    ├── README.md
    └── black_scholes_model.ipynb
```
