"""acad.py: boxed monochrome matplotlib style for academic quant finance figures."""
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

INK = "#111111"
GREY = "#7f7f7f"
LIGHT = "#c8c8c8"
GRID = "#cccccc"
SHADE = "#bdbdbd"
WIDTHS = {"half": 3.3, "full": 6.5, "wide": 7.5}   # inches, matches a LaTeX text block
NBER = [("2001-03-01", "2001-11-30"), ("2007-12-01", "2009-06-30"), ("2020-02-01", "2020-04-30")]

# Series in plot order get: solid black, dashed black, solid grey, dotted black.
LINE_CYCLE = cycler(color=[INK, INK, GREY, INK]) + cycler(linestyle=["-", "--", "-", ":"])
MARKERS = ["o", "s", "^", "D"]
BAR_STYLES = [("white", "////"), (LIGHT, ""), ("white", "...."), (GREY, ""), ("white", "xxxx")]


def apply_style(usetex: bool = False, font_size: float = 9) -> None:
    """Set global rcParams. usetex=True renders text with LaTeX if a LaTeX install exists."""
    mpl.rcdefaults()   # start clean so nothing from an earlier style leaks in
    rc = {
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "STIX Two Text", "Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": font_size,
        "axes.labelsize": font_size,
        "axes.titlesize": font_size,
        "axes.titlelocation": "left",
        "axes.titleweight": "normal",
        "axes.titlepad": 4,
        "xtick.labelsize": font_size - 1,
        "ytick.labelsize": font_size - 1,
        "legend.fontsize": font_size - 1,
        "legend.frameon": True,
        "legend.fancybox": False,
        "legend.framealpha": 1.0,
        "legend.edgecolor": INK,
        "legend.handlelength": 2.4,
        "axes.spines.top": True,
        "axes.spines.right": True,
        "axes.linewidth": 0.8,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "axes.facecolor": "white",
        "axes.axisbelow": True,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linestyle": ":",
        "grid.linewidth": 0.6,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "xtick.major.size": 3.5,
        "ytick.major.size": 3.5,
        "xtick.minor.visible": True,
        "ytick.minor.visible": True,
        "xtick.minor.size": 1.8,
        "ytick.minor.size": 1.8,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "xtick.minor.width": 0.5,
        "ytick.minor.width": 0.5,
        "axes.prop_cycle": LINE_CYCLE,
        "lines.linewidth": 1.1,
        "lines.markersize": 3.5,
        "errorbar.capsize": 2,
        "patch.linewidth": 0.7,
        "hatch.linewidth": 0.5,
        "figure.facecolor": "white",
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
    if usetex and shutil.which("latex"):
        rc.update({
            "text.usetex": True,
            "font.serif": ["Computer Modern Roman"],
            "text.latex.preamble": r"\usepackage{amsmath}\usepackage{amssymb}",
        })
    mpl.rcParams.update(rc)


def new_fig(width: str = "full", aspect: float = 0.6, nrows: int = 1, ncols: int = 1, **kw):
    """Figure at a standard width. aspect = height / width. Single axis is returned directly."""
    w = WIDTHS[width] if isinstance(width, str) else float(width)
    return plt.subplots(nrows, ncols, figsize=(w, w * aspect), **kw)


def panel_title(ax, letter: str, text: str) -> None:
    """Panel title in the journal convention: '(a) Growth of $1, log scale'."""
    ax.set_title(f"({letter}) {text}", loc="left")


def shade(ax, start, end, label: str | None = None, color: str = SHADE, alpha: float = 0.28) -> None:
    """Grey vertical band for holdout periods, regimes, events."""
    ax.axvspan(pd.Timestamp(start) if isinstance(start, str) else start,
               pd.Timestamp(end) if isinstance(end, str) else end,
               color=color, alpha=alpha, linewidth=0, zorder=0)
    if label:
        ax.annotate(label, xy=(start, 0.0), xycoords=("data", "axes fraction"), xytext=(3, 3),
                    textcoords="offset points", ha="left", va="bottom", fontsize=mpl.rcParams["legend.fontsize"])


def recession_bands(ax, bands=NBER) -> None:
    """NBER recession shading (US). Pass your own list of (start, end) for other regions."""
    for a, b in bands:
        shade(ax, a, b)


def zero_line(ax, y: float = 0.0) -> None:
    ax.axhline(y, color=INK, linewidth=0.5, zorder=1)


def ref_line(ax, value, text, axis: str = "x", ls: str = "--") -> None:
    """Dashed reference line with a direct label, no legend entry."""
    fs = mpl.rcParams["legend.fontsize"]
    if axis == "x":
        ax.axvline(value, color=INK, linestyle=ls, linewidth=0.9)
        ax.annotate(text, xy=(value, 1.0), xycoords=("data", "axes fraction"), xytext=(3, -3),
                    textcoords="offset points", ha="left", va="top", fontsize=fs)
    else:
        ax.axhline(value, color=INK, linestyle=ls, linewidth=0.9)
        ax.annotate(text, xy=(1.0, value), xycoords=("axes fraction", "data"), xytext=(-3, 3),
                    textcoords="offset points", ha="right", va="bottom", fontsize=fs)


def pct_axis(ax, axis: str = "y", decimals: int = 0, scale: float = 100.0) -> None:
    """Percent tick labels with a proper minus sign. scale=100 when data are decimals."""
    fmt = FuncFormatter(lambda v, _: f"{v * scale:.{decimals}f}%".replace("-", "−"))
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def categorical_x(ax, positions, labels) -> None:
    """Category labels on the x axis without tick marks (use for bar charts)."""
    ax.set_xticks(positions, labels)
    ax.tick_params(axis="x", which="both", length=0)
    ax.xaxis.set_minor_locator(NullLocator())


def bar_kw(i: int = 0) -> dict:
    """Bar style i: 0 white with hatching, 1 light grey, 2 white with dots, 3 mid grey, 4 white crosshatch."""
    fc, h = BAR_STYLES[i % len(BAR_STYLES)]
    return dict(facecolor=fc, edgecolor=INK, hatch=h, linewidth=0.7)


def hist_kw() -> dict:
    return dict(facecolor=LIGHT, edgecolor=INK, linewidth=0.5)


def source_note(fig, text: str, y: float = -0.01) -> None:
    """Small italic note under the figure: data, sample, definitions."""
    fig.text(0.0, y, text, ha="left", va="top", fontsize=mpl.rcParams["legend.fontsize"] - 0.5, style="italic")


def save(fig, name: str, outdir: str = "output", formats=("pdf", "png")) -> list[Path]:
    """Vector PDF for papers, 300 dpi PNG for slides. Returns the written paths."""
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in formats:
        p = out / f"{name}.{ext}"
        fig.savefig(p)
        paths.append(p)
    return paths


# ---------------------------------------------------------------- quant finance helpers

def drawdown(r: pd.Series) -> pd.Series:
    w = (1 + r).cumprod()
    return w / w.cummax() - 1


def equity_stats(r: pd.Series, periods: int = 252) -> dict:
    """Annualized geometric return, volatility, Sharpe (pass excess returns for a true Sharpe), max drawdown."""
    return {
        "ret": (1 + r).prod() ** (periods / len(r)) - 1,
        "vol": r.std() * np.sqrt(periods),
        "sharpe": r.mean() / r.std() * np.sqrt(periods),
        "mdd": drawdown(r).min(),
    }


def log_wealth_axis(ax, lo: float, hi: float, headroom: float = 1.0, fmt: str = "${:g}") -> None:
    """Log y axis with $ ticks at 0.5, 1, 2, 4, ... fitted to the data range lo..hi.
    headroom > 1 leaves empty space above the data (for a legend)."""
    std = [0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 128]
    top = hi * headroom
    ticks = [t for t in std if lo * 0.9 <= t <= top * 1.02]
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt.format(v)))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_ylim(lo * 0.9, top)


