"""Risk measures: EWMA and rolling volatility, drawdowns, monthly returns.

Every estimate at day t uses returns up to and including day t only, so a strategy can
use the value at the close of day t without looking ahead.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

Returns = pd.Series | pd.DataFrame


def ewma_vol(r: Returns, halflife: int = 20, periods: int = 252) -> Returns:
    """Annualized exponentially weighted volatility, as in RiskMetrics.

    The variance estimate is an exponentially weighted average of squared returns (the
    mean is assumed to be zero, which is standard at daily frequency). A halflife of 20
    days means a return from 20 days ago gets half the weight of today's. The first
    ``halflife`` values are NaN, because the estimate is too noisy before that.
    """
    variance = (r ** 2).ewm(halflife=halflife, min_periods=halflife).mean()
    return np.sqrt(variance * periods)


def rolling_vol(r: Returns, window: int = 63, periods: int = 252) -> Returns:
    """Annualized volatility over a rolling window (63 trading days is about 3 months)."""
    return r.rolling(window).std() * np.sqrt(periods)


def drawdown(r: Returns) -> Returns:
    """Percentage drop of wealth from its running peak, at every date (0 or negative).

    Wealth starts at 1 before the first return, so a loss on the very first day already
    counts as a drawdown.
    """
    wealth = (1 + r).cumprod()
    peak = np.maximum(wealth.cummax(), 1.0)
    return wealth / peak - 1


def max_drawdown(r: Returns) -> float | pd.Series:
    """Worst peak to trough loss, for example -0.55 for a 55% fall."""
    return drawdown(r).min()


def to_monthly(r: Returns) -> Returns:
    """Monthly returns, compounded from daily returns within each calendar month."""
    return (1 + r).resample("ME").prod() - 1
