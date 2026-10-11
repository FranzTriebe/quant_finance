# quantlab · Project 1: The Backtest Referee

Build plan for Claude Code. Read `CLAUDE.md` first; it holds the standing rules for this repo.

Work **one phase at a time** (section 10). After each phase, stop at its checkpoint and wait for Franz.

> **Changes agreed after this plan was written (2026-10-11)**
> 1. **Notebooks instead of scripts.** Everything in `projects/p01_referee/` is a Jupyter notebook in the `notebook-craft` format, numbered in order (`01_...ipynb`). Where this plan says `monte_carlo.py`, `run.py` and so on, read the matching notebook; command line flags such as `--ticker` become entries in the notebook's parameters cell.
> 2. **Trial family in the engine.** Code that tests must import, such as `build_trials` from section 7.2, moves into `quantlab/` so notebooks stay free of local helper files.
> 3. **Commits** follow the `git-commits` skill and every clear step is pushed (see `CLAUDE.md`).
> 4. **Figures and reports.** Figures follow the `academic-graphs` skill (black and white, via `quantlab.acad`) instead of the colour palette in section 6.6; `plotting.PALETTE` and `apply_style()` remain for compatibility. Reports and briefs are LaTeX documents in the `model-docs` house style.

---

## 1. Goal

Build a reusable "referee" that answers one question:

> I tried N variants of a strategy and kept the best one. How much of its backtest should I believe?

Then run it on about 250 trend timing rules for an equity index (the 200 day moving average rule among them) and write up the verdict.

The referee is the foundation for every later project in this repo. Nothing gets called a result until it has passed through the referee.

### Why this is worth building

* Investment banks' "alternative beta" strategies lost a **median 73% of their Sharpe ratio** between backtest and live trading, and the most complex strategies lost the most (Suhonen, Lennkh, Perez 2017).
* Across 888 Quantopian algorithms, the backtest Sharpe ratio explained **less than 2.5%** of live performance (Wiecki et al. 2016).
* After only **7 tries**, you should expect at least one 2 year backtest with an annualized Sharpe of about 1, even when every true Sharpe is zero (López de Prado 2013). A simulation check for this plan gave 0.97.
* Harvey, Liu and Zhu (2016) argue that a new factor needs a t statistic above 3, not above 2.
* Counterweight: Jensen, Kelly and Pedersen (2023) find that most published equity factors do replicate. The aim is calibrated trust, not blanket distrust.
* The field is still active. López de Prado and coauthors published new standards for Sharpe ratio inference and the deflated Sharpe ratio in the Journal of Portfolio Management in 2026.

### Definition of done for Project 1

1. `quantlab/` engine with the interfaces in section 6, fully tested.
2. `projects/p01_referee/` scripts produce `output/p01/report.md` and four figures from one command.
3. Any new strategy idea can be run through the referee in one command, and its trials are counted in a persistent trial ledger.
4. Franz can explain every number in the report.

---

## 2. Who is learning

* **Background:** BA in Economics (Basel) with a minor in quantitative methods. Exchange semester at HSG with courses in Applied Monte Carlo Simulation, Machine Learning in Finance, and Data Science & Numerical Optimization.
* **Already comfortable with:** OLS, t tests, skewness and kurtosis, the bootstrap, and pandas.
* **New to him:**
  * multiple testing corrections as used in finance
  * the deflated Sharpe ratio
  * combinatorially symmetric cross validation (CSCV)

At every checkpoint, explain each new concept in plain language and link it to his coursework. Section 9 has the mapping.

---

## 3. Repository layout

```
quantlab/
    CLAUDE.md
    PLAN.md
    README.md               setup, how to run, project ladder
    requirements.txt
    pyproject.toml          [tool.pytest.ini_options] pythonpath = ["."], testpaths = ["tests"]
    .vscode/settings.json   interpreter .venv, pytest enabled
    .gitignore              .venv, data/*, output/*, __pycache__, .DS_Store
    quantlab/               the engine: pure functions, file I/O only in data.py
        __init__.py
        data.py
        risk.py
        backtest.py
        stats.py
        validation.py       the referee
        plotting.py
    projects/
        p01_referee/
            monte_carlo.py
            strategies.py
            run.py
            my_rules.py     Franz's own ideas (Phase 5)
    tests/
        test_backtest.py
        test_validation.py
        test_strategies.py
    data/                   cached downloads (gitignored, keep a .gitkeep)
    output/                 figures, reports, trial ledger (gitignored, keep a .gitkeep)
```

