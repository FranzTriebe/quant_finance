"""Performance statistics: Sharpe ratio, t statistics and a summary table.

Inputs are daily excess returns (return minus the risk free rate). Annualizing uses 252
trading days and is for display only; the referee formulas in ``validation`` work with
daily numbers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as sps

from quantlab.risk import max_drawdown

PERIODS = 252


def sharpe(x: pd.Series | pd.DataFrame, periods: int = PERIODS,
           annualize: bool = True) -> float | pd.Series:
    """Sharpe ratio: mean excess return divided by its standard deviation (ddof 1).

    Annualized by multiplying with sqrt(periods): the mean scales with time, the
    standard deviation with the square root of time.
    """
    sr = x.mean() / x.std(ddof=1)
    return sr * np.sqrt(periods) if annualize else sr


def tstat_mean(x: pd.Series, nw_lags: int | None = None) -> float:
    """t statistic of the mean excess return (is the average return different from 0?).

    With ``nw_lags=None`` this is the textbook iid t statistic, mean / (s / sqrt(T)).
    With ``nw_lags`` set, the standard error is Newey West (HAC), which stays valid when
    returns are autocorrelated or their volatility changes over time. It comes from an
    OLS regression of x on a constant, exactly as in econometrics class.
    """
    x = pd.Series(x).dropna()
    if nw_lags is None:
        return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))
    import statsmodels.api as sm

    fit = sm.OLS(x.to_numpy(), np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": nw_lags})
    return float(fit.tvalues[0])


def summary(x: pd.Series, total: pd.Series | None = None,
            position: pd.Series | None = None) -> pd.Series:
    """One column of key statistics for a strategy, ready to put next to others.

    Parameters
    ----------
    x : daily excess returns.
    total : daily total returns (excess plus cash interest). Used for the geometric
        return and drawdowns, because that is what an investor actually experiences.
        Without it, those figures are computed from ``x``.
    position : daily positions, for time in market, hit rate and turnover.

    Notes
    -----
    * Sortino uses the downside deviation sqrt(mean(min(x, 0)^2)) with target 0.
    * Calmar is the annualized geometric total return divided by the absolute max
      drawdown.
    * Skewness and kurtosis are the plain moment estimates; kurtosis is Pearson's, so a
      normal distribution has 3.
    * Hit rate counts only days in the market (position not 0), so a strategy that is
      often flat is not punished for its flat days.
    """
    x = x.dropna()
    wealth_path = (total if total is not None else x).loc[x.index]
    n = len(x)
    ann_mean = x.mean() * PERIODS
    ann_vol = x.std(ddof=1) * np.sqrt(PERIODS)
    geo = (1 + wealth_path).prod() ** (PERIODS / n) - 1
    downside = np.sqrt((np.minimum(x, 0) ** 2).mean()) * np.sqrt(PERIODS)
    mdd = max_drawdown(wealth_path)

    if position is not None:
        pos = position.loc[x.index]
        in_market = pos != 0
        hit = (x[in_market] > 0).mean() if in_market.any() else np.nan
        time_in = in_market.mean()
        prior = position.shift(1).loc[x.index].fillna(0)
        turnover = (pos - prior).abs().sum() / n * PERIODS
    else:
        hit, time_in, turnover = (x[x != 0] > 0).mean(), np.nan, np.nan

    return pd.Series({
        "ann_mean_excess": ann_mean,
        "ann_geo_total": geo,
        "ann_vol": ann_vol,
        "sharpe": ann_mean / ann_vol,
        "sortino": ann_mean / downside,
        "max_drawdown": mdd,
        "calmar": geo / abs(mdd),
        "skew": sps.skew(x),
        "kurtosis": sps.kurtosis(x, fisher=False),
        "hit_rate": hit,
        "time_in_market": time_in,
        "turnover_per_year": turnover,
    }, name=x.name)