def booktabs(ax, header: list[str], rows: list[tuple[str, list[str]]], fs: float | None = None) -> None:
    """Three rule academic table on an empty axis. header[0] is the label column heading (may be '')."""
    fs = fs or mpl.rcParams["font.size"] - 0.5
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    n_vals = len(header) - 1
    cols = np.linspace(0.98 - (n_vals - 1) * 0.26, 0.98, n_vals)
    m = len(rows) + 1
    step = 1.0 / (m + 1.0)
    ax.plot([0, 1], [1, 1], color=INK, linewidth=0.9, linestyle="-", clip_on=False)
    ax.plot([0, 1], [0, 0], color=INK, linewidth=0.9, linestyle="-", clip_on=False)
    ax.text(0.0, 1 - step, header[0], ha="left", va="center", fontsize=fs, style="italic")
    for cx, h in zip(cols, header[1:]):
        ax.text(cx, 1 - step, h, ha="right", va="center", fontsize=fs, style="italic")
    ymid = 1 - step * 1.675
    ax.plot([0, 1], [ymid, ymid], color=INK, linewidth=0.5, linestyle="-")
    for i, (lab, vals) in enumerate(rows):
        yy = 1 - step * (i + 1 + 1.35)
        ax.text(0.0, yy, lab, ha="left", va="center", fontsize=fs)
        for cx, v in zip(cols, vals):
            ax.text(cx, yy, v, ha="right", va="center", fontsize=fs)