---

## 4. Environment

* Python 3.11 or newer, with a virtual environment in `.venv`.
* Contents of `requirements.txt`: `numpy`, `pandas`, `scipy`, `statsmodels`, `matplotlib`, `yfinance`, `pytest`, `ipykernel`.
* Contents of `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.analysis.extraPaths": ["${workspaceFolder}"],
  "jupyter.notebookFileRoot": "${workspaceFolder}"
}
```

* Project scripts use `# %%` cell markers. That way they run as normal scripts and also cell by cell in the VS Code interactive window.

---

## 5. Conventions

These apply everywhere in the repo.

1. **Returns.** Daily simple returns in decimals, with a sorted `DatetimeIndex`.
2. **Excess returns.** Work in excess returns `x_t = r_t − rf_t`. If no risk free series is given, `rf = 0`.
3. **No look ahead.**
   * Strategy functions return *target weights as of the close of day t*, computed only from data up to and including day t.
   * `backtest.run` is the only place that shifts weights, by `lag` days (default 1).
   * Strategy code never shifts.
4. **Sharpe ratios inside formulas are per period (daily) and never annualized.**
   * Skewness is the sample skewness.
   * Kurtosis is **Pearson kurtosis**, where a normal distribution has kurtosis 3: `scipy.stats.kurtosis(x, fisher=False)`.
   * Annualize with √252 only for display.
5. **Costs.** Proportional to turnover. Default is 5 bp per unit of one way turnover.
6. **Common sample.** All trials in one comparison share exactly the same dates. Start after the longest warmup.
7. **Reproducibility.**
   * Random seeds are fixed.
   * Tests never touch the internet.
   * Every script writes its outputs to `output/p01/`.

---

## 6. Engine specification (`quantlab/`)

### 6.1 `data.py`

```python
def load_yahoo(ticker: str, start: str = "1990-01-01", end: str | None = None,
               refresh: bool = False) -> pd.Series:
    """Daily simple returns from adjusted closes (yfinance, auto_adjust=True).
    Caches prices in data/yahoo_<ticker>.csv and reuses the cache unless refresh=True."""

def load_rf_daily(refresh: bool = False) -> pd.Series:
    """Daily US risk free rate in decimals from the Ken French data library.
    URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip
    Column RF is in percent. Parsing: skip lines until the first line that starts with an 8 digit date
    (YYYYMMDD), stop at the first non date line (copyright footer). Cache in data/."""

def load_csv_prices(path: str, date_col: str, price_col: str) -> pd.Series:
    """For Franz's own exports (bank statements, other data vendors)."""

def prices_to_returns(prices: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame: ...

def simulate_returns(n_obs: int, n_assets: int = 1, ann_sharpe: float | np.ndarray = 0.0,
                     ann_vol: float = 0.16, dist: str = "normal", df: int = 5,
                     seed: int = 0) -> pd.DataFrame:
    """Business day index. Student t draws are rescaled to unit variance.
    Used by every test so that tests run offline."""
```

Data notes:

* **SPY** (from 1993) includes dividends through the adjusted close. Use it as the default.
* **^GDAXI** (DAX, from 1987) is a performance index, so dividends are already included.
* **^GSPC** goes back to 1927 but is a price index without dividends. If it is used, add that as a caveat in the report.
* yfinance sometimes rate limits. That is why prices are cached. On failure, raise a clear error that suggests `load_csv_prices`.

### 6.2 `risk.py`

```python
def ewma_vol(r, halflife: int = 20, periods: int = 252) -> pd.Series   # annualized, uses data up to and including t
def rolling_vol(r, window: int = 63, periods: int = 252) -> pd.Series
def drawdown(r) -> pd.Series
def max_drawdown(r) -> float
def to_monthly(r) -> pd.Series                                         # compounded within the month
```

### 6.3 `backtest.py`

