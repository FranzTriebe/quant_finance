"""Trend timing rules on a single index and the 256 trial family of Project 1.

Every rule takes a price series P (a total return index works best) and returns target
weights as of the close of day t, computed only from prices up to and including day t.
Nothing in this module shifts weights; ``backtest.run`` applies the lag.

The family (PLAN.md section 7.2) crosses 32 signals with 8 variants:

* signals: price above SMA(L) (7), SMA(fast) above SMA(slow) (19), time series
  momentum over k months (6)
* direction: long/flat (``lf``, weight 1 or 0) or long/short (``ls``, +1 or -1)
* sizing: ``full`` (|w| = 1) or volatility targeted (``vt``, scaled down to 15% EWMA vol)
* rebalancing: daily (``d``) or weekly (``w``, the weight from the last trading day of a
  week is held through the next week)

Trial ids read like ``sma200_lf_full_d`` or ``x20_150_ls_vt_w``.
"""

from __future__ import annotations

import pandas as pd

from quantlab.risk import ewma_vol

SMA_LENGTHS = (20, 50, 100, 150, 200, 250, 300)
CROSS_FAST = (5, 10, 20, 50)
CROSS_SLOW = (50, 100, 150, 200, 250)
TSMOM_MONTHS = (1, 2, 3, 6, 9, 12)
DAYS_PER_MONTH = 21
VOL_TARGET = 0.15
VOL_HALFLIFE = 20


def sma(prices: pd.Series, length: int) -> pd.Series:
    """Simple moving average of the last ``length`` closes, including today's."""
    return prices.rolling(length).mean()


def price_above_sma(prices: pd.Series, length: int) -> pd.Series:
    """Bullish (1.0) when today's close is above its SMA(length), else 0.0; NaN in warmup."""
    avg = sma(prices, length)
    return (prices > avg).astype(float).where(avg.notna())


def sma_cross(prices: pd.Series, fast: int, slow: int) -> pd.Series:
    """Bullish (1.0) when SMA(fast) is above SMA(slow), else 0.0; NaN in warmup."""
    fast_avg, slow_avg = sma(prices, fast), sma(prices, slow)
    return (fast_avg > slow_avg).astype(float).where(slow_avg.notna())


def tsmom(prices: pd.Series, months: int) -> pd.Series:
    """Time series momentum: bullish (1.0) when P_t / P_{t-21k} - 1 is positive."""
    past = prices.shift(DAYS_PER_MONTH * months)
    return (prices > past).astype(float).where(past.notna())


def signals(prices: pd.Series) -> dict[str, pd.Series]:
    """The 32 bullish/bearish signals, keyed by their short name."""
    out = {f"sma{n}": price_above_sma(prices, n) for n in SMA_LENGTHS}
    out |= {f"x{f}_{s}": sma_cross(prices, f, s) for f in CROSS_FAST for s in CROSS_SLOW if f < s}
    out |= {f"tsm{k}": tsmom(prices, k) for k in TSMOM_MONTHS}
    return out


def apply_variant(bullish: pd.Series, direction: str, sizing: str, rebalance: str,
                  vol: pd.Series | None = None) -> pd.Series:
    """Turn a bullish indicator (1, 0 or NaN) into target weights.

    Parameters
    ----------
    bullish : 1.0 when the signal is bullish at the close, 0.0 when not, NaN in warmup.
    direction : ``"lf"`` holds 1 or 0, ``"ls"`` holds +1 or -1.
    sizing : ``"full"`` keeps |w| = 1; ``"vt"`` multiplies by min(1, 15% / EWMA vol), so
        the position shrinks when the market is volatile and never levers up.
    rebalance : ``"d"`` daily; ``"w"`` holds the weight set on the last trading day of
        each week (Friday, or Thursday before a Friday holiday) through the next week.
    vol : annualized volatility as of each close, needed for ``"vt"``.
    """
    if direction == "lf":
        w = bullish
    elif direction == "ls":
        w = 2 * bullish - 1
    else:
        raise ValueError(f"direction must be 'lf' or 'ls', got {direction!r}")
    if sizing == "vt":
        if vol is None:
            raise ValueError("volatility targeting needs vol")
        w = w * (VOL_TARGET / vol).clip(upper=1.0)
    elif sizing != "full":
        raise ValueError(f"sizing must be 'full' or 'vt', got {sizing!r}")
    if rebalance == "w":
        weeks = pd.Series(w.index.to_period("W-FRI"), index=w.index)
        last_day_of_week = weeks != weeks.shift(-1)
        w = w.where(last_day_of_week).ffill().where(w.notna())
    elif rebalance != "d":
        raise ValueError(f"rebalance must be 'd' or 'w', got {rebalance!r}")
    return w


def build_trials(prices: pd.Series) -> dict[str, pd.Series]:
    """All 256 trials (32 signals x 2 directions x 2 sizings x 2 rebalancing rules).

    Buy and hold is the benchmark, not a trial.
    """
    returns = prices / prices.shift(1) - 1
    vol = ewma_vol(returns, halflife=VOL_HALFLIFE)
    trials = {}
    for name, bullish in signals(prices).items():
        for direction in ("lf", "ls"):
            for sizing in ("full", "vt"):
                for rebalance in ("d", "w"):
                    trial_id = f"{name}_{direction}_{sizing}_{rebalance}"
                    w = apply_variant(bullish, direction, sizing, rebalance, vol)
                    trials[trial_id] = w.rename(trial_id)
    return trials
