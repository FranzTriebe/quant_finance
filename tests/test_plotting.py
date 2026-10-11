"""Tests for quantlab.plotting: style settings and labelled reference lines."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from quantlab import plotting  # noqa: E402


def test_apply_style_sets_house_rules():
    plotting.apply_style()
    rc = matplotlib.rcParams
    assert rc["lines.linewidth"] == 2.0
    assert rc["axes.grid"] and rc["grid.linestyle"] == "-"
    assert rc["savefig.dpi"] == 150
    assert rc["axes.prop_cycle"].by_key()["color"][0] == plotting.PALETTE["primary"]


@pytest.mark.parametrize("axis", ["x", "y"])
def test_reference_line_draws_line_and_label(axis):
    fig, ax = plt.subplots()
    plotting.reference_line(ax, 0.5, "hurdle", axis=axis)
    assert len(ax.lines) == 1
    assert any(t.get_text() == "hurdle" for t in ax.texts)
    plt.close(fig)


def test_reference_line_label_can_sit_left_of_the_line():
    fig, ax = plt.subplots()
    plotting.reference_line(ax, 0.5, "left label", side="left")
    assert ax.texts[0].get_ha() == "right"
    plt.close(fig)


def test_reference_line_label_height_can_be_lowered():
    fig, ax = plt.subplots()
    plotting.reference_line(ax, 0.5, "low label", ypos=0.6)
    assert ax.texts[0].xy[1] == 0.6
    plt.close(fig)