```python
def run(weights: pd.Series | pd.DataFrame, returns: pd.Series | pd.DataFrame,
        lag: int = 1, cost_bps: float = 5.0, rf: pd.Series | None = None) -> pd.DataFrame:
    """Columns: position, turnover, cost, excess, total."""
```

The function computes, for each day t:

* `position_t = weights_{t − lag}`
* `turnover_t = Σ |position_t − position_{t−1}|`
* `cost_t = turnover_t × cost_bps / 10,000`
* `excess_t = Σ position_t · (r_t − rf_t) − cost_t`
* `total_t = excess_t + rf_t`

A short position of −1 earns `rf − (r − rf)`, which is how a futures implementation behaves.

```python
def run_many(weights: dict[str, pd.Series], returns: pd.Series, **kw) -> pd.DataFrame:
    """T × N matrix of daily excess returns, one column per trial id, all on a common sample."""
```

### 6.4 `stats.py`

```python
def sharpe(x, periods: int = 252, annualize: bool = True) -> float     # x = excess returns
def tstat_mean(x, nw_lags: int | None = None) -> float                 # iid, or Newey West via statsmodels OLS on a constant, cov_type="HAC"
def summary(x, total=None, position=None) -> pd.Series
```

`summary` reports the following:

* annualized mean excess return
* annualized geometric total return
* annualized volatility
* Sharpe and Sortino ratios
* maximum drawdown and Calmar ratio
* skewness and Pearson kurtosis
* hit rate
* share of time in the market
* turnover per year

### 6.5 `validation.py` (the referee)

Notation: `x` is the per period excess return series of length T. Then:

* $\hat{SR} = \bar x / s$ (with ddof = 1)
* $\hat\gamma_3$ is the skewness and $\hat\gamma_4$ is the Pearson kurtosis
* $\Phi$ is the standard normal CDF

**(a) Standard error of the Sharpe ratio, allowing for non normal returns** (Bailey & López de Prado 2012, building on Lo 2002):

$$\hat\sigma(\hat{SR}) = \sqrt{\frac{1 - \hat\gamma_3 \hat{SR} + \frac{\hat\gamma_4 - 1}{4}\hat{SR}^2}{T-1}}$$

Sanity check: when returns are normal ($\gamma_3 = 0$, $\gamma_4 = 3$), this becomes $\sqrt{(1 + \hat{SR}^2/2)/(T-1)}$.

**(b) Probabilistic Sharpe ratio**, which is the probability that the true SR exceeds a benchmark $SR^*$ (per period):

$$PSR(SR^*) = \Phi\!\left(\frac{(\hat{SR} - SR^*)\sqrt{T-1}}{\sqrt{1 - \hat\gamma_3\hat{SR} + \frac{\hat\gamma_4-1}{4}\hat{SR}^2}}\right)$$

**(c) Expected maximum Sharpe ratio of N trials when every true SR is zero** (the "false strategy" benchmark in Bailey & López de Prado 2014):

$$SR_0 = \sqrt{V}\left((1-\gamma)\,\Phi^{-1}\!\left(1-\tfrac1N\right) + \gamma\,\Phi^{-1}\!\left(1-\tfrac{1}{Ne}\right)\right)$$

* $\gamma \approx 0.5772$ is the Euler Mascheroni constant and $e$ is Euler's number.
* $V$ is the cross sectional variance of the N trial Sharpe ratios (per period).
* In the Monte Carlo check, use $V = 1/(T-1)$.

Verified for this plan: the formula is within about 4% of simulation for N ≥ 7. It is 9 to 13% off for N = 2.

**(d) Deflated Sharpe ratio:** $DSR = PSR(SR_0)$, computed on the selected strategy's own T, skewness and kurtosis.

**(e) Effective number of independent trials.** Trials are highly correlated: Levine & Pedersen (2016) show that moving average and momentum trend filters are close relatives. Report both of these estimates next to the raw N:

* `n_eff_avgcorr` $= \bar\rho + (1-\bar\rho)N$, where $\bar\rho$ is the average off diagonal correlation of the trial returns
* `n_eff_eigen` $= (\sum\lambda_i)^2 / \sum\lambda_i^2$, using the eigenvalues of the trial correlation matrix

Both are simple, transparent approximations. Say so in the report.

