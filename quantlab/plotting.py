"""House style for figures: ``apply_style()``, the ``PALETTE`` colours and a helper for
labelled reference lines.

Rules: one y axis per chart, 2px lines, a light solid grid, text in the text colours
(never in series colours), a legend from two series on, reference lines labelled
directly, and a title that states the takeaway.
"""

from __future__ import annotations

import matplotlib as mpl
from cycler import cycler
from matplotlib.axes import Axes

PALETTE = {
    "primary": "#2a78d6",
    "comparison": "#eb6834",
    "third": "#1baf7a",
    "text": "#0b0b0b",
    "text_secondary": "#52514e",
    "grid": "#e4e3df",
    "surface": "#fcfcfb",
}


def apply_style() -> None:
    """Set matplotlib defaults once per notebook; every later chart follows them."""
    p = PALETTE
    mpl.rcParams.update({
        "figure.figsize": (10, 4.5),
        "figure.dpi": 110,
        "figure.facecolor": p["surface"],
        "axes.facecolor": p["surface"],
        "axes.edgecolor": p["grid"],
        "axes.labelcolor": p["text_secondary"],
        "axes.titlecolor": p["text"],
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "axes.prop_cycle": cycler(color=[p["primary"], p["comparison"], p["third"]]),
        "grid.color": p["grid"],
        "grid.linestyle": "-",
        "grid.linewidth": 0.6,
        "lines.linewidth": 2.0,
        "xtick.color": p["text_secondary"],
        "ytick.color": p["text_secondary"],
        "text.color": p["text"],
        "legend.frameon": False,
        "legend.labelcolor": p["text"],
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "savefig.facecolor": p["surface"],
    })


def reference_line(ax: Axes, value: float, label: str, axis: str = "x",
                   color: str | None = None) -> None:
    """Draw a dashed reference line (a benchmark, a hurdle) and label it on the line.

    ``axis="x"`` draws a vertical line at x = value, ``axis="y"`` a horizontal one.
    The label sits next to the line in the secondary text colour, so no legend entry
    is needed.
    """
    color = color or PALETTE["text_secondary"]
    style = {"color": color, "linestyle": "--", "linewidth": 1.2}
    text = {"color": PALETTE["text_secondary"], "fontsize": 9}
    if axis == "x":
        ax.axvline(value, **style)
        ax.annotate(label, (value, 1), xycoords=("data", "axes fraction"),
                    xytext=(4, -4), textcoords="offset points", va="top", **text)
    elif axis == "y":
        ax.axhline(value, **style)
        ax.annotate(label, (0, value), xycoords=("axes fraction", "data"),
                    xytext=(4, 4), textcoords="offset points", va="bottom", **text)
    else:
        raise ValueError("axis must be 'x' or 'y'")
