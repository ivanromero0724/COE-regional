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
    assert ".eoc-pair-heading{min-height:0;margin:0 0 2px" in APP
    assert ".section-desc{font-size:.81rem;line-height:1.46;color:#657A8A;margin-bottom:8px;" in APP
    assert "@media(max-width:900px){.eoc-pair-heading{margin-bottom:0;}" in APP
    assert ".card-panel.eoc-pair-overview.eoc-operations-card{height:auto;overflow:visible;}" in APP


def test_map_height_is_proportionate_to_operations_card():
    records, _ = load_data()
    fig = charts.countries_map(country_aggregate(records))
    assert fig is not None
    assert fig.layout.height == 450
    assert ".card-panel.eoc-pair-overview" in APP
    assert "with st.container(border=False, key='eoc_coverage_map_panel')" in APP
    assert "with st.container(border=True, key='eoc_operations_panel')" not in APP
    assert 'card-panel eoc-pair-overview eoc-operations-card' in APP
    assert 'height:calc(450px + 2rem + 2px)' in APP
    assert "overflow-y:auto;" in APP
    assert "st-key-eoc_coverage_map_panel" in APP
    assert fig.layout.paper_bgcolor == '#FFFFFF'


def test_hazard_chart_and_infrastructure_do_not_force_whitespace():
    records, _ = load_data()
    fig = charts.country_hazards(records.iloc[0])
    assert fig.layout.height == 340
    assert ".status-tile-grid.eoc-pair-infrastructure{min-height:0" in APP


def test_cards_are_compact_and_have_relevant_accessible_icons():
    assert "justify-content:space-between" not in APP
    assert 'grid-template-areas:"label icon" "value icon"' in APP
    assert 'KPI_ICON_PATHS={' in APP
    assert 'aria-hidden="true"' in APP
    assert "min-height:117px" in APP


def test_map_has_matching_border_and_no_header_spacer():
    assert "with st.container(border=False, key='eoc_coverage_map_panel')" in APP
    assert "width='stretch'" in APP
    assert ".eoc-pair-heading{min-height:0" in APP


def test_operations_no_double_border_or_white_overlay():
    assert ".st-key-eoc_operations_panel" not in APP
    assert "with st.container(border=True, key='eoc_operations_panel')" not in APP
    assert ".card-panel.eoc-pair-overview.eoc-operations-card{" in APP
    assert "border:1px solid #DFE9F1;" in APP
    assert "overflow-x:hidden;" in APP


def test_capacity_panels_are_equal_height_without_obsolete_notes():
    assert ".card-panel.eoc-pair-capacities{min-height:305px;margin-bottom:0;padding:13px 16px;}" in APP
    assert ".card-panel.eoc-pair-capacities .measure-row{padding:6px 0;min-height:35px;}" in APP
    assert "min-height:425px" not in APP
    assert ".card-panel.eoc-pair-capacities{min-height:0;}" in APP
    assert "In development or informal is not considered fully in place." not in APP
    assert "PRELIMINARY · Self-reported capacities" not in APP
    assert "justify-content:space-evenly" not in APP


def test_priority_capacity_rows_fill_card_without_stretching_other_sections():
    # The five-row gaps card intentionally gets distributed rows; the seven-row
    # capacities card keeps its existing, compact layout.
    assert "grid-template-columns:minmax(0,1fr);" in APP
    assert "align-content:space-between;" in APP
    assert ".card-panel.eoc-pair-capacities.eoc-priority-card{" in APP
    assert ".eoc-priority-card .measure-row{padding:9px 0;}" in APP
    assert "variant_class=' eoc-priority-card' if pair=='capacities' and variant=='priority'" in APP
    assert "capacity_rows_html(pd.DataFrame(figures),pair='capacities',variant='priority')" in APP
    assert "capacity_rows_html(ranked,pair='capacities')" in APP
    assert "min-height:305px" in APP
