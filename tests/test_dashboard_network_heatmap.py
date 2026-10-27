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
    assert "viz.network_participation_heatmap(active,lang=chosen_language())" in network
    assert network.index("'<div class=\"network-grid\">'") < network.index(
        "viz.network_participation_heatmap(active,lang=chosen_language())"
    )
    assert "width='stretch'" in network
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
