"""Tests for quantlab.data: offline parsing, return math and the simulator."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats as sps

from quantlab import data

FRENCH_SAMPLE = """This file was created by using the 202608 CRSP database.
The Tbill return is the simple daily rate.

,Mkt-RF,SMB,HML,RF
19260701,    0.09,   -0.23,   -0.28,    0.01
19260702,    0.45,   -0.33,   -0.08,    0.02

Copyright 2026 Eugene F. Fama and Kenneth R. French
"""


def test_parse_french_daily_reads_rows_and_stops_at_footer():
    df = data.parse_french_daily(FRENCH_SAMPLE)
    assert list(df.columns) == ["Mkt-RF", "SMB", "HML", "RF"]
    assert list(df.index) == [pd.Timestamp("1926-07-01"), pd.Timestamp("1926-07-02")]
    assert df.loc["1926-07-02", "RF"] == pytest.approx(0.02)


def test_prices_to_returns():
    prices = pd.Series([100.0, 110.0, 99.0], index=pd.bdate_range("2020-01-01", periods=3))
    r = data.prices_to_returns(prices)
    assert r.tolist() == pytest.approx([0.10, -0.10])
    assert r.index[0] == prices.index[1]


def test_load_csv_prices(tmp_path):
    path = tmp_path / "prices.csv"
    path.write_text("Day,Close,Other\n2020-01-03,2,y\n2020-01-02,1,x\n")
    prices = data.load_csv_prices(str(path), "Day", "Close")
    assert prices.index.is_monotonic_increasing
    assert prices.tolist() == [1.0, 2.0]


def test_simulate_returns_is_reproducible():
    a = data.simulate_returns(100, n_assets=3, seed=7)
    b = data.simulate_returns(100, n_assets=3, seed=7)
    pd.testing.assert_frame_equal(a, b)
    assert a.shape == (100, 3)
    assert isinstance(a.index, pd.DatetimeIndex)


@pytest.mark.parametrize("dist", ["normal", "t"])
def test_simulate_returns_hits_target_vol_and_sharpe(dist):
    x = data.simulate_returns(200_000, ann_sharpe=1.0, ann_vol=0.20, dist=dist, seed=1)["s0"]
    assert x.std() * np.sqrt(252) == pytest.approx(0.20, rel=0.02)
    assert x.mean() / x.std() * np.sqrt(252) == pytest.approx(1.0, abs=0.08)


def test_simulate_t_has_fat_tails():
    x = data.simulate_returns(200_000, dist="t", df=5, seed=2)["s0"]
    assert sps.kurtosis(x, fisher=False) > 5  # normal is 3, t(5) is 9 in theory
