"""The referee: how much of a selected backtest should we believe?

Notation follows PLAN.md section 6.5. ``x`` is a series of daily excess returns of length
T, SR is its daily Sharpe ratio (mean / std with ddof 1, never annualized inside a
formula), skew is the sample skewness and kurt the Pearson kurtosis (normal = 3).

Tools, from simple to strict:

* ``sr_std_error`` and ``psr``: how precise is one Sharpe ratio, and how likely is the
  true one above a benchmark (Lo 2002; Bailey and Lopez de Prado 2012).
* ``expected_max_sr`` and ``dsr``: the best of N useless strategies looks good by luck
  alone; the deflated Sharpe ratio measures the winner against that luck benchmark
  (Bailey and Lopez de Prado 2014).
* ``n_eff_avgcorr`` and ``n_eff_eigen``: correlated trials are fewer independent bets.
* ``min_trl``: how long a track record must be before the Sharpe ratio is significant.
* ``haircut_sharpe``: multiple testing corrections of the p value (Harvey and Liu 2015).
* ``pbo_cscv``: how often does the in sample winner end up below the median out of
  sample (Bailey, Borwein, Lopez de Prado and Zhu 2016).
* ``ledger_append`` and ``ledger_count``: a permanent count of every trial ever run.
* ``referee_report`` and ``report_to_markdown``: everything above in one verdict.

The ledger functions write a CSV file. They live here because PLAN.md defines them as
part of the referee; they are the only file I/O outside ``quantlab.data``.
"""

from __future__ import annotations

from datetime import datetime
from itertools import combinations
from math import comb
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps
from statsmodels.stats.multitest import multipletests

from quantlab.stats import tstat_mean

EULER_GAMMA = 0.5772156649015329
PERIODS = 252
REPO_ROOT = Path(__file__).resolve().parents[1]
VERDICT_THRESHOLDS = {"strong_dsr": 0.95, "strong_pbo": 0.20, "weak_dsr": 0.80, "weak_pbo": 0.50}


# (a) and (b): precision of one Sharpe ratio --------------------------------------------

def moments(x: pd.Series) -> dict[str, float]:
    """Daily Sharpe ratio, skewness, Pearson kurtosis and length of a return series."""
    x = pd.Series(x).dropna().to_numpy(float)
    return {"sr": x.mean() / x.std(ddof=1), "skew": float(sps.skew(x)),
            "kurt": float(sps.kurtosis(x, fisher=False)), "n": len(x)}


def sr_std_error(sr: float, n: int, skew: float = 0.0, kurt: float = 3.0) -> float:
    """Standard error of a daily Sharpe ratio estimate, allowing for non normal returns.

    sqrt((1 - skew * SR + (kurt - 1) / 4 * SR^2) / (T - 1)). Negative skew and fat tails
    (kurt above 3) make the estimate less precise. For normal returns this reduces to
    sqrt((1 + SR^2 / 2) / (T - 1)), the delta method result of Lo (2002).
    """
    return float(np.sqrt(_sr_variance_factor(sr, skew, kurt) / (n - 1)))


def _sr_variance_factor(sr: float, skew: float, kurt: float) -> float:
    return 1 - skew * sr + (kurt - 1) / 4 * sr ** 2


def psr_from_moments(sr: float, n: int, skew: float, kurt: float, sr_star: float = 0.0) -> float:
    """Probabilistic Sharpe ratio from summary numbers; see ``psr``."""
    z = (sr - sr_star) * np.sqrt(n - 1) / np.sqrt(_sr_variance_factor(sr, skew, kurt))
    return float(sps.norm.cdf(z))


def psr(x: pd.Series, sr_star: float = 0.0) -> float:
    """Probability that the true daily Sharpe ratio is above ``sr_star``.

    A one sided z test of the estimated Sharpe ratio against a benchmark, with the
    standard error corrected for skewness and kurtosis. PSR(0) = 0.97 means: if the true
    Sharpe ratio were 0, an estimate this high would be unlikely (about 3%).
    """
    m = moments(x)
    return psr_from_moments(m["sr"], m["n"], m["skew"], m["kurt"], sr_star)


