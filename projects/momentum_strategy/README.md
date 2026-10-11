# Momentum Strategy

A moving-average crossover strategy on gold (GLD), using 10 years of daily data from Yahoo Finance.

- **Signals:** long when the 9-day moving average is above the 21-day moving average, short when it is below. Both averages are shifted by one day so the strategy only uses information it would have had at the time.
- **Output:** a chart of the last ~252 trading days with entry markers, a chart of cumulative returns against buy & hold, and the total return of each.

## Run

Open [`momentum_strategy.ipynb`](momentum_strategy.ipynb) in Jupyter and run all cells.

Needs an internet connection to download data with `yfinance`.
