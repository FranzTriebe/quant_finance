"""One call from a set of trial weights to a referee verdict, with honest trial counting.

``run_referee`` is what "run any new idea through the referee in one command" means in
PLAN.md: backtest every trial on a common sample, pick the best one the way a naive
researcher would, record the run in the trial ledger, and judge the winner against
everything ever tried on the same data.
"""

from __future__ import annotations

import pandas as pd

from quantlab import backtest, validation


def make_data_id(label: str, returns: pd.Series) -> str:
    """Ledger key for a data set: label plus first and last date of the loaded returns.

    It uses the loaded data, not a strategy's sample after warmup, so trials with
    different warmups on the same data share one count.
    """
    return f"{label} {returns.index[0]:%Y-%m-%d} {returns.index[-1]:%Y-%m-%d}"


def run_referee(trials: dict[str, pd.Series], returns: pd.Series, *, project: str,
                data_label: str, rf: pd.Series | None = None, lag: int = 1,
                cost_bps: float = 5.0, n_blocks: int = 16, alpha: float = 0.05,
                record: bool = True, ledger_path: str = "output/trial_ledger.csv") -> dict:
    """Backtest all trials, select the best by Sharpe ratio, and run the referee.

    The run is written to the ledger first (``record=True``), so the deflated Sharpe
    ratio counts every distinct trial ever run by this project on this data, including
    the ones in this run.

    Returns
    -------
    dict with ``excess`` (T x N daily excess returns), ``results`` (full ``run`` output
    per trial), ``selected`` (the naive winner), ``data_id``, ``n_ledger`` and ``report``
    (the ``validation.referee_report`` dict).
    """
    results = backtest.run_all(trials, returns, lag=lag, cost_bps=cost_bps, rf=rf)
    excess = pd.DataFrame({k: r["excess"] for k, r in results.items()})
    sharpes = excess.mean() / excess.std(ddof=1) * (252 ** 0.5)
    selected = sharpes.idxmax()
    data_id = make_data_id(data_label, returns)
    if record:
        validation.ledger_append(project, data_id, sharpes.to_frame("sharpe"), ledger_path)
    n_ledger = validation.ledger_count(project, data_id, ledger_path)
    report = validation.referee_report(excess, selected, n_blocks=n_blocks, alpha=alpha,
                                       n_ledger=n_ledger)
    return {"excess": excess, "results": results, "selected": selected, "data_id": data_id,
            "n_ledger": n_ledger, "report": report, "lag": lag, "cost_bps": cost_bps}
