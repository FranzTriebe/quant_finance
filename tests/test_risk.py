"""Tests for quantlab.risk: volatility, drawdowns and monthly compounding."""

import numpy as np
import pandas as pd
import pytest

from quantlab import data, risk


def _series(values, start="2020-01-01"):
    return pd.Series(values, index=pd.bdate_range(start, periods=len(values)), dtype=float)


def test_drawdown_counts_first_day_loss_and_recovers():
    r = _series([-0.10, 0.0, 0.20, -0.05])
    dd = risk.drawdown(r)
    assert dd.iloc[0] == pytest.approx(-0.10)
    assert dd.iloc[2] == pytest.approx(0.0)  # 0.9 * 1.2 = 1.08, a new peak
    assert dd.iloc[3] == pytest.approx(-0.05)


def test_max_drawdown_of_known_path():
    r = _series([0.10, -0.50, 0.20])  # wealth 1.1, 0.55, 0.66
    assert risk.max_drawdown(r) == pytest.approx(-0.50)


def test_to_monthly_compounds_within_month():
    idx = pd.to_datetime(["2020-01-30", "2020-01-31", "2020-02-03"])
    r = pd.Series([0.10, 0.10, -0.05], index=idx)
    m = risk.to_monthly(r)
    assert m.iloc[0] == pytest.approx(1.1 * 1.1 - 1)
    assert m.iloc[1] == pytest.approx(-0.05)


def test_vol_estimates_match_true_vol():
    r = data.simulate_returns(20_000, ann_vol=0.16, seed=3)["s0"]
    assert risk.rolling_vol(r).mean() == pytest.approx(0.16, rel=0.03)
    assert risk.ewma_vol(r).mean() == pytest.approx(0.16, rel=0.05)


@pytest.mark.parametrize("func", [risk.ewma_vol, risk.rolling_vol])
def test_vol_uses_no_future_data(func):
    r = data.simulate_returns(500, seed=4)["s0"]
    cut = r.index[300]
    changed = r.copy()
    changed.loc[changed.index > cut] *= 10
    np.testing.assert_allclose(func(r).loc[:cut], func(changed).loc[:cut])
