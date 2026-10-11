"""Tests for quantlab.strategies: 256 unique trials, weight bounds, and the look ahead test."""

import numpy as np
import pandas as pd
import pytest

from quantlab import data, strategies

WARMUP = 300  # longest signal: SMA(300); TSMOM(12) needs 252 days, vol targeting 20


@pytest.fixture(scope="module")
def prices() -> pd.Series:
    r = data.simulate_returns(1500, ann_sharpe=0.4, ann_vol=0.18, seed=31)["s0"]
    return 100 * (1 + r).cumprod()


@pytest.fixture(scope="module")
def trials(prices) -> dict[str, pd.Series]:
    return strategies.build_trials(prices)


def test_exactly_256_trials_with_unique_readable_ids(trials):
    assert len(trials) == 256 == len(set(trials))
    assert {"sma200_lf_full_d", "x20_150_ls_vt_w", "tsm12_ls_full_d"} <= set(trials)
    assert all(w.name == k for k, w in trials.items())


def test_no_nan_after_warmup_and_weights_within_bounds(trials, prices):
    after = prices.index[WARMUP + 5:]  # +5: a weekly trial waits for the first week end
    for trial_id, w in trials.items():
        assert not w.loc[after].isna().any(), trial_id
        assert w.dropna().between(-1, 1).all(), trial_id


def test_variants_take_the_expected_values(trials):
    lf = trials["sma200_lf_full_d"].dropna()
    ls = trials["sma200_ls_full_d"].dropna()
    assert set(lf.unique()) <= {0.0, 1.0}
    assert set(ls.unique()) <= {-1.0, 1.0}
    pd.testing.assert_series_equal(ls, 2 * lf - 1, check_names=False)
    vt = trials["sma200_lf_vt_d"].dropna()
    assert (vt <= lf.loc[vt.index]).all() and (vt < 1).any()


def test_weekly_weights_only_change_on_the_last_day_of_a_week(trials):
    w = trials["x10_50_ls_full_w"].dropna()
    changes = w.index[w.ne(w.shift(1))][1:]
    assert len(changes) > 10
    next_day = w.index[w.index.get_indexer(changes) + 1]
    # the next trading day after every change is already in a new week
    assert (changes.to_period("W-FRI") != next_day.to_period("W-FRI")).all()


@pytest.mark.parametrize("cut", [400, 777, 1200])
def test_no_look_ahead(prices, trials, cut):
    """Change every price after day d: no weight up to and including d may change."""
    d = prices.index[cut]
    rng = np.random.default_rng(cut)
    changed = prices.copy()
    after = changed.index > d
    # a crash to half the level plus noise: any rule peeking past d would see it
    changed.loc[after] *= 0.5 * np.exp(rng.normal(0, 0.05, after.sum()).cumsum())
    rebuilt = strategies.build_trials(changed)
    for trial_id, w in trials.items():
        pd.testing.assert_series_equal(w.loc[:d], rebuilt[trial_id].loc[:d], obj=trial_id)
    # the perturbation is strong enough to matter afterwards
    assert any(not w.loc[d:].equals(rebuilt[k].loc[d:]) for k, w in trials.items())


def test_bad_variant_names_raise(prices):
    bull = strategies.price_above_sma(prices, 50)
    for kwargs in ({"direction": "x"}, {"sizing": "x"}, {"rebalance": "x"}):
        args = {"direction": "lf", "sizing": "full", "rebalance": "d", **kwargs}
        with pytest.raises(ValueError):
            strategies.apply_variant(bull, **args)
