"""Regression tests for the full-width network participation heatmap."""
from pathlib import Path

import app as ui
from dashboard.charts import (
    NETWORK_STATUS_CODES, NETWORK_STATUS_COLORS, network_participation_heatmap,
)
from dashboard.data import NETWORK_NAMES, country_aggregate, load_data
from dashboard.i18n import tr

ROOT=Path(__file__).resolve().parents[1]


def survey_countries():
    records,_=load_data()
    return country_aggregate(records).sort_values('country').reset_index(drop=True)


def test_heatmap_has_every_country_and_all_three_networks_in_source_order():
    countries=survey_countries()
    for lang in ('en','es'):
        fig=network_participation_heatmap(countries,lang=lang)
        matrix=fig.data[0]
        assert matrix.type=='heatmap'
        assert list(matrix.x)==[tr(q,lang) for q in NETWORK_NAMES.values()]
        assert list(matrix.y)==[tr(q,lang) for q in countries.country]
        assert len(matrix.z)==len(countries)
        assert all(len(row)==len(NETWORK_NAMES) for row in matrix.z)
        assert fig.layout.yaxis.autorange=='reversed'
        assert fig.layout.xaxis.side=='top'
        assert matrix.showscale is False
        assert len(fig.layout.annotations)==len(countries)*len(NETWORK_NAMES)


def test_each_cell_preserves_the_true_categorical_response_in_both_languages():
    countries=survey_countries()
    names=list(NETWORK_NAMES.values())
    fig_en=network_participation_heatmap(countries,lang='en')
    fig_es=network_participation_heatmap(countries,lang='es')
    for row in range(len(countries)):
        for col,name in enumerate(names):
            value=countries.loc[row,name]
            status=value if value in NETWORK_STATUS_CODES else 'Not reported'
            expected=NETWORK_STATUS_CODES[status]
            assert int(fig_en.data[0].z[row][col])==expected
            assert int(fig_es.data[0].z[row][col])==expected
            assert fig_en.data[0].customdata[row][col]==status
            assert fig_es.data[0].customdata[row][col]==tr(status,'es')
    assert set(NETWORK_STATUS_CODES)=={
        'Participating','Interested','Not participating','Not reported'
    }
    assert set(NETWORK_STATUS_COLORS)==set(NETWORK_STATUS_CODES)


def test_network_cards_are_static_and_country_status_is_separate_heatmap():
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    network=app.split('def cooperation_section(active):',1)[1].split('def flag_from_iso(',1)[0]
    assert '<div class="network-card">' in network
    assert '<details class="network-card">' not in network
    assert '<summary>' not in network
    assert "st.markdown(network_heatmap_html(active),unsafe_allow_html=True)" in network
    assert "st.plotly_chart(viz.network_participation_heatmap" not in network
    assert network.index('network-grid') < network.index('network_heatmap_html(active)')
    assert 'eoc-network-legend' in network
    for status in NETWORK_STATUS_CODES:
        assert status in network
    # Other capacity indicators retain their own disclosures.
    assert "capacity_rows_html(ranked,pair='cooperation',country=active)" in network


def test_heatmap_legend_statuses_are_translated():
    assert tr('Country participation by network','es') == 'Participación de los países por red'
    assert tr('Participating','es') == 'Participa'
    assert tr('Interested','es') == 'Interesado'
    assert tr('Not participating','es') == 'No participa'
    assert tr('Not reported','es') == 'Sin información'


def test_streamlit_network_matrix_renders_all_countries_and_statuses_without_plotly():
    """Exercise the actual dashboard render path (not just the unused Plotly fig)."""
    from html.parser import HTMLParser

    class Extract(HTMLParser):
        def __init__(self):
            super().__init__()
            self.statuses=[]
            self.headers=[]
        def handle_starttag(self, tag, attrs):
            info=dict(attrs)
            if tag=='span' and 'eoc-network-heat-cell' in info.get('class',''):
                self.statuses.append(info)
            if tag=='th':
                self.headers.append(info)

    countries=survey_countries()
    from unittest.mock import patch
    for lang in ('en','es'):
        with patch('dashboard.i18n.chosen_language',return_value=lang):
            html=ui.network_heatmap_html(countries)
        parsed=Extract()
        parsed.feed(html)
        assert html.count('<tr>')==len(countries)+1
        assert html.count('class="eoc-network-country"')==len(countries)
        assert len(parsed.statuses)==len(countries)*len(NETWORK_NAMES)
        assert len(parsed.headers)==len(countries)+len(NETWORK_NAMES)+1
        assert 'eoc-network-matrix' in html
        for country_no,(_,country) in enumerate(countries.iterrows()):
            for network_no,network in enumerate(NETWORK_NAMES.values()):
                status=country[network]
                expected=status if status in NETWORK_STATUS_CODES else 'Not reported'
                cell=parsed.statuses[country_no*len(NETWORK_NAMES)+network_no]
                assert cell['data-status']==expected
                assert tr(expected,lang) in cell['title']
                assert tr(country.country,lang) in cell['aria-label']


def test_network_heatmap_icon_legend_matches_cells_and_no_heavy_status_fills():
    """Legend and matrix use identical glyphs, status colors and neutral backgrounds."""
    import re
    from html.parser import HTMLParser

    class Symbols(HTMLParser):
        def __init__(self):
            super().__init__()
            self.legend=[]
            self.cells=[]
            self.active=None
        def handle_starttag(self,tag,attrs):
            if tag!='span':
                return
            d=dict(attrs)
            cl=d.get('class','')
            if cl=='eoc-network-legend-symbol':
                self.active=('legend',d.get('data-status'))
            elif cl=='eoc-network-heat-symbol':
                self.active=('cell',d.get('data-status'))
        def handle_data(self,data):
            if self.active and data.strip():
                label,status=self.active
                (self.legend if label=='legend' else self.cells).append((status,data.strip()))
                self.active=None

    countries=survey_countries()
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    assert 'background:#005A8B;' not in app.split('.eoc-network-heat-cell{',1)[1].split('}',1)[0]
    assert 'background:#009BDA;' not in app.split('.eoc-network-heat-cell{',1)[1].split('}',1)[0]
    assert '.eoc-network-legend-symbol[data-status="Participating"]' in app
    assert '.eoc-network-heat-symbol[data-status="Participating"]' in app
    assert '.eoc-network-legend-symbol[data-status="Interested"]' in app
    assert '.eoc-network-heat-symbol[data-status="Interested"]' in app
    assert 'eoc-network-swatch' not in app
    # Same symbol dictionary powers all legend keys and 15x3 country cells.
    symbols=ui.NETWORK_STATUS_SYMBOLS
    assert symbols=={
        'Participating':'✓','Interested':'◐',
        'Not participating':'×','Not reported':'—'
    }
    html=ui.network_heatmap_html(countries)
    parsed=Symbols()
    parsed.feed(html)
    assert len(parsed.cells)==len(countries)*len(NETWORK_NAMES)
    for index,(_,country) in enumerate(countries.iterrows()):
        for j,name in enumerate(NETWORK_NAMES.values()):
            status=country[name]
            if status not in symbols:
                status='Not reported'
            assert parsed.cells[index*len(NETWORK_NAMES)+j]==(status,symbols[status])
    assert all('background:' not in piece for piece in re.findall(r'<span class="eoc-network-heat-cell"[^>]*>',html))
