"""House style for figures: the academic black and white style of ``quantlab.acad``.

``apply_style()`` and ``PALETTE`` keep the interface PLAN.md defines, but now follow the
academic-graphs skill: boxed axes, serif text, black and grey only, series told apart by
line style. New figure code should use ``quantlab.acad`` directly (panel titles, notes,
the standard wealth and drawdown figure, PDF and PNG output).
"""

from __future__ import annotations

import matplotlib as mpl
from matplotlib.axes import Axes

from quantlab import acad

PALETTE = {
    "primary": acad.INK,
    "comparison": acad.INK,
    "third": acad.GREY,
    "text": acad.INK,
    "text_secondary": acad.GREY,
    "grid": acad.GRID,
    "surface": "white",
}


def apply_style() -> None:
    """Reset matplotlib and apply the academic style; call once at the top of a notebook."""
    acad.apply_style()


def reference_line(ax: Axes, value: float, label: str, axis: str = "x",
                   linestyle: str = "--", side: str = "right", ypos: float = 1.0) -> None:
    """Black reference line (a benchmark, a hurdle) labelled directly on the chart.

    ``axis="x"`` draws a vertical line at x = value, ``axis="y"`` a horizontal one. Use
    different ``linestyle`` values (``"--"``, ``":"``, ``"-."``) to tell several lines
    apart. ``side="left"`` puts the label left of a vertical line, or at the left end of
    a horizontal one, and ``ypos`` (0 to 1, axes height) moves the label of a vertical
    line down, so close lines stay readable.
    """
    fs = mpl.rcParams["legend.fontsize"]
    if axis == "x":
        ax.axvline(value, color=acad.INK, linestyle=linestyle, linewidth=0.9)
        left = side == "left"
        ax.annotate(label, xy=(value, ypos), xycoords=("data", "axes fraction"),
                    xytext=(-3 if left else 3, -3), textcoords="offset points",
                    ha="right" if left else "left", va="top", fontsize=fs)
    elif axis == "y":
        ax.axhline(value, color=acad.INK, linestyle=linestyle, linewidth=0.9)
        left = side == "left"
        ax.annotate(label, xy=(0.0 if left else 1.0, value), xycoords=("axes fraction", "data"),
                    xytext=(3 if left else -3, 3), textcoords="offset points",
                    ha="left" if left else "right", va="bottom", fontsize=fs)
    else:
        raise ValueError("axis must be 'x' or 'y'")