**(f) Minimum track record length** (Bailey & López de Prado 2012), in periods. Divide by 252 to get years. It is only defined when $\hat{SR} > SR^*$.

$$MinTRL = 1 + \left(1 - \hat\gamma_3\hat{SR} + \frac{\hat\gamma_4-1}{4}\hat{SR}^2\right)\left(\frac{\Phi^{-1}(1-\alpha)}{\hat{SR}-SR^*}\right)^2$$

**(g) Haircut Sharpe ratio** (Harvey & Liu 2015):

1. For every trial, compute $t = \hat{SR}_{daily}\sqrt{T}$ and its two sided p value.
2. Adjust the p values across all N trials with `statsmodels.stats.multitest.multipletests`, using the methods `"bonferroni"`, `"holm"` and `"fdr_by"` (BHY).
3. For the selected trial, compute:
   * $t_{adj} = \Phi^{-1}(1 - p_{adj}/2)$
   * $SR_{adj} = t_{adj}/\sqrt{T}$
   * haircut $= 1 - SR_{adj}/\hat{SR}$
4. If $p_{adj} = 1$, then $SR_{adj} = 0$ and the haircut is 100%.

Also report the Newey West t statistic, because daily strategy returns can be autocorrelated.

**(h) Probability of backtest overfitting via CSCV** (Bailey, Borwein, López de Prado, Zhu 2016). The input is the T × N trial matrix.

1. Drop the first `T mod S` rows. Split the rest into S contiguous blocks (default S = 16, must be even).
2. Loop over all $\binom{S}{S/2}$ ways to choose half of the blocks (12,870 when S = 16). For each:
   1. The in sample (IS) part is the chosen blocks and the out of sample (OOS) part is the rest.
   2. Compute every trial's Sharpe ratio on IS and on OOS.
   3. Let $n^*$ be the IS winner.
   4. Compute $\omega = \text{rank}_{OOS}(n^*)/(N+1)$, where rank 1 is the worst and rank N is the best.
   5. Compute the logit $\lambda = \ln(\omega/(1-\omega))$.
3. PBO is the share of combinations where $\lambda \le 0$, meaning the IS winner finished at or below the OOS median.
4. Also return:
   * the winner's IS and OOS Sharpe ratio for each combination
   * the regression OOS = a + b · IS (the performance degradation slope)
   * $P(\text{OOS SR} < 0)$

Implementation hint: precompute per block sums, sums of squares and counts. Then all IS statistics are one matrix product, `combos (C × S) @ block_sums (S × N)`. With N = 256 the whole thing must run in a few seconds.

**(i) Trial ledger**

```python
def ledger_append(project: str, data_id: str, trial_stats: pd.DataFrame,
                  path: str = "output/trial_ledger.csv") -> None
def ledger_count(project: str, data_id: str, path: str = "output/trial_ledger.csv") -> int
```

* Each row is one trial run: timestamp, project, data_id (ticker plus sample dates), trial_id, and annualized Sharpe.
* `ledger_count` counts distinct trial ids ever run on that data.
* The DSR uses `N = max(trials in this run, ledger_count)`. That keeps the trial count honest across sessions.

**(j) Report**

```python
def referee_report(trials: pd.DataFrame, selected: str, n_blocks: int = 16,
                   alpha: float = 0.05, n_ledger: int | None = None) -> dict
def report_to_markdown(rep: dict) -> str
```

The verdict depends on parameters, with these defaults:

| Verdict | Condition |
|---|---|
| "Strong" | DSR ≥ 0.95 and PBO ≤ 0.20 |
| "Weak" | DSR ≥ 0.80 and PBO ≤ 0.50, but not Strong |
| "Not distinguishable from luck" | everything else |

These thresholds are conventions, not laws. The report says so.

### 6.6 `plotting.py`

`apply_style()` plus a `PALETTE` dict:

| Role | Color |
|---|---|
| primary | `#2a78d6` |
| comparison | `#eb6834` |
| third | `#1baf7a` |
| text | `#0b0b0b` |
| text_secondary | `#52514e` |
| grid | `#e4e3df` |
| surface | `#fcfcfb` |

Style rules:

