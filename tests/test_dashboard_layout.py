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
    for section in ('Overview', 'Capacities & gaps', 'Hazards & training', 'Networks & cooperation'):
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
    assert "capacity_visual_dashboard(sliced,active)" in section
    assert "key='capacity_country_view'" not in app
    assert "compact_table(['Country','Reported capacity'],rows" not in section
    assert 'def capacity_visual_dashboard(frame, active):' in app
    assert '<details class="eoc-capacity-disclosure">' in app
    assert '<summary class="eoc-capacity-summary">' in app
    assert "countries_capacity_grid(rows)" in app
    assert 'eoc-country-capacity-grid' in app
    assert '.eoc-country-capacity-grid,.eoc-country-category-grid{grid-template-columns:1fr;}' in app
    assert 'grid-template-columns:repeat(3,minmax(0,1fr));' in app
    assert '.eoc-capacity-summary:focus-visible' in app
    assert '.eoc-capacity-disclosure[open] .eoc-capacity-chevron' in app


def test_capacity_charts_cover_component_questions():
    import app as dashboard_app
    from dashboard.data import load_data, country_aggregate, capacity_table, CAPACITIES
    records,_=load_data()
    countries=country_aggregate(records)
    comp=next(iter(CAPACITIES))
    frame=capacity_table(countries)
    selected=frame[frame.component==comp]
    assert len(selected)==len(CAPACITIES[comp])
    for _,item in selected.iterrows():
        counts=dashboard_app.capacity_response_distribution(countries,item)
        if len(counts):
            assert counts.sum()<=len(countries)
            for kind in ('donut','bar','treemap'):
                chart=dashboard_app.capacity_chart(item,counts,kind)
                assert len(chart.data)>=1
                assert chart.layout.dragmode is False
                assert chart.layout.height==430
                if kind=='donut':
                    # The donut and the center annotation must share a center,
                    # at approximately half the entire Plotly chart height.
                    ymin,ymax=chart.data[0].domain.y
                    assert chart.layout.annotations[0].y==(ymin+ymax)/2
                    top=chart.layout.margin.t
                    bottom=chart.layout.margin.b
                    plot_height=chart.layout.height-top-bottom
                    visual_center=top+(1-(ymin+ymax)/2)*plot_height
                    assert abs(visual_center-chart.layout.height/2)<12
                    assert chart.layout.legend.orientation=='h'



def test_expandable_capacity_bars_keep_visible_blue_fill():
    """Inline spans ignore percentage width; the fill must be display:block."""
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert '.measure-fill{display:block;height:100%;background:#009BDA;' in app
    assert '<span class="measure-bar"><span class="measure-fill" style="width:' in app


def test_overview_uses_regional_treemaps_without_country_drilldowns():
    """Section 03 and 04 show region-only aggregate proportions side by side."""
    from dashboard.data import load_data,country_aggregate,capacity_table,CAPACITIES
    from dashboard.treemap import overview_treemap_html
    records,_=load_data()
    active=country_aggregate(records)
    strengths=capacity_table(active)
    strengths=strengths[strengths.component.isin(CAPACITIES)]
    strengths=(strengths[strengths.denominator>0]
               .sort_values(['in_place','capacity'],ascending=[False,True]).head(7))
    html=overview_treemap_html(strengths,'available')
    assert html.count('class="eoc-overview-treemap-tile"')==7
    assert '<details' not in html
    assert 'eoc-country-capacity-item' not in html
    source=(ROOT/'app.py').read_text(encoding='utf-8')
    overview=source.split('def regional_overview(country,active):',1)[1].split('def capacity_and_gaps(active):',1)[0]
    after_map=overview.split('    st.divider()',1)[1]
    assert "left,right=st.columns(2,gap='large')" in after_map
    assert "overview_treemap_html(strengths,'available',lang=chosen_language())" in after_map
    assert "overview_treemap_html(pd.DataFrame(gap_rows),'gap',lang=chosen_language())" in after_map
    assert 'capacity_rows_html(' not in after_map


