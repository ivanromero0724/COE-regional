"""Regressions for compact, top-aligned side-by-side dashboard sections.

Panels may have different natural heights when content differs: no giant blank
cards, artificially spaced bars, or large gaps below section headings.
"""
from pathlib import Path
from dashboard import charts
from dashboard.data import load_data, country_aggregate

APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_comparisons_do_not_stretch_bar_cards():
    # Only the older Overview bars retain card-panel pairing.
    assert ".card-panel.eoc-pair-overview" in APP
    # The cooperation cards are now HTML treemaps rather than expandable bars.
    assert "cooperation_treemap_html(ranked,lang=chosen_language()" in APP
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
    assert fig.layout.height == 600
    assert ".card-panel.eoc-pair-overview" in APP
    assert "with st.container(border=False, key='eoc_coverage_map_panel')" in APP
    assert "with st.container(border=True, key='eoc_operations_panel')" not in APP
    assert 'card-panel eoc-pair-overview eoc-operations-card' in APP
    # Chart plus its two 1px borders: same exterior height on both columns.
    map_css=APP.split('.st-key-eoc_coverage_map_panel{',1)[1].split('}',1)[0]
    ops_css=APP.split('.card-panel.eoc-pair-overview.eoc-operations-card{',1)[1].split('}',1)[0]
    assert 'height:602px;' in map_css
    assert 'min-height:602px;' in map_css
    assert 'height:602px;' in ops_css
    assert 'box-sizing:border-box;' in ops_css
    assert fig.layout.height + 2 == 602
    assert fig.layout.yaxis.scaleanchor == 'x'
    assert fig.layout.yaxis.scaleratio == 1
    assert "overflow-y:auto;" in APP
    assert "st-key-eoc_coverage_map_panel" in APP
    assert fig.layout.paper_bgcolor == '#FFFFFF'


def test_hazard_and_infrastructure_cards_have_the_same_height():
    records, _ = load_data()
    fig = charts.country_hazards(records.iloc[0])
    assert fig.layout.height == 340
    assert ".status-tile-grid.eoc-pair-infrastructure{min-height:0" in APP
    assert ".eoc-country-infrastructure-panel{height:340px;" in APP
    profile=APP.split('def country_profile(records,countries):',1)[1].split('def main():',1)[0]
    assert 'class="eoc-country-infrastructure-panel"' in profile
    assert "st.plotly_chart(viz.country_hazards(" in profile


def test_country_experience_cards_share_one_stretching_css_grid():
    profile=APP.split('def country_profile(records,countries):',1)[1].split('def main():',1)[0]
    assert 'class="eoc-country-experience-grid"' in profile
    assert 'class="eoc-country-experience-card"' in profile
    assert "st.container(border=True)" not in profile
    assert '.eoc-country-experience-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;align-items:stretch;' in APP
    assert '.eoc-country-experience-card{box-sizing:border-box;' in APP
    assert 'padding:16px 18px;height:100%;' in APP
    assert 'white-space:pre-line;overflow-wrap:anywhere;' in APP
    # Paragraphs and emphasized phrases are still readable and safely escaped.
    assert "esc(value),flags=re.S)" in profile


def test_cards_are_compact_and_have_relevant_accessible_icons():
    # Space-between is allowed on the country-status tiles, not on bar rows.
    assert ".eoc-country-capacity-item{" in APP
    assert ".eoc-country-capacity-item" in APP
    assert ".eoc-capacity-full .eoc-capacity-summary{" in APP
    assert ".card-panel.eoc-pair-capacities.eoc-priority-card{" not in APP
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


def test_capacity_page_has_two_aligned_regional_summary_treemaps():
    overview=APP.split('def regional_overview(country,active):',1)[1].split('def capacity_and_gaps(active):',1)[0]
    capacity=APP.split('def capacity_and_gaps(active):',1)[1].split('def hazard_summary_cards(active):',1)[0]
    assert 'overview_treemap_html(' not in overview
    assert 'hazard_summary_cards(active)' in overview
    assert "left,right=st.columns(2,gap='large')" in capacity
    assert "section('Most widely reported capacities'" in capacity
    assert "section('Priority capacity gaps'" in capacity
    assert "overview_treemap_html(strengths,'available',lang=chosen_language())" in capacity
    assert "overview_treemap_html(pd.DataFrame(gap_rows),'gap',lang=chosen_language())" in capacity
    assert "capacity_rows_html(" not in capacity
    assert "eoc-country-capacity-item" not in capacity
    assert ".eoc-overview-treemap-plot{position:relative;width:100%;height:450px;}" in APP
    assert ".eoc-overview-treemap-card{" in APP
    assert ".card-panel.eoc-pair-capacities.eoc-priority-card" not in APP
    assert "PRELIMINARY · Self-reported capacities" not in APP


def test_full_bleed_map_wrapper_and_evenly_spaced_operating_groups():
    """No nested Streamlit padding; the right-hand summary uses all card height."""
    from app import distribution_html
    records,_=load_data()
    countries=country_aggregate(records)
    source=APP
    frame=source.split('.st-key-eoc_coverage_map_panel{',1)[1].split('}',1)[0]
    assert 'height:602px;' in frame
    assert 'border:1px solid #DFE9F1!important;' in frame
    for wrapper in ('stVerticalBlockBorderWrapper','stVerticalBlock',
                    'stElementContainer','stPlotlyChart'):
        assert '[data-testid="'+wrapper+'"]' in source.split(
            '/* Full-bleed map:',1
        )[1].split('[data-testid="stMetric"]',1)[0]
    block=source.split('/* Full-bleed map:',1)[1].split(
        '[data-testid="stMetric"]',1
    )[0]
    assert 'padding:0!important;' in block
    assert 'margin:0!important;' in block
    assert 'gap:0!important;' in block

    card=source.split('.card-panel.eoc-pair-overview.eoc-operations-card{',1)[1].split('}',1)[0]
    assert 'height:602px;' in card
    assert 'display:grid;' in card
    assert 'grid-template-rows:minmax(0,1fr) minmax(0,1fr);' in card
    assert '.eoc-operations-rows{display:flex;flex-direction:column;justify-content:space-around;flex:1;' in source
    assert '.eoc-operations-card:has(.eoc-capacity-disclosure[open]){display:block;}' in source

    modes=['24/7 continuous','Response + monitoring',
           'Response only','Not formally defined','Not reported']
    section=distribution_html(countries.operating_mode,'Operating mode',
                              modes,'#005A8B',countries,'operating_mode')
    assert section.count('class="eoc-operations-group"')==1
    assert section.count('class="eoc-operations-rows"')==1
    assert section.count('class="eoc-capacity-disclosure"')==4
    assert '40% (6/15)' in section
    assert '33% (5/15)' in section
