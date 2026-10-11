"""Tests for quantlab.pipeline and validation.holdout: one call to a verdict, honest counting."""

import numpy as np
import pandas as pd

from quantlab import data, pipeline, strategies, validation


def _setup():
    r = data.simulate_returns(1500, ann_sharpe=0.3, ann_vol=0.18, seed=41)["s0"]
    trials = strategies.build_trials(100 * (1 + r).cumprod())
    return r, {k: trials[k] for k in list(trials)[:16]}


def test_run_referee_counts_new_trials_across_runs(tmp_path):
    r, trials = _setup()
    path = str(tmp_path / "ledger.csv")
    first = pipeline.run_referee(trials, r, project="p", data_label="SIM", ledger_path=path)
    assert first["n_ledger"] == 16 and first["report"]["n_used"] == 16
    assert first["selected"] == first["excess"].pipe(lambda x: x.mean() / x.std()).idxmax()

    extra = {"my_rule": strategies.price_above_sma(100 * (1 + r).cumprod(), 333)}
    second = pipeline.run_referee({**trials, **extra}, r, project="p", data_label="SIM", ledger_path=path)
    assert second["n_ledger"] == 17  # the longer warmup does not open a new ledger bucket
    assert second["data_id"] == first["data_id"]


def test_record_false_leaves_the_ledger_alone(tmp_path):
    r, trials = _setup()
    path = tmp_path / "ledger.csv"
    pipeline.run_referee(trials, r, project="p", data_label="SIM", ledger_path=str(path), record=False)
    assert not path.exists()


def test_holdout_selects_on_train_part_only():
    sharpes = np.zeros(10)
    sharpes[3] = 3.0
    trials = data.simulate_returns(3000, n_assets=10, ann_sharpe=sharpes, seed=42)
    bench = pd.Series(trials.mean(axis=1), index=trials.index)
    out = validation.holdout(trials, bench)
    assert out["selected"] == "s3" and out["test_rank"] == 1
    assert out["split_date"] == trials.index[2000]