* One y axis per chart, never two.
* 2px lines and a solid hairline grid.
* Text uses the text colors, never series colors.
* Add a legend when there are 2 or more series. Label reference lines directly.
* The title states the takeaway.

---

## 7. Project scripts (`projects/p01_referee/`)

### 7.1 `monte_carlo.py`: why the best of N lies

1. **Maximum Sharpe of zero skill strategies.**
   * Settings: T ∈ {504 (2 years), 2520 (10 years)}, N ∈ {1, 2, 5, 7, 10, 20, 50, 100, 250, 1000}, and 2,000 simulations per cell (fewer for N = 1000 if it is slow).
   * Run it twice: once with normal returns and once with Student t returns (df = 5).
   * Plot the simulated mean and the 5% to 95% band of the maximum annualized SR against N (log x axis), with the formula (c) curve on top. This is **Figure F1**.
   * Check: at N = 7 and T = 504, the result is about 1.0.
2. **PBO calibration**, using N = 100, T = 2520 and S = 16:
   * pure noise strategies: PBO should be about 0.5
   * one planted strategy with a true annualized SR of 2.0: PBO should be about 0
   * one planted strategy with a true annualized SR of 1.0: PBO comes out around 0.25. This is the teaching point: even a real edge competes with lucky noise.
3. Print a short plain language summary.

### 7.2 `strategies.py`: the trial family

Every rule works on a single index. It takes a price series `P` and returns weights as of close t.

| Family | Rule | Parameters | Count |
|---|---|---|---|
| A | price above simple moving average SMA(L) | L ∈ {20, 50, 100, 150, 200, 250, 300} | 7 |
| B | SMA(fast) above SMA(slow) | fast ∈ {5, 10, 20, 50}, slow ∈ {50, 100, 150, 200, 250}, fast < slow | 19 |
| C | time series momentum: sign of $P_t / P_{t-21k} - 1$ | k ∈ {1, 2, 3, 6, 9, 12} months | 6 |

That gives 32 signals. Each signal is crossed with three variant dimensions, for **256 trials** in total (32 × 2 × 2 × 2):

* **Direction:** long/flat (weight 1 or 0) or long/short (weight +1 or −1).
* **Sizing:**
  * full: |w| = 1
  * vol targeted: w × min(1, 0.15 / ewma_vol(halflife 20))
* **Rebalancing:**
  * daily
  * weekly: take the weight on the last trading day of each week and hold it until the next one. Use `index.to_period("W-FRI")`.

Further requirements:

* Trial ids are readable, for example `sma200_lf_full_d` or `x20_150_ls_vt_w`.
* `build_trials(P) -> dict[str, pd.Series]` returns all 256 trials.
* Buy and hold is the benchmark. It is **not** a trial.

### 7.3 `run.py`: the full analysis

Command line:

```
python projects/p01_referee/run.py --ticker SPY --start 1993-01-01 --lag 1 --cost-bps 5 --blocks 16
python projects/p01_referee/run.py --ticker ^GDAXI
python projects/p01_referee/run.py --ticker SPY --my-rules        # Phase 5
```

Steps:

1. Load returns, plus the risk free rate for US tickers. For other tickers use rf = 0 and note it in the report.
2. Build the 256 trials and run the backtests with `run_many` (lag 1, 5 bp).
3. **Naive researcher:** pick the trial with the highest full sample Sharpe.
4. Run `referee_report` on it, using the trial ledger count.
5. **Holdout check:**
   1. Select the best trial on the first two thirds of the sample.
   2. Report its Sharpe on the last third, compared with buy and hold and with the median trial.
   3. Report its rank among all trials in the last third.
6. **Robustness:** repeat with lag 2 and with 10 bp costs. Does the winner change? Does the verdict change?
7. **Save** to `output/p01/`:
   * `trials.csv` (summary statistics of every trial)
   * `report.md`
   * Figures F2 to F4 (Figure F1 comes from `monte_carlo.py`)
8. Append the trials to the ledger.

Figures:

| Figure | Content |
|---|---|
| F1 | Maximum Sharpe of N zero skill strategies against N, simulation compared with formula (from `monte_carlo.py`) |
| F2 | Histogram of all 256 annualized trial Sharpe ratios, with labeled vertical lines for buy and hold, the hurdle $SR_0$ (annualized) and the selected winner |
| F3 | Two panels: histogram of the CSCV logits with the PBO annotated; scatter of the winner's IS Sharpe against its OOS Sharpe with the fitted line |
| F4 | Cumulative log wealth of the winner compared with buy and hold, with the holdout period shaded |

