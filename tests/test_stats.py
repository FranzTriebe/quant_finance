"""Tests for quantlab.stats: Sharpe ratio, t statistics and the summary table."""

import numpy as np
import pandas as pd
import pytest

from quantlab import data, stats


@pytest.fixture
def x() -> pd.Series:
    return data.simulate_returns(5_000, ann_sharpe=0.8, seed=21)["s0"]


def test_sharpe_annualizes_with_sqrt_252(x):
    daily = stats.sharpe(x, annualize=False)
    assert daily == pytest.approx(x.mean() / x.std())
    assert stats.sharpe(x) == pytest.approx(daily * np.sqrt(252))


def test_iid_tstat_equals_daily_sharpe_times_sqrt_t(x):
    assert stats.tstat_mean(x) == pytest.approx(stats.sharpe(x, annualize=False) * np.sqrt(len(x)))


def test_newey_west_close_to_iid_for_iid_returns(x):
    assert stats.tstat_mean(x, nw_lags=5) == pytest.approx(stats.tstat_mean(x), rel=0.1)


def test_newey_west_smaller_for_positively_autocorrelated_returns():
    e = data.simulate_returns(5_000, seed=22)["s0"].to_numpy()
    ar = np.empty_like(e)
    ar[0] = e[0]
    for t in range(1, len(e)):
        ar[t] = 0.5 * ar[t - 1] + e[t]
    x = pd.Series(ar + 0.0005)
    assert abs(stats.tstat_mean(x, nw_lags=10)) < abs(stats.tstat_mean(x))


def test_summary_fields_and_values(x):
    position = pd.Series(1.0, index=x.index)
    s = stats.summary(x, total=x, position=position)
    assert s["sharpe"] == pytest.approx(stats.sharpe(x))
    assert s["ann_vol"] == pytest.approx(x.std() * np.sqrt(252))
    assert s["kurtosis"] == pytest.approx(3, abs=0.3)
    assert s["time_in_market"] == 1.0
    assert s["turnover_per_year"] == pytest.approx(252 / len(x))  # one entry trade
    assert s["max_drawdown"] < 0
