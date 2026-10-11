"""Tests for quantlab.plotting and quantlab.acad: academic style, reference lines, saving."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from quantlab import acad, data, plotting  # noqa: E402


def test_apply_style_is_black_and_white_and_boxed():
    plotting.apply_style()
    rc = matplotlib.rcParams
    assert rc["axes.spines.top"] and rc["axes.spines.right"]
    assert rc["xtick.direction"] == "in"
    assert rc["savefig.dpi"] == 300
    colors = set(rc["axes.prop_cycle"].by_key()["color"])
    assert colors <= {acad.INK, acad.GREY}
    assert set(plotting.PALETTE.values()) <= {acad.INK, acad.GREY, acad.GRID, "white"}


@pytest.mark.parametrize("axis", ["x", "y"])
def test_reference_line_draws_line_and_label(axis):
    fig, ax = plt.subplots()
    plotting.reference_line(ax, 0.5, "hurdle", axis=axis)
    assert len(ax.lines) == 1
    assert any(t.get_text() == "hurdle" for t in ax.texts)
    plt.close(fig)


def test_reference_line_label_position_options():
    fig, ax = plt.subplots()
    plotting.reference_line(ax, 0.5, "left label", side="left", ypos=0.6)
    assert ax.texts[0].get_ha() == "right" and ax.texts[0].xy[1] == 0.6
    plt.close(fig)


def test_wealth_drawdown_figure_saves_pdf_and_png(tmp_path):
    acad.apply_style()
    r = data.simulate_returns(600, n_assets=2, ann_sharpe=0.5, seed=51)
    fig, _ = acad.wealth_drawdown_figure({"strategy": r["s0"], "benchmark": r["s1"]},
                                         recessions=None, note="Notes: simulated data.")
    paths = acad.save(fig, "test_fig", outdir=str(tmp_path))
    plt.close(fig)
    assert [p.suffix for p in paths] == [".pdf", ".png"] and all(p.exists() for p in paths)


def test_horizontal_reference_label_can_sit_left():
    fig, ax = plt.subplots()
    plotting.reference_line(ax, 0.2, "average", axis="y", side="left")
    assert ax.texts[0].get_ha() == "left" and ax.texts[0].xy[0] == 0.0
    plt.close(fig)