`report.md` sections:

1. **Setup:** data, dates, T, trials in this run and in the ledger, lag, costs, risk free source.
2. Buy and hold compared with the naive winner, side by side (`stats.summary`).
3. **Referee table:**
   * annualized SR
   * t statistic (iid and Newey West)
   * PSR(0)
   * $SR_0$ (annualized)
   * DSR with raw N, `n_eff_avgcorr` and `n_eff_eigen`
   * MinTRL in years compared with the actual years
   * haircut Sharpe under Bonferroni, Holm and BHY
   * PBO, P(OOS loss) and the degradation slope
4. **Verdict line.**
5. **Holdout.**
6. **Robustness.**
7. **Caveats**, generated automatically:
   * price index or total return index
   * which risk free rate was used
   * the trial family contains famous rules, which were chosen with hindsight
   * daily autocorrelation
8. **Interpretation:** left empty by the code. After the run, Claude Code writes it in plain language and labels it as written after the run.

### 7.4 `my_rules.py` (Phase 5)

Franz writes functions with the signature `def rule_name(P: pd.Series) -> pd.Series`. With `--my-rules`, `run.py` adds them as extra trials. They are evaluated against the whole family and counted in the ledger.

---

## 8. Tests

All tests use `simulate_returns` with fixed seeds. They must pass offline in under a minute.

The thresholds below were checked by simulation while writing this plan.

**`test_backtest.py`**

* A weight of 1 set only on day d affects only the return of day d + 1 (when lag = 1).
* Cost equals turnover × bp / 10,000.
* A position of 0 earns exactly rf in `total` and exactly 0 in `excess`.
* `run_many` returns a common sample with no NaN values.

**`test_validation.py`**

* The SR standard error under normal returns matches $\sqrt{(1+SR^2/2)/(T-1)}$.
* `psr(x, sr_star=SR_hat) == 0.5`.
* The expected maximum SR is within 5% of simulation for N = 100 and T = 1000 (1,000 simulations).
* PBO on pure noise: the mean over 20 seeds lies in [0.42, 0.58]. Single runs scatter widely (0.24 to 0.76 in the check), so never test a single draw.
* PBO with a planted annualized SR of 2.0 among 99 noise strategies (T = 2520, fixed seed) is below 0.10.
* Bonferroni with N = 1 gives a haircut of 0. The haircut grows with N.
* MinTRL falls as SR rises. It raises a clear error when SR ≤ SR*.

**`test_strategies.py`**

* `build_trials` returns exactly 256 trials with unique ids.
* After warmup there are no NaN values. All weights lie in [−1, 1].
* **Look ahead test (most important):** perturb all prices after date d, rebuild the trials, and assert that every weight up to and including d is identical.

---

## 9. Concept map: referee tool to coursework

| Referee tool | What Franz already knows |
|---|---|
| Standard error of the Sharpe ratio | Standard error of a mean, delta method |
| PSR | One sided z test, corrected for skewness and kurtosis |
| Expected maximum Sharpe | Order statistics, extreme values of N normal draws, Monte Carlo |
| DSR | PSR measured against that maximum instead of against zero |
| Haircut Sharpe | Bonferroni, Holm, false discovery rate (Benjamini Hochberg Yekutieli) |
| PBO via CSCV | Cross validation from the ML course, applied to choosing a strategy instead of fitting a model |
| MinTRL | Sample size and power calculation |
| Newey West t statistic | HAC standard errors from econometrics |
| Effective number of trials | Correlation matrix, eigenvalues, PCA |

---

## 10. Phases and checkpoints

Do one phase, run `pytest -q`, commit (`p01 phase N: ...`), then **stop** and present the checkpoint.