# (c) and (d): the best of N ------------------------------------------------------------

def expected_max_sr(n_trials: float, var_sr: float) -> float:
    """Expected maximum daily Sharpe ratio of N trials whose true Sharpe ratio is 0.

    sqrt(V) * ((1 - g) * Phi^-1(1 - 1/N) + g * Phi^-1(1 - 1/(N e))), with g the Euler
    Mascheroni constant and V the variance of the trial Sharpe ratios. This is an
    extreme value approximation to the maximum of N normal draws. N may be a non integer
    (an effective number of trials); for N at or below 1 there is no selection, so 0.
    """
    if n_trials <= 1:
        return 0.0
    q1 = sps.norm.ppf(1 - 1 / n_trials)
    q2 = sps.norm.ppf(1 - 1 / (n_trials * np.e))
    return float(np.sqrt(var_sr) * ((1 - EULER_GAMMA) * q1 + EULER_GAMMA * q2))


def dsr(x: pd.Series, n_trials: float, var_sr: float) -> float:
    """Deflated Sharpe ratio: PSR measured against the luck benchmark of N trials.

    Instead of asking "is the Sharpe ratio above 0?", it asks "is it above what the best
    of N useless strategies would show?". It uses the selected strategy's own length,
    skewness and kurtosis.
    """
    return psr(x, sr_star=expected_max_sr(n_trials, var_sr))


def simulate_max_sr(n_obs: int, n_trials: list[int], n_sims: int, dist: str = "normal",
                    df: int = 5, seed: int = 0, chunk: int = 8) -> pd.DataFrame:
    """Monte Carlo: maximum daily Sharpe ratio among N zero skill strategies.

    Each simulation draws ``max(n_trials)`` independent strategies with true Sharpe 0
    and records, for every N in ``n_trials``, the best Sharpe ratio among the first N.
    Reusing one draw for all N is faster and makes the curve over N smoother.

    Returns a DataFrame with one row per simulation and one column per N.
    """
    rng = np.random.default_rng(seed)
    n_max = max(n_trials)
    cols = np.asarray(n_trials) - 1
    out = np.empty((n_sims, len(n_trials)))
    for start in range(0, n_sims, chunk):
        k = min(chunk, n_sims - start)
        if dist == "normal":
            z = rng.standard_normal((k, n_obs, n_max), dtype=np.float32)
        elif dist == "t":
            z = rng.standard_t(df, (k, n_obs, n_max)).astype(np.float32)
        else:
            raise ValueError(f"dist must be 'normal' or 't', got {dist!r}")
        sr = z.mean(axis=1) / z.std(axis=1, ddof=1)  # k x n_max
        out[start:start + k] = np.maximum.accumulate(sr, axis=1)[:, cols]
    return pd.DataFrame(out, columns=list(n_trials))


# (e): effective number of trials -------------------------------------------------------

def n_eff_avgcorr(trials: pd.DataFrame) -> float:
    """Effective number of independent trials from the average pairwise correlation.

    rho + (1 - rho) * N: identical trials (rho = 1) count as 1, uncorrelated trials
    (rho = 0) count as N. A simple, transparent approximation.
    """
    corr = trials.corr().to_numpy()
    n = corr.shape[0]
    rho = (corr.sum() - n) / (n * (n - 1)) if n > 1 else 1.0
    return float(rho + (1 - rho) * n)


def n_eff_eigen(trials: pd.DataFrame) -> float:
    """Effective number of trials from the eigenvalues of the correlation matrix.

    (sum of eigenvalues)^2 / (sum of squared eigenvalues), the participation ratio: if
    one factor (one principal component) explains everything, the result is 1; if all
    eigenvalues are equal (no common factor), it is N.
    """
    eig = np.linalg.eigvalsh(trials.corr().to_numpy())
    eig = np.clip(eig, 0, None)
    return float(eig.sum() ** 2 / (eig ** 2).sum())


