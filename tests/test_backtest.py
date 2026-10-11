"""Tests for quantlab.backtest: lag timing, costs, cash earns rf, common sample."""

import numpy as np
import pandas as pd
import pytest

from quantlab import backtest, data


@pytest.fixture
def returns() -> pd.Series:
    return data.simulate_returns(300, ann_sharpe=0.5, seed=11)["s0"]


@pytest.mark.parametrize("lag", [1, 2])
def test_weight_on_day_d_only_earns_return_of_day_d_plus_lag(returns, lag):
    d = 100
    weights = pd.Series(0.0, index=returns.index)
    weights.iloc[d] = 1.0
    res = backtest.run(weights, returns, lag=lag, cost_bps=0)
    earning = res["excess"].fillna(0) != 0
    assert earning.sum() == 1
    assert res["excess"].iloc[d + lag] == pytest.approx(returns.iloc[d + lag])


def test_cost_equals_turnover_times_bps(returns):
    rng = np.random.default_rng(0)
    weights = pd.Series(rng.uniform(-1, 1, len(returns)), index=returns.index)
    res = backtest.run(weights, returns, cost_bps=7.5).dropna()
    np.testing.assert_allclose(res["cost"], res["turnover"] * 7.5 / 10_000)
    position = weights.shift(1)
    expected_turnover = (position - position.shift(1).fillna(0)).abs().dropna()
    np.testing.assert_allclose(res["turnover"], expected_turnover)


def test_entering_the_market_costs_like_any_trade(returns):
    res = backtest.run(pd.Series(1.0, index=returns.index), returns, cost_bps=5).dropna()
    assert res["turnover"].iloc[0] == 1.0
    assert (res["turnover"].iloc[1:] == 0).all()


def test_zero_position_earns_rf_in_total_and_zero_excess(returns):
    rf = pd.Series(0.0001, index=returns.index)
    res = backtest.run(pd.Series(0.0, index=returns.index), returns, rf=rf).dropna()
    assert (res["excess"] == 0).all()
    np.testing.assert_allclose(res["total"], rf.loc[res.index])


def test_short_position_earns_rf_minus_excess_return(returns):
    rf = pd.Series(0.0001, index=returns.index)
    res = backtest.run(pd.Series(-1.0, index=returns.index), returns, rf=rf, cost_bps=0).dropna()
    expected = rf - (returns - rf)
    np.testing.assert_allclose(res["total"], expected.loc[res.index])


def test_missing_rf_raises(returns):
    rf = pd.Series(0.0001, index=returns.index[:-5])
    with pytest.raises(ValueError, match="rf has no value"):
        backtest.run(pd.Series(1.0, index=returns.index), returns, rf=rf)


def test_lag_zero_is_refused(returns):
    with pytest.raises(ValueError):
        backtest.run(pd.Series(1.0, index=returns.index), returns, lag=0)


def test_multi_asset_weights(returns):
    r2 = pd.DataFrame({"a": returns, "b": -returns})
    w2 = pd.DataFrame({"a": 0.5, "b": 0.5}, index=returns.index)
    res = backtest.run(w2, r2, cost_bps=0).dropna()
    np.testing.assert_allclose(res["excess"], 0.0, atol=1e-15)  # the two legs cancel
    assert (res["position"] == 1.0).all()


def test_run_many_returns_common_sample_without_nan(returns):
    prices = (1 + returns).cumprod()
    trials = {f"sma{n}": (prices > prices.rolling(n).mean()).astype(float).where(
        prices.rolling(n).mean().notna()) for n in (5, 20, 50)}
    out = backtest.run_many(trials, returns)
    assert list(out.columns) == ["sma5", "sma20", "sma50"]
    assert not out.isna().any().any()
    slowest_first_weight = trials["sma50"].first_valid_index()
    assert out.index[0] == returns.index[returns.index.get_loc(slowest_first_weight) + 1]

    full = backtest.run_all(trials, returns)
    assert all(r.index.equals(out.index) for r in full.values())
    pd.testing.assert_series_equal(full["sma20"]["excess"], out["sma20"], check_names=False)