| Phase | Build | Checkpoint for Franz | He should be able to answer |
|---|---|---|---|
| 0 | Repo skeleton, venv, git init, requirements, settings, empty tests | VS Code finds the interpreter, `pytest -q` runs | Where does the lag live, and why only there? |
| 1 | `data`, `risk`, `backtest`, `stats`, `plotting` + tests | Summary of SPY buy and hold since 1993: volatility around 19% a year, maximum drawdown around −55% in 2007 to 2009 | What exactly does a weight set on Monday earn? |
| 2 | `validation.py` + `monte_carlo.py` + tests | F1 shows about 1.0 at N = 7, T = 504; the three PBO calibration results | Why does the best of N rise with N and fall with T? |
| 3 | `strategies.py` + look ahead test | Table of all 256 trials sorted by Sharpe. Before seeing the referee, Franz writes down which result he would believe and why. | Why are these 256 trials far fewer than 256 independent bets? |
| 4 | `run.py`, report, F2 to F4 | Franz reads `report.md`; Claude Code explains every number in the referee table | What does a DSR of 0.6 mean in words? |
| 5 | Robustness options, trial ledger, `--my-rules` | Franz writes one rule of his own, runs it, and sees N grow | Why must the ledger never be reset? |
| 6 (optional) | 2 page model brief in LaTeX | Franz has a house format; ask him for it | |

**Honesty rule for Phases 4 and 5.** Do not change the trial family, the sample or the thresholds after seeing the referee's verdict. If the winner fails, that is a finding, not a failure of the project. A typical outcome for trend timing on one equity index is that the winner beats buy and hold in sample while the referee cannot tell it apart from luck. Write that plainly if it happens.

---

## 11. Optional extensions (after Phase 6)

* White's reality check or Hansen's SPA test with a stationary bootstrap, as a third independent referee.
* Sharpe inference with serially correlated, non normal returns, following López de Prado et al. (2026).
* Clustering trials (hierarchical clustering on the correlation matrix) as a better estimate of the effective N.

---

## 12. What comes next (keep interfaces stable)

Later projects call `backtest.run_many` and `validation.referee_report` and log to the same ledger.

* **P2: Regime switching with statistical jump models** (Shu, Yu, Mulvey 2024).
  * Classify bull and bear regimes from return features, with a penalty on switching. Reduce exposure in bear regimes on the S&P 500, DAX and SMI.
  * Every jump penalty tried counts as a trial.
* **P3: Trend following across asset classes and CTA replication** (Moskowitz, Ooi, Pedersen 2012; Hurst, Ooi, Pedersen 2013).
  * Regress the Quantica Managed Futures UCITS NAV on trend factors at different speeds.
* **P4: Swiss franc hedging for Franz's own portfolio** (Campbell, Serfaty-de Medeiros, Viceira 2010).
* **P5: Technology momentum from REGPAT patent data** (Lee, Sun, Wang, Zhang 2019). This is the flagship, building on his thesis data.

---

## 13. References

