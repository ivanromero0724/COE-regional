"""Regressions for compact, top-aligned side-by-side dashboard sections.

Panels may have different natural heights when content differs: no giant blank
cards, artificially spaced bars, or large gaps below section headings.
"""
from pathlib import Path
from dashboard import charts
from dashboard.data import load_data, country_aggregate

APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_comparisons_do_not_stretch_bar_cards():
    for pair in ("overview", "capacities", "cooperation"):
        assert f".card-panel.eoc-pair-{pair}" in APP
        assert f"pair='{pair}'" in APP or pair == "overview"
    assert "justify-content:space-evenly" not in APP
    assert "min-height:500px" not in APP
    assert "min-height:435px" not in APP
    assert "min-height:645px" not in APP


def test_headings_are_compact_and_translate_flexibly():
    assert ".eoc-pair-heading{min-height:92px" in APP
    assert ".section-desc{font-size:.81rem;line-height:1.46;color:#657A8A;margin-bottom:8px;" in APP
    assert "@media(max-width:900px){.eoc-pair-heading{min-height:0;}}" in APP


def test_map_height_is_proportionate_to_operations_card():
    records, _ = load_data()
    fig = charts.countries_map(country_aggregate(records))
    assert fig is not None
    assert fig.layout.height == 385
    assert ".card-panel.eoc-pair-overview" in APP


def test_hazard_chart_and_infrastructure_do_not_force_whitespace():
    records, _ = load_data()
    fig = charts.country_hazards(records.iloc[0])
    assert fig.layout.height == 340
    assert ".status-tile-grid.eoc-pair-infrastructure{min-height:0" in APP