# (f): minimum track record length ------------------------------------------------------

def min_trl(sr: float, sr_star: float = 0.0, skew: float = 0.0, kurt: float = 3.0,
            alpha: float = 0.05) -> float:
    """Minimum track record length in periods (days) for SR to beat ``sr_star``.

    The number of observations needed so that PSR(sr_star) reaches 1 - alpha. Like a
    sample size calculation: the smaller the edge (SR - SR*), the longer you must watch.
    Divide by 252 for years.
    """
    if sr <= sr_star:
        raise ValueError(f"MinTRL is only defined when SR ({sr:.4f}) is above SR* ({sr_star:.4f})")
    z = sps.norm.ppf(1 - alpha)
    return float(1 + _sr_variance_factor(sr, skew, kurt) * (z / (sr - sr_star)) ** 2)


# (g): haircut Sharpe ratio -------------------------------------------------------------

def haircut_sharpe(trials: pd.DataFrame, selected: str,
                   methods: tuple[str, ...] = ("bonferroni", "holm", "fdr_by")) -> pd.DataFrame:
    """Sharpe ratio of the selected trial after correcting its p value for N tests.

    Every trial's t statistic is SR_daily * sqrt(T) with a two sided p value. The p
    values are adjusted across all trials (Bonferroni, Holm, or the Benjamini Hochberg
    Yekutieli false discovery rate). The adjusted p value of the selected trial is turned
    back into a t statistic and a Sharpe ratio; the haircut is the share lost.
    """
    n = len(trials)
    sr = trials.mean() / trials.std(ddof=1)
    t = sr * np.sqrt(n)
    p = 2 * sps.norm.sf(np.abs(t))
    pos = list(trials.columns).index(selected)
    sr_hat = sr.iloc[pos]
    rows = {}
    for method in methods:
        p_adj = multipletests(p, method=method)[1][pos]
        t_adj = sps.norm.ppf(1 - p_adj / 2)
        sr_adj = np.sign(sr_hat) * t_adj / np.sqrt(n)
        rows[method] = {"p_raw": p[pos], "p_adj": p_adj, "t_adj": t_adj,
                        "sr_adj_ann": sr_adj * np.sqrt(PERIODS),
                        "haircut": 1 - sr_adj / sr_hat if sr_hat != 0 else np.nan}
    return pd.DataFrame(rows).T


# (h): probability of backtest overfitting via CSCV -------------------------------------