* Bailey & López de Prado (2012). [The Sharpe Ratio Efficient Frontier](https://consensus.app/papers/details/318f32d46c755b108109d1629328d3b7/?utm_source=claude_desktop). Journal of Risk. DOI 10.2139/ssrn.1821643
* Bailey & López de Prado (2014). [The Deflated Sharpe Ratio](https://consensus.app/papers/details/378afd063fd15487a4fcb21af0850767/?utm_source=claude_desktop). Journal of Portfolio Management. DOI 10.3905/jpm.2014.40.5.094
* Bailey, Borwein, López de Prado, Zhu (2016). [The Probability of Backtest Overfitting](https://consensus.app/papers/details/f5ef21e8509b544fba76ccc9aa2de55c/?utm_source=claude_desktop). DOI 10.2139/ssrn.2326253
* López de Prado (2013). [Computing the Probability of Overfitting in the Backtesting and Optimization of Investment Strategies](https://consensus.app/papers/details/dad5b8cfdbad5a0f91a8d052407af09a/?utm_source=claude_desktop)
* Harvey & Liu (2015). [Backtesting](https://consensus.app/papers/details/26c79e6752075f64842d5bd2e1a67f72/?utm_source=claude_desktop). Journal of Portfolio Management. DOI 10.3905/jpm.2015.42.1.013
* Harvey, Liu, Zhu (2016). [... and the Cross-Section of Expected Returns](https://consensus.app/papers/details/3568af295ac75e38b7e082106da51311/?utm_source=claude_desktop). Review of Financial Studies. DOI 10.1093/rfs/hhv059
* Harvey & Liu (2020). [An Evaluation of Alternative Multiple Testing Methods for Finance Applications](https://consensus.app/papers/details/0b909de8bb8a51b7a451c79e7eaef4cf/?utm_source=claude_desktop). Review of Asset Pricing Studies. DOI 10.1093/rapstu/raaa003
* Lo (2002). [The Statistics of Sharpe Ratios](https://consensus.app/papers/details/ae10105da6315c3da6ea60251ec0b456/?utm_source=claude_desktop). Financial Analysts Journal. DOI 10.2469/faj.v58.n4.2453
* Suhonen, Lennkh, Perez (2017). [Quantifying Backtest Overfitting in Alternative Beta Strategies](https://consensus.app/papers/details/df15834241b85f16a52df4f546753386/?utm_source=claude_desktop). Journal of Portfolio Management. DOI 10.3905/jpm.2017.43.2.090
* Wiecki et al. (2016). [All That Glitters Is Not Gold](https://consensus.app/papers/details/cbf1b88914f55668987babb345905af4/?utm_source=claude_desktop). Journal of Investing. DOI 10.3905/joi.2016.25.3.069
* Jensen, Kelly, Pedersen (2023). [Is There a Replication Crisis in Finance?](https://consensus.app/papers/details/e70e9b4b51b35178b6e16cbf78086437/?utm_source=claude_desktop) DOI 10.3386/w28432
* López de Prado et al. (2026). [Sharpe Ratio Inference: A New Standard for Decision Making and Reporting](https://consensus.app/papers/details/a5bf04463c2f5b8e8d1a6b474c79443f/?utm_source=claude_desktop). Journal of Portfolio Management. DOI 10.3905/jpm.2026.1.837
* López de Prado et al. (2026). [The Deflated Sharpe Ratio: A Unified Framework for Search-Adjusted Performance Inference](https://consensus.app/papers/details/60fe2b8163ba516cb2ce633a20451d2e/?utm_source=claude_desktop). Journal of Portfolio Management. DOI 10.3905/jpm.2026.070
* Levine & Pedersen (2016). [Which Trend Is Your Friend?](https://consensus.app/papers/details/6f6ad2e8252a59309fb8dcb2b2966b8e/?utm_source=claude_desktop). Financial Analysts Journal. DOI 10.2469/faj.v72.n3.3
* Moskowitz, Ooi, Pedersen (2012). [Time Series Momentum](https://consensus.app/papers/details/1e4090b52b0e50cc9e781c24971f060a/?utm_source=claude_desktop). Journal of Financial Economics. DOI 10.1016/j.jfineco.2011.11.003
* Shu, Yu, Mulvey (2024). [Downside Risk Reduction Using Regime-Switching Signals: A Statistical Jump Model Approach](https://consensus.app/papers/details/af35e1366f905ee684be45e4e031242f/?utm_source=claude_desktop). Journal of Asset Management. DOI 10.1057/s41260-024-00376-x
* Hurst, Ooi, Pedersen (2013). [Demystifying Managed Futures](https://consensus.app/papers/details/c099096df8aa5f2c943cfc372fdb424e/?utm_source=claude_desktop). Journal of Investment Management
* Campbell, Serfaty-de Medeiros, Viceira (2010). [Global Currency Hedging](https://consensus.app/papers/details/f3bd1caec46a5c8c9cbf7f169ff9d6b4/?utm_source=claude_desktop). Journal of Finance. DOI 10.2139/ssrn.970847
* Lee, Sun, Wang, Zhang (2019). [Technological Links and Predictable Returns](https://consensus.app/papers/details/3227487a163d5de09468aabe2726e11a/?utm_source=claude_desktop). Journal of Financial Economics. DOI 10.1016/j.jfineco.2018.11.008

---

## 14. Kickoff prompt (paste into Claude Code)

```
Read CLAUDE.md and PLAN.md in this folder. We are building Project 1, the backtest referee.
Start with Phase 0 only. When it is done, run the tests, commit, and stop at the
checkpoint. Explain what you built in plain language and tell me what I should look at.
Do not start Phase 1 until I say go.
```
