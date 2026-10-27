"""Layout and navigation regressions, without requiring a browser or Streamlit."""
from pathlib import Path
import pandas as pd
from dashboard import charts
from dashboard.data import HAZARD_LABELS

ROOT = Path(__file__).resolve().parents[1]


def test_methods_data_page_removed():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert "['Regional overview','Country profiles']" in app
    assert 'Methods & data' not in app
    assert 'def methodology(' not in app
    assert 'maturity_radar' not in app


def test_hazard_heatmap_has_legible_labels():
    cats = list(HAZARD_LABELS.values())
    data = pd.DataFrame([
        dict(country='Argentina', **dict(zip(cats, (1.0, 3.0, 0.0, float('nan'))))),
        dict(country='Belize', **dict(zip(cats, (2.0, 1.0, 1.0, 0.0))))])
    fig = charts.hazard_heatmap(data)
    assert len(fig.layout.annotations) == 8
    assert list(fig.data[0].x) == ['Geo / weather','Biological','Social','Technological']
    assert len(fig.data[0].y) == 2
    assert 'Not reported' in fig.data[0].customdata[0]

def test_streamlit_header_is_opaque_and_fixed():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    header_css = app.split('[data-testid="stHeader"]{', 1)[1].split('}', 1)[0]
    assert 'position:fixed!important;' in header_css
    assert 'top:0!important;' in header_css
    assert 'background:#F7FAFC!important;' in header_css
    assert 'background-image:none!important;' in header_css
    assert 'opacity:1!important;' in header_css
    assert 'backdrop-filter:none!important;' in header_css
    assert 'background:rgba(247,250,252,.93)' not in app


def test_banner_clears_fixed_streamlit_toolbar():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert 'position:fixed!important;' in app
    assert 'padding:3.25rem 1.35rem 2.6rem;' in app
    assert 'padding-top:2.75rem;' in app
    assert 'background:#F7FAFC!important;' in app


def test_paho_and_eoc_logos_are_enlarged_and_responsive():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "minmax(290px,395px)" in app
    assert ".brand-set img{display:block;width:100%;height:96px;" in app
    assert ".brand-set{max-width:360px;}" in app
    assert "object-fit:contain" in app


def test_map_heading_and_chart_borders_consistent():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "Which countries have EOC-S?" in app
    assert "Where have countries responded?" not in app
    assert "border-color:#DFE9F1!important;" in app
    assert "with st.container(border=False, key='eoc_coverage_map_panel')" in app
    assert "with st.container(border=True, key='eoc_coverage_map_panel')" not in app
    assert ".st-key-eoc_coverage_map_panel{" in app
    assert "border:1px solid #DFE9F1!important;" in app
    assert "border:1px solid #DFE9F1;" in app
    assert 'border-radius:12px!important;' in app
    # Every standalone Plotly chart has the same outline as the HTML cards.
    plotly_css = app.split('\n    [data-testid="stPlotlyChart"]{', 1)[1].split('}', 1)[0]
    assert "border:1px solid #DFE9F1;" in plotly_css
    assert "border-radius:12px;" in plotly_css
    # The map's own native frame provides its outline: no nested second border.
    map_css = app.rsplit('.st-key-eoc_coverage_map_panel [data-testid="stPlotlyChart"]{', 1)[1].split('}', 1)[0]
    assert "border:0!important;" in map_css
    assert "border-radius:0!important;" in map_css
    assert "border:1px solid #DFE9F1;border-top:3px solid #005A8B;" in app
    assert "PRELIMINARY · Self-reported capacities from responding countries only." not in app
    assert "Preliminary, self-reported information" not in app


def test_regional_section_navigation_is_top_horizontal_segmented_control():
    """Regional section buttons are on top; the sidebar has no geographic filters."""
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    main = app.split('def main():', 1)[1]
    sidebar = main.split('with st.sidebar:', 1)[1].split('    header()', 1)[0]
    assert "key='regional_section'" not in sidebar
    assert "key='geo_area'" not in sidebar
    assert "key='country_filter'" not in sidebar
    assert "key='coe_language'" in sidebar
    assert "key='main_view'" in sidebar
    assert "st.segmented_control(" in main
    header_index = main.index('    header()')
    controls_index = main.index('tabscope=st.segmented_control(')
    content_index = main.index('active=country')
    assert header_index < controls_index < content_index
    assert "default='Overview'" in main
    assert "key='regional_section'" in main
    assert "format_func=lambda value, _lang=chosen_language(): tr(value, _lang)" in main
    for section in ('Overview', 'Capacities & gaps', 'Operations & hazards', 'Networks & cooperation'):
        assert section in main


def test_sidebar_contains_no_technical_metadata_or_regional_filters():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    main = app.split('def main():', 1)[1]
    sidebar = main.split('with st.sidebar:', 1)[1].split('    header()', 1)[0]
    for removed in ('Geographic area', 'Countries (optional)', 'geo_area', 'country_filter',
                    'Source: local Excel', 'UI build · 2026-10-27.2'):
        assert removed not in sidebar
    assert 'active=country' in main
    assert 'selected=st.multiselect(' not in main
    assert 'subregion=st.selectbox(' not in main


def test_capacity_bars_expand_countries_in_place():
    """The whole horizontal bar is a disclosure, so no second selector/table."""
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    section = app.split('def capacity_and_gaps(active):', 1)[1].split('def operations_section(active):', 1)[0]
    assert 'st.columns(' not in section
    assert "capacity_drilldown_html(sliced,active,component)" in section
    assert "key='capacity_country_view'" not in app
    assert "compact_table(['Country','Reported capacity'],rows" not in section
    assert 'def capacity_drilldown_html(frame, active, component):' in app
    assert '<details class="eoc-capacity-disclosure">' in app
    assert '<summary class="eoc-capacity-summary">' in app
    assert "countries_capacity_grid(rows)" in app
    assert 'eoc-country-capacity-grid' in app
    assert '.eoc-country-capacity-grid{grid-template-columns:1fr;}' in app
    assert 'grid-template-columns:repeat(3,minmax(0,1fr));' in app
    assert '.eoc-capacity-summary:focus-visible' in app
    assert '.eoc-capacity-disclosure[open] .eoc-capacity-chevron' in app


def test_capacity_disclosures_preserve_counts_and_country_statuses():
    """One expandable row per capacity, each containing all reporting countries."""
    import app as dashboard_app
    from dashboard.data import load_data, country_aggregate, capacity_table, CAPACITIES

    records, _ = load_data()
    countries = country_aggregate(records)
    component = next(iter(CAPACITIES))
    frame = capacity_table(countries)
    frame = frame[frame.component == component]
    html = dashboard_app.capacity_drilldown_html(frame, countries, component)
    assert html.count('<details class="eoc-capacity-disclosure">') == len(frame)
    assert html.count('<summary class="eoc-capacity-summary">') == len(frame)
    assert html.count('class="eoc-country-capacity-item"') == len(frame) * len(countries)
    for _, item in frame.iterrows():
        assert item["capacity"] in html
        pct = 100 * item["in_place"] / item["denominator"] if item["denominator"] else 0
        expected = (f'{pct:.0f}% ({int(item["in_place"])}/{int(item["denominator"])})'
                    if item["denominator"] else 'No valid responses')
        assert expected in html
    assert 'class="status-chip status-yes"' in html
    assert 'class="status-chip status-no"' in html