def test_regional_capacity_component_is_the_only_regional_capacity_explorer():
    """Consolidated regional capacity and infrastructure indicators remain in the component selector."""
    source=(ROOT/'app.py').read_text(encoding='utf-8')
    capacities=source.split('def capacity_and_gaps(active):',1)[1].split('def operations_section(active):',1)[0]
    operations=source.split('def operations_section(active):',1)[1].split('NETWORK_STATUS_SYMBOLS=',1)[0]
    assert "key='capacity_component'" in capacities
    assert "list(CAPACITIES.keys())" in capacities
    assert "capacity_visual_dashboard(sliced,active)" in capacities
    assert "Information systems and surge workforce" not in capacities
    assert "capacity_rows_html(focus,country=active)" not in capacities
    assert "section('Physical infrastructure'" not in operations
    assert "RESOURCE_LABELS.values()" not in operations
    assert "capacity_rows_html(pd.DataFrame(cards)" not in operations
    assert "section('Hazards reported in the past two years'" in operations
    assert "section('Training completed and prioritized'" in operations
    assert "eyebrow='02 / WORKFORCE DEVELOPMENT'" in operations
    # The national institution detail is not removed by this regional simplification.
    national=source.split('def country_profile(',1)[1] if 'def country_profile(' in source else source
    assert "section('Physical infrastructure','Resources the institution reports as available.'" in national


def test_infrastructure_remains_available_in_capacity_component():
    from dashboard.data import CAPACITIES, RESOURCE_LABELS, load_data, country_aggregate, capacity_table
    import app as dashboard_app
    records,_=load_data()
    countries=country_aggregate(records)
    caps=capacity_table(countries)
    assert 'Infrastructure' in CAPACITIES or 'Infrastructure' in set(caps.component)
    infrastructure=caps[caps.component=='Infrastructure']
    assert len(infrastructure)==len(RESOURCE_LABELS)
    assert infrastructure['denominator'].gt(0).any()
    assert set(RESOURCE_LABELS.values()).issubset(set(infrastructure.capacity))
    assert infrastructure['denominator'].gt(0).any()


def test_regional_hazards_are_four_donuts_above_country_heatmap():
    from dashboard.data import load_data,country_aggregate,HAZARD_LABELS
    from app import hazard_summary_cards,training_summary_data
    records,_=load_data()
    active=country_aggregate(records)
    html=hazard_summary_cards(active)
    assert html.count('class="network-card eoc-hazard-card"')==len(HAZARD_LABELS)==4
    assert html.count('class="eoc-hazard-donut"')==4
    assert html.count('class="eoc-hazard-band"')==16
    assert 'conic-gradient(' in html
    assert all(label in html for label in
               ('No events','1–2 events','3–5 events','More than 5 events'))
    assert 'countries with data' not in html
    from dashboard.visual_style import HAZARD_COLORS, NAVY, CYAN, ORANGE
    assert HAZARD_COLORS[1:]==(CYAN,NAVY,ORANGE)
    assert all(color in html for color in HAZARD_COLORS)
    from unittest.mock import patch
    with patch('dashboard.i18n.chosen_language',return_value='es'):
        html_es=hazard_summary_cards(active)
    assert all(label in html_es for label in
               ('Ningún evento','1–2 eventos','3–5 eventos','Más de 5 eventos'))
    assert 'países con datos' not in html_es
    assert all(name in html for name in HAZARD_LABELS.values())
    summary=training_summary_data(active)
    from dashboard.data import TRAINING_LABELS
    assert len(summary)==len(TRAINING_LABELS)
    for _,row in summary.iterrows():
        assert 0<=row.done_n<=row.done_d<=len(active)
        assert 0<=row.priority_n<=row.priority_d<=len(active)
    fig=charts.training_comparison(summary,lang='en')
    assert len(fig.data)==2
    assert fig.layout.barmode=='group'
    assert set(trace.name for trace in fig.data)=={'Completed','Prioritized'}


def test_hazard_and_training_nav_has_one_non_expandable_comparison():
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    main=app.split('def main():',1)[1]
    assert "'Hazards & training'" in main
    assert "'Operations & hazards'" not in main
    operations=app.split('def operations_section(active):',1)[1].split('NETWORK_STATUS_SYMBOLS=',1)[0]
    assert operations.index('hazard_summary_cards(active)')<operations.index('viz.hazard_heatmap(')
    assert operations.index('viz.hazard_heatmap(')<operations.index('viz.training_comparison(')
    assert 'training_drilldown_html(active)' not in operations
    assert operations.count('st.plotly_chart(')==2