def wealth_drawdown_figure(returns: dict[str, pd.Series], table: bool = True, recessions=NBER,
                           note: str | None = None, width: str = "wide"):
    """Standard backtest figure: (a) growth of $1 on a log scale, (b) drawdown, optional results table.
    returns: ordered dict name -> daily return series on a common sample. The FIRST entry is the main
    series (solid black), the second is the benchmark (dashed black). Returns (fig, (ax1, ax2))."""
    names = list(returns)
    fig = plt.figure(figsize=(WIDTHS[width], 6.6 if table else 5.0))
    rows_ratio = [3, 1.1] + ([0.95] if table else [])
    gs = fig.add_gridspec(len(rows_ratio), 1, height_ratios=rows_ratio, hspace=0.30)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax1.tick_params(labelbottom=True)
    wealth = {k: (1 + r).cumprod() for k, r in returns.items()}
    dd = {k: drawdown(r) for k, r in returns.items()}
    for k in names:
        ax1.plot(wealth[k].index, wealth[k], label=k)
    for k in names:
        ax2.plot(dd[k].index, dd[k])
    if recessions:
        recession_bands(ax1, recessions)
        recession_bands(ax2, recessions)
    lo = min(w.min() for w in wealth.values())
    hi = max(w.max() for w in wealth.values())
    log_wealth_axis(ax1, lo, hi, headroom=1.3)
    ax1.set_ylabel("Wealth ($1 invested)")
    ax2.set_ylabel("Drawdown")
    pct_axis(ax2)
    ax2.set_ylim(min(d.min() for d in dd.values()) * 1.12, 0.02)
    first = wealth[names[0]].index
    ax1.set_xlim(first[0], first[-1])
    panel_title(ax1, "a", "Growth of $1, log scale")
    panel_title(ax2, "b", "Drawdown")
    ax1.legend(loc="upper left")
    zero_line(ax2)
    if table:
        ax3 = fig.add_subplot(gs[2])
        pct = lambda x: f"{x:.1%}".replace("-", "−")
        st = {k: equity_stats(r) for k, r in returns.items()}
        rows = [("Annualized return", [pct(st[k]["ret"]) for k in names]),
                ("Annualized volatility", [pct(st[k]["vol"]) for k in names]),
                ("Sharpe ratio", [f"{st[k]['sharpe']:.2f}" for k in names]),
                ("Maximum drawdown", [pct(st[k]["mdd"]) for k in names])]
        booktabs(ax3, [""] + names, rows)
        fig.subplots_adjust(left=0.10, right=0.97, top=0.965, bottom=0.07)
    else:
        fig.subplots_adjust(left=0.10, right=0.97, top=0.93, bottom=0.10)
    if note:
        source_note(fig, note, y=0.015)
    return fig, (ax1, ax2)