def pbo_cscv(trials: pd.DataFrame, n_blocks: int = 16) -> dict:
    """Probability of backtest overfitting with combinatorially symmetric cross validation.

    The sample is cut into S contiguous blocks. For every way of choosing half of them as
    in sample (IS), the other half is out of sample (OOS). We pick the trial with the best
    IS Sharpe ratio and look up where it ranks OOS. PBO is the share of splits in which
    that IS winner lands at or below the OOS median: how often choosing the best backtest
    is no better than choosing at random.

    All IS statistics come from one matrix product of the split matrix (C x S) with the
    per block sums (S x N), so even 12,870 splits of 256 trials take seconds.

    Returns
    -------
    dict with pbo, logits, is_sr and oos_sr (the winner's daily Sharpe in each split),
    the degradation regression oos = intercept + slope * is, and p_oos_loss (share of
    splits where the winner loses money OOS).
    """
    if n_blocks % 2:
        raise ValueError("n_blocks must be even")
    x = trials.to_numpy(float)
    x = x[x.shape[0] % n_blocks:]  # drop the first T mod S rows
    t_used, n = x.shape
    blocks = x.reshape(n_blocks, t_used // n_blocks, n)
    sums, sumsq = blocks.sum(axis=1), (blocks ** 2).sum(axis=1)  # S x N each

    combos = np.zeros((_n_combos(n_blocks), n_blocks))
    for i, chosen in enumerate(combinations(range(n_blocks), n_blocks // 2)):
        combos[i, list(chosen)] = 1.0
    half = t_used // 2
    is_sr = _sr_from_sums(combos @ sums, combos @ sumsq, half)
    oos_sr = _sr_from_sums((1 - combos) @ sums, (1 - combos) @ sumsq, half)

    winner = is_sr.argmax(axis=1)
    rows = np.arange(len(combos))
    oos_winner = oos_sr[rows, winner]
    rank = 1 + (oos_sr < oos_winner[:, None]).sum(axis=1)  # 1 = worst, N = best
    omega = rank / (n + 1)
    logits = np.log(omega / (1 - omega))
    slope, intercept = np.polyfit(is_sr[rows, winner], oos_winner, 1)
    return {"pbo": float((logits <= 0).mean()), "logits": logits,
            "is_sr": is_sr[rows, winner], "oos_sr": oos_winner,
            "slope": float(slope), "intercept": float(intercept),
            "p_oos_loss": float((oos_winner < 0).mean()),
            "n_blocks": n_blocks, "n_combos": len(combos), "t_used": t_used}


def _n_combos(s: int) -> int:
    return comb(s, s // 2)


def _sr_from_sums(s: np.ndarray, ss: np.ndarray, n: int) -> np.ndarray:
    var = (ss - s ** 2 / n) / (n - 1)
    return (s / n) / np.sqrt(var)


# (i): trial ledger ---------------------------------------------------------------------

def _ledger_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def ledger_append(project: str, data_id: str, trial_stats: pd.DataFrame,
                  path: str = "output/trial_ledger.csv") -> None:
    """Append one row per trial to the permanent trial ledger (never delete rows).

    ``trial_stats`` is indexed by trial id and has an annualized ``sharpe`` column.
    ``data_id`` identifies the data, for example ``"SPY 1993-02-01 2026-10-09"``.
    Relative paths are resolved from the repository root.
    """
    rows = pd.DataFrame({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "project": project,
        "data_id": data_id,
        "trial_id": trial_stats.index.astype(str),
        "sharpe": trial_stats["sharpe"].to_numpy(float),
    })
    file = _ledger_path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(file, mode="a", header=not file.exists(), index=False)


def ledger_count(project: str, data_id: str, path: str = "output/trial_ledger.csv") -> int:
    """Number of distinct trial ids ever run by this project on this data (0 if none).

    A data id that ends in a date (``"SPY 1993-02-01 2026-10-09"``) is matched without
    that end date: when the data is refreshed and runs further, every trial tried on the
    shorter history still counts.
    """
    file = _ledger_path(path)
    if not file.exists():
        return 0
    ledger = pd.read_csv(file)
    same_data = ledger["data_id"].map(_series_key) == _series_key(data_id)
    mask = (ledger["project"] == project) & same_data
    return int(ledger.loc[mask, "trial_id"].nunique())


def _series_key(data_id: str) -> str:
    """The data id without a trailing end date (YYYY-MM-DD), if it has one."""
    head, _, last = str(data_id).rpartition(" ")
    is_date = len(last) == 10 and last[4] == last[7] == "-" and last.replace("-", "").isdigit()
    return head if head and is_date else str(data_id)


# Holdout check -------------------------------------------------------------------------

def holdout(trials: pd.DataFrame, benchmark: pd.Series, split: float = 2 / 3) -> dict:
    """Select the best trial on the first part of the sample and test it on the rest.

    This is what a researcher should have done before looking at the whole sample: the
    last ``1 - split`` of the dates are never used for selection. Sharpe ratios are
    annualized; rank 1 is the best trial in the holdout.
    """
    cut = int(len(trials) * split)
    train, test = trials.iloc[:cut], trials.iloc[cut:]
    sr_train = train.mean() / train.std(ddof=1) * np.sqrt(PERIODS)
    sr_test = test.mean() / test.std(ddof=1) * np.sqrt(PERIODS)
    selected = sr_train.idxmax()
    bench_test = benchmark.loc[test.index]
    return {
        "selected": selected, "split_date": test.index[0],
        "train_sr": float(sr_train[selected]),
        "test_sr": float(sr_test[selected]),
        "test_sr_benchmark": float(bench_test.mean() / bench_test.std(ddof=1) * np.sqrt(PERIODS)),
        "test_sr_median_trial": float(sr_test.median()),
        "test_rank": int(sr_test.rank(ascending=False)[selected]),
        "n_trials": trials.shape[1], "test_sharpes": sr_test,
    }


# (j): the report -----------------------------------------------------------------------

def referee_report(trials: pd.DataFrame, selected: str, n_blocks: int = 16,
                   alpha: float = 0.05, n_ledger: int | None = None,
                   thresholds: dict | None = None) -> dict:
    """Run every referee tool on the selected trial and give a verdict.

    Parameters
    ----------
    trials : T x N daily excess returns of all trials, on a common sample.
    selected : column name of the trial that was picked (usually the best one).
    n_blocks : number of CSCV blocks for PBO.
    alpha : significance level for MinTRL.
    n_ledger : trials ever run on this data according to the ledger. The deflated
        Sharpe ratio uses N = max(trials in this run, n_ledger), so earlier sessions
        count too.
    thresholds : override the verdict thresholds in ``VERDICT_THRESHOLDS``.
    """
    th = {**VERDICT_THRESHOLDS, **(thresholds or {})}
    x = trials[selected]
    m = moments(x)
    t_len = m["n"]
    n_run = trials.shape[1]
    n_used = max(n_run, n_ledger or 0)
    trial_sr = trials.mean() / trials.std(ddof=1)
    var_sr = float(trial_sr.var(ddof=1)) if n_run > 1 else 1 / (t_len - 1)
    nw_lags = int(4 * (t_len / 100) ** (2 / 9))
    n_eff = {"raw": n_used, "avg_corr": n_eff_avgcorr(trials), "eigen": n_eff_eigen(trials)}
    sr0 = {k: expected_max_sr(v, var_sr) for k, v in n_eff.items()}
    dsrs = {k: psr_from_moments(m["sr"], t_len, m["skew"], m["kurt"], v) for k, v in sr0.items()}
    pbo = pbo_cscv(trials, n_blocks)

    def trl_years(sr_star):
        try:
            return min_trl(m["sr"], sr_star, m["skew"], m["kurt"], alpha) / PERIODS
        except ValueError:
            return np.nan

    rep = {
        "selected": selected, "start": trials.index[0], "end": trials.index[-1],
        "t": t_len, "years": t_len / PERIODS, "n_run": n_run, "n_ledger": n_ledger,
        "n_used": n_used, "n_eff": n_eff,
        "sr_ann": m["sr"] * np.sqrt(PERIODS), "sr_daily": m["sr"],
        "skew": m["skew"], "kurt": m["kurt"],
        "t_iid": tstat_mean(x), "t_nw": tstat_mean(x, nw_lags=nw_lags), "nw_lags": nw_lags,
        "psr0": psr_from_moments(m["sr"], t_len, m["skew"], m["kurt"], 0.0),
        "var_sr": var_sr, "sr0_ann": {k: v * np.sqrt(PERIODS) for k, v in sr0.items()},
        "dsr": dsrs,
        "min_trl_years": {"vs_zero": trl_years(0.0), "vs_sr0": trl_years(sr0["raw"])},
        "haircut": haircut_sharpe(trials, selected),
        "pbo": pbo, "alpha": alpha, "thresholds": th,
    }
    rep["verdict"] = _verdict(dsrs["raw"], pbo["pbo"], th)
    return rep


def _verdict(dsr_value: float, pbo_value: float, th: dict) -> str:
    if dsr_value >= th["strong_dsr"] and pbo_value <= th["strong_pbo"]:
        return "Strong"
    if dsr_value >= th["weak_dsr"] and pbo_value <= th["weak_pbo"]:
        return "Weak"
    return "Not distinguishable from luck"


def report_to_markdown(rep: dict) -> str:
    """The referee table and verdict as markdown, ready for report.md or a notebook."""
    hc = rep["haircut"]
    th = rep["thresholds"]
    ne = rep["n_eff"]
    lines = [
        f"**Selected trial:** `{rep['selected']}` · {rep['start']:%Y-%m-%d} to {rep['end']:%Y-%m-%d} "
        f"({rep['years']:.1f} years, T = {rep['t']:,})",
        "",
        "| Measure | Value | Meaning |",
        "| --- | --- | --- |",
        f"| Sharpe ratio (annualized) | {rep['sr_ann']:.2f} | before any correction |",
        f"| t statistic, iid / Newey West ({rep['nw_lags']} lags) | {rep['t_iid']:.2f} / {rep['t_nw']:.2f} | above 2 is the usual bar, above 3 after a search |",
        f"| Skewness / kurtosis | {rep['skew']:.2f} / {rep['kurt']:.1f} | normal is 0 / 3 |",
        f"| PSR(0) | {rep['psr0']:.3f} | probability the true Sharpe is above 0, ignoring the search |",
        f"| Trials: this run / ledger / used | {rep['n_run']} / {rep['n_ledger'] if rep['n_ledger'] is not None else 'n.a.'} / {rep['n_used']} | |",
        f"| Effective trials: avg corr / eigen | {ne['avg_corr']:.1f} / {ne['eigen']:.1f} | independent bets among the trials |",
        f"| Hurdle SR0 (annualized): raw N / avg corr / eigen | {rep['sr0_ann']['raw']:.2f} / {rep['sr0_ann']['avg_corr']:.2f} / {rep['sr0_ann']['eigen']:.2f} | expected best Sharpe of that many useless trials |",
        f"| DSR: raw N / avg corr / eigen | {rep['dsr']['raw']:.3f} / {rep['dsr']['avg_corr']:.3f} / {rep['dsr']['eigen']:.3f} | probability the true Sharpe beats the hurdle |",
        f"| MinTRL in years vs 0 / vs SR0 (actual {rep['years']:.1f}) | {_fmt_years(rep['min_trl_years']['vs_zero'])} / {_fmt_years(rep['min_trl_years']['vs_sr0'])} | track record needed at {1 - rep['alpha']:.0%} confidence |",
    ]
    for method, label in [("bonferroni", "Bonferroni"), ("holm", "Holm"), ("fdr_by", "BHY")]:
        if method in hc.index:
            row = hc.loc[method]
            lines.append(f"| Haircut Sharpe, {label} | {row['sr_adj_ann']:.2f} ({row['haircut']:.0%} haircut) | Sharpe left after correcting for {rep['n_run']} tests |")
    pbo = rep["pbo"]
    lines += [
        f"| PBO (CSCV, {pbo['n_blocks']} blocks, {pbo['n_combos']:,} splits) | {pbo['pbo']:.2f} | share of splits where the IS winner is at or below the OOS median |",
        f"| P(OOS loss) / degradation slope | {pbo['p_oos_loss']:.2f} / {pbo['slope']:.2f} | slope 1 means IS performance carries over fully |",
        "",
        f"**Verdict: {rep['verdict']}.** Strong needs DSR at least {th['strong_dsr']} and PBO at most "
        f"{th['strong_pbo']}; Weak needs DSR at least {th['weak_dsr']} and PBO at most {th['weak_pbo']}. "
        "These thresholds are conventions, not laws.",
    ]
    return "\n".join(lines)


def _fmt_years(v: float) -> str:
    return "not defined" if np.isnan(v) else f"{v:.1f}"
