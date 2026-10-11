"""Tests for quantlab.validation, the referee. Thresholds were checked by simulation in PLAN.md."""

import numpy as np
import pandas as pd
import pytest

from quantlab import data, validation as v


def test_sr_std_error_matches_normal_formula():
    sr, n = 0.05, 1000
    assert v.sr_std_error(sr, n) == pytest.approx(np.sqrt((1 + sr ** 2 / 2) / (n - 1)))


def test_fat_tails_and_negative_skew_widen_the_standard_error():
    base = v.sr_std_error(0.05, 1000)
    assert v.sr_std_error(0.05, 1000, kurt=10) > base
    assert v.sr_std_error(0.05, 1000, skew=-1) > base


def test_psr_against_own_sharpe_is_one_half():
    x = data.simulate_returns(2000, ann_sharpe=1.0, seed=1)["s0"]
    assert v.psr(x, sr_star=v.moments(x)["sr"]) == pytest.approx(0.5)


def test_expected_max_sr_matches_simulation():
    n_obs, n_trials = 1000, 100
    sim = v.simulate_max_sr(n_obs, [n_trials], n_sims=1000, seed=2)[n_trials].mean()
    formula = v.expected_max_sr(n_trials, 1 / (n_obs - 1))
    assert formula == pytest.approx(sim, rel=0.05)


def test_expected_max_sr_is_one_at_seven_trials_two_years():
    annualized = v.expected_max_sr(7, 1 / 503) * np.sqrt(252)
    assert annualized == pytest.approx(0.98, abs=0.02)


def test_dsr_is_below_psr_when_there_was_a_search():
    x = data.simulate_returns(2520, ann_sharpe=1.0, seed=3)["s0"]
    assert v.dsr(x, n_trials=100, var_sr=1 / 2519) < v.psr(x)
    assert v.dsr(x, n_trials=1, var_sr=1 / 2519) == pytest.approx(v.psr(x))


def _noise_pbo(seed):
    trials = data.simulate_returns(2520, n_assets=100, seed=seed)
    return v.pbo_cscv(trials, n_blocks=16)["pbo"]


def test_pbo_of_pure_noise_is_about_one_half_on_average():
    mean_pbo = np.mean([_noise_pbo(seed) for seed in range(20)])
    assert 0.42 <= mean_pbo <= 0.58


def test_pbo_is_low_when_one_strategy_has_a_real_edge():
    sharpes = np.zeros(100)
    sharpes[0] = 2.0
    trials = data.simulate_returns(2520, n_assets=100, ann_sharpe=sharpes, seed=4)
    assert v.pbo_cscv(trials, n_blocks=16)["pbo"] < 0.10


def test_pbo_rejects_odd_block_count():
    with pytest.raises(ValueError):
        v.pbo_cscv(data.simulate_returns(100, n_assets=3), n_blocks=5)


def test_haircut_is_zero_for_one_trial_and_grows_with_n():
    sharpes = np.zeros(200)
    sharpes[0] = 1.5
    trials = data.simulate_returns(2520, n_assets=200, ann_sharpe=sharpes, seed=5)
    one = v.haircut_sharpe(trials[["s0"]], "s0").loc["bonferroni", "haircut"]
    assert one == pytest.approx(0.0, abs=1e-9)
    cuts = [v.haircut_sharpe(trials.iloc[:, :n], "s0").loc["bonferroni", "haircut"] for n in (10, 50, 200)]
    assert cuts == sorted(cuts) and cuts[0] > 0


def test_min_trl_falls_as_sharpe_rises_and_needs_an_edge():
    assert v.min_trl(0.10) < v.min_trl(0.05) < v.min_trl(0.02)
    with pytest.raises(ValueError, match="only defined"):
        v.min_trl(0.03, sr_star=0.05)


def test_effective_trials_for_identical_and_independent_trials():
    x = data.simulate_returns(3000, n_assets=10, seed=6)
    same = pd.DataFrame({f"c{i}": x["s0"] for i in range(10)})
    assert v.n_eff_avgcorr(same) == pytest.approx(1.0)
    assert v.n_eff_eigen(same) == pytest.approx(1.0)
    assert v.n_eff_avgcorr(x) == pytest.approx(10, rel=0.05)
    assert v.n_eff_eigen(x) == pytest.approx(10, rel=0.1)


def test_ledger_counts_distinct_trials_across_sessions(tmp_path):
    path = str(tmp_path / "ledger.csv")
    stats_a = pd.DataFrame({"sharpe": [0.5, 0.7]}, index=["a", "b"])
    stats_b = pd.DataFrame({"sharpe": [0.7, 0.1]}, index=["b", "c"])
    assert v.ledger_count("p01", "SPY", path) == 0
    v.ledger_append("p01", "SPY", stats_a, path)
    v.ledger_append("p01", "SPY", stats_b, path)
    v.ledger_append("p01", "DAX", stats_b, path)
    assert v.ledger_count("p01", "SPY", path) == 3
    assert len(pd.read_csv(path)) == 6  # every run is kept, nothing is overwritten


def test_referee_report_and_markdown():
    sharpes = np.zeros(20)
    sharpes[0] = 3.0
    trials = data.simulate_returns(2520, n_assets=20, ann_sharpe=sharpes, seed=7)
    rep = v.referee_report(trials, "s0", n_ledger=50)
    assert rep["n_used"] == 50
    assert rep["verdict"] == "Strong"
    md = v.report_to_markdown(rep)
    assert "Verdict: Strong" in md and "PBO" in md

    noise = data.simulate_returns(2520, n_assets=20, seed=8)
    best = (noise.mean() / noise.std()).idxmax()
    assert v.referee_report(noise, best)["verdict"] == "Not distinguishable from luck"
