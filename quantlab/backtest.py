"""Backtest engine: turns target weights into daily strategy returns.

Strategies hand in target weights as of the close of day t, computed from data up to and
including day t. ``run`` lags them by ``lag`` days (default 1) before applying them to
returns. This module is the only place in the repo that shifts weights, so look ahead
bias can only enter in one place, and that place is tested.
"""

from __future__ import annotations

import pandas as pd

Weights = pd.Series | pd.DataFrame


def run(weights: Weights, returns: Weights, lag: int = 1, cost_bps: float = 5.0,
        rf: pd.Series | None = None) -> pd.DataFrame:
    """Backtest one strategy and return its daily position, costs and returns.

    For each day t:

    * ``position_t = weights_{t - lag}``: a weight decided at Monday's close is held
      during Tuesday (lag 1) and earns Tuesday's return.
    * ``turnover_t = sum |position_t - position_{t-1}|``: how much was traded. The day
      before the first position counts as cash, so entering the market costs too.
    * ``cost_t = turnover_t * cost_bps / 10,000``.
    * ``excess_t = sum position_t * (r_t - rf_t) - cost_t``: return above cash.
    * ``total_t = excess_t + rf_t``: what the account earns, cash interest included.

    A short position of -1 therefore earns ``rf - (r - rf)``, which is how a short
    futures position behaves. Days before the strategy has a position (warmup) are NaN.

    Parameters
    ----------
    weights : target weights indexed by date; a Series for one asset or a DataFrame
        with one column per asset. Must not be lagged already.
    returns : daily simple returns with the same shape (Series or DataFrame).
    lag : trading days between the decision and the first day it earns a return.
    cost_bps : cost in basis points per unit of one way turnover.
    rf : daily risk free rate in decimals; ``None`` means 0. It must have a value on
        every return date (align and fill it yourself, so that choice stays visible).

    Returns
    -------
    DataFrame with columns position, turnover, cost, excess, total. For several assets,
    position is the net exposure (sum of the asset positions).
    """
    if lag < 1:
        raise ValueError("lag must be at least 1; lag 0 would trade on the same close it uses")
    single = isinstance(returns, pd.Series)
    r = returns.to_frame() if single else returns
    w = weights.to_frame(r.columns[0]) if isinstance(weights, pd.Series) else weights
    if list(w.columns) != list(r.columns):
        raise ValueError("weights and returns must cover the same assets")
    rf_t = _align_rf(rf, r.index)

    position = w.reindex(r.index).shift(lag)
    has_position = position.notna().all(axis=1)
    previous = position.shift(1).fillna(0.0)
    turnover = (position - previous).abs().sum(axis=1).where(has_position)
    cost = turnover * cost_bps / 10_000
    gross = position.mul(r.sub(rf_t, axis=0)).sum(axis=1).where(has_position)
    excess = gross - cost
    return pd.DataFrame({
        "position": position.sum(axis=1).where(has_position),
        "turnover": turnover,
        "cost": cost,
        "excess": excess,
        "total": excess + rf_t,
    })


def _align_rf(rf: pd.Series | None, index: pd.DatetimeIndex) -> pd.Series:
    if rf is None:
        return pd.Series(0.0, index=index)
    aligned = rf.reindex(index)
    if aligned.isna().any():
        first = aligned.index[aligned.isna()][0].date()
        raise ValueError(f"rf has no value on {first}; reindex and fill it before calling run")
    return aligned


def run_all(weights: dict[str, pd.Series], returns: pd.Series, **kw) -> dict[str, pd.DataFrame]:
    """Backtest many trials on one asset over a common sample; full ``run`` output each.

    All trials share exactly the same dates: before backtesting, every trial's weights
    are blanked until the date when the slowest trial (longest warmup) has its first
    weight. So every trial enters the market on the same day, pays the same entry cost,
    and is measured over the same sample. Extra keyword arguments go to ``run``.
    """
    if not weights:
        raise ValueError("no trials given")
    firsts = {k: w.first_valid_index() for k, w in weights.items()}
    empty = [k for k, d in firsts.items() if d is None]
    if empty:
        raise ValueError(f"trials without any weight: {empty[:5]}")
    common_start = max(firsts.values())
    results = {k: run(w.where(w.index >= common_start), returns, **kw) for k, w in weights.items()}
    common = pd.DataFrame({k: r["excess"] for k, r in results.items()}).dropna().index
    return {k: r.loc[common] for k, r in results.items()}


def run_many(weights: dict[str, pd.Series], returns: pd.Series, **kw) -> pd.DataFrame:
    """Backtest many trials on one asset and return a T x N matrix of daily excess returns.

    Same common sample rules as ``run_all``; this is the input the referee expects.
    """
    return pd.DataFrame({k: r["excess"] for k, r in run_all(weights, returns, **kw).items()})
