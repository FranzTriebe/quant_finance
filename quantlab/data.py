"""Data loading and caching.

Yahoo prices, the Ken French daily risk free rate, CSV imports and simulated returns.
This is the only module in quantlab that reads or writes files. Downloads are cached in
the repo's ``data/`` folder, so a rerun uses exactly the same numbers unless you ask
for a refresh.
"""

from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
FRENCH_DAILY_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_Factors_daily_CSV.zip"
)
TRADING_DAYS = 252


def load_yahoo(ticker: str, start: str = "1990-01-01", end: str | None = None,
               refresh: bool = False) -> pd.Series:
    """Daily simple returns from adjusted closes (yfinance, auto_adjust=True).

    Adjusted closes fold dividends and splits into the price, so for SPY the returns are
    total returns. The full price history is cached in ``data/yahoo_<ticker>.csv`` and
    reused unless ``refresh=True``; ``start`` and ``end`` only slice the cached history.

    Parameters
    ----------
    ticker : Yahoo symbol, for example ``"SPY"`` or ``"^GDAXI"``.
    start, end : first and last date to keep (inclusive), as ``"YYYY-MM-DD"``.
    refresh : download again even if a cache file exists.

    Returns
    -------
    pd.Series of daily simple returns in decimals, named after the ticker.
    """
    path = DATA_DIR / f"yahoo_{ticker.replace('^', '').replace('/', '_')}.csv"
    if refresh or not path.exists():
        prices = _download_yahoo(ticker)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        prices.to_frame("close").to_csv(path)
    prices = pd.read_csv(path, index_col=0, parse_dates=True)["close"]
    prices.index.name = "date"
    prices = prices.loc[start:end]
    return prices_to_returns(prices).rename(ticker)


def _download_yahoo(ticker: str) -> pd.Series:
    """Full adjusted close history from Yahoo, with a helpful error when it fails."""
    import yfinance as yf

    try:
        raw = yf.download(ticker, period="max", auto_adjust=True, progress=False)
    except Exception as exc:  # yfinance raises many different types
        raise RuntimeError(_yahoo_hint(ticker, exc)) from exc
    if raw is None or raw.empty:
        raise RuntimeError(_yahoo_hint(ticker, "no data returned"))
    close = raw["Close"]
    if isinstance(close, pd.DataFrame):  # newer yfinance labels columns by ticker
        close = close.iloc[:, 0]
    close = close.dropna().astype(float)
    close.index = pd.DatetimeIndex(close.index).tz_localize(None).normalize()
    close.index.name = "date"
    return close.sort_index()


def _yahoo_hint(ticker: str, reason: object) -> str:
    return (f"Could not download {ticker} from Yahoo ({reason}). Yahoo rate limits "
            "often; wait and retry, or export the prices yourself and use "
            "quantlab.data.load_csv_prices(path, date_col, price_col).")


def load_rf_daily(refresh: bool = False) -> pd.Series:
    """Daily US risk free rate in decimals from the Ken French data library.

    This is the one month T bill return spread over the trading days of the month.
    The library is updated with a lag of one to two months, so the series usually ends
    before today; aligning it with newer returns is the caller's decision.
    The parsed series is cached in ``data/french_rf_daily.csv``.
    """
    path = DATA_DIR / "french_rf_daily.csv"
    if refresh or not path.exists():
        with urllib.request.urlopen(FRENCH_DAILY_URL, timeout=60) as resp:
            archive = zipfile.ZipFile(io.BytesIO(resp.read()))
        text = archive.read(archive.namelist()[0]).decode("latin-1")
        rf = parse_french_daily(text)["RF"] / 100
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        rf.to_frame("rf").to_csv(path)
    rf = pd.read_csv(path, index_col=0, parse_dates=True)["rf"]
    rf.index.name = "date"
    return rf.rename("rf")


def parse_french_daily(text: str) -> pd.DataFrame:
    """Parse a Ken French daily CSV file into a DataFrame (values still in percent).

    The file starts with free text, then a header line, then rows that start with an
    8 digit date (YYYYMMDD), then a copyright footer. We keep the header right before
    the first date row and stop at the first row that is not a date.
    """
    lines = text.splitlines()
    first = next(i for i, ln in enumerate(lines) if _is_date_row(ln))
    header = [h.strip() for h in lines[first - 1].split(",")][1:]
    rows = []
    for ln in lines[first:]:
        if not _is_date_row(ln):
            break
        parts = [p.strip() for p in ln.split(",")]
        rows.append([parts[0], *map(float, parts[1:])])
    df = pd.DataFrame(rows, columns=["date", *header])
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    return df.set_index("date")


def _is_date_row(line: str) -> bool:
    head = line.split(",", 1)[0].strip()
    return len(head) == 8 and head.isdigit()


def load_csv_prices(path: str, date_col: str, price_col: str) -> pd.Series:
    """Prices from your own CSV export (another data vendor, a bank statement).

    Returns a price series (not returns) with a sorted DatetimeIndex; pass it to
    ``prices_to_returns`` next.
    """
    df = pd.read_csv(path, usecols=[date_col, price_col], parse_dates=[date_col])
    prices = df.set_index(date_col)[price_col].astype(float).dropna().sort_index()
    prices.index.name = "date"
    return prices


def prices_to_returns(prices: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """Simple returns r_t = P_t / P_{t-1} - 1, dropping the first (undefined) day."""
    prices = prices.sort_index()
    returns = (prices / prices.shift(1) - 1).iloc[1:]
    if isinstance(returns, pd.Series):
        returns = returns.dropna()
    return returns


def simulate_returns(n_obs: int, n_assets: int = 1, ann_sharpe: float | np.ndarray = 0.0,
                     ann_vol: float = 0.16, dist: str = "normal", df: int = 5,
                     seed: int = 0) -> pd.DataFrame:
    """Simulated daily excess returns with a known true Sharpe ratio.

    Every test uses this, so tests never need the internet. The daily mean is chosen so
    that mean / volatility equals ``ann_sharpe / sqrt(252)``: the true Sharpe ratio is
    exactly what you ask for, and any difference in a sample is pure luck.

    Parameters
    ----------
    n_obs : number of business days.
    n_assets : number of independent return series (columns).
    ann_sharpe : true annualized Sharpe ratio, one number or one per asset.
    ann_vol : annualized volatility.
    dist : ``"normal"`` or ``"t"``. Student t draws are rescaled to unit variance, so
        they have the same volatility but fatter tails (kurtosis above 3).
    df : degrees of freedom for the t distribution (must be above 2).
    seed : random seed; the same seed always gives the same returns.
    """
    rng = np.random.default_rng(seed)
    if dist == "normal":
        z = rng.standard_normal((n_obs, n_assets))
    elif dist == "t":
        if df <= 2:
            raise ValueError("df must be above 2 for the t distribution to have a variance")
        z = rng.standard_t(df, (n_obs, n_assets)) * np.sqrt((df - 2) / df)
    else:
        raise ValueError(f"dist must be 'normal' or 't', got {dist!r}")
    daily_vol = ann_vol / np.sqrt(TRADING_DAYS)
    daily_mean = np.broadcast_to(np.asarray(ann_sharpe, float), (n_assets,)) / np.sqrt(TRADING_DAYS) * daily_vol
    index = pd.bdate_range("2000-01-03", periods=n_obs, name="date")
    columns = [f"s{i}" for i in range(n_assets)]
    return pd.DataFrame(daily_mean + daily_vol * z, index=index, columns=columns)
