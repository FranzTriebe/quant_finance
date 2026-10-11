"""quantlab: a small research engine for backtesting and validating trading strategies.

Modules
-------
data        loading and caching prices, risk free rates, simulated returns (the only module with file I/O)
risk        volatility estimates, drawdowns, monthly aggregation
backtest    turns target weights into strategy returns; the only place where weights are lagged
stats       Sharpe ratio, t statistics, summary tables
validation  the referee: PSR, deflated Sharpe, haircut Sharpe, PBO via CSCV, trial ledger
plotting    house style and colour palette for figures
"""
